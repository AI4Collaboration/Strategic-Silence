"""Isolated Terra decisions over the Codex app-server JSON-RPC interface."""
import itertools
from collections import deque
import json
import os
from pathlib import Path
from queue import Empty, Queue
import shutil
import subprocess
from tempfile import TemporaryDirectory
from threading import Lock, Thread
from time import monotonic

from luna import read, save


class ParticipantToolUse(ValueError):
    pass


class TerraServer:
    def __init__(self, root, model):
        self.root, self.model = root, model
        self.directory = TemporaryDirectory(prefix="crew-rpc-", ignore_cleanup_errors=True)
        self.stderr = (root / "server-stderr.txt").open("a", encoding="utf8")
        exe = os.environ.get("CODEX_APP_RUNTIME_CLI_PATH") or shutil.which("codex")
        self.proc = subprocess.Popen([exe, "app-server", "--listen", "stdio://"], cwd=self.directory.name,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr,
                                     text=True, encoding="utf8")
        self.ids, self.events, self.lock = itertools.count(1), Queue(), Lock()
        def receive():
            try:
                for line in self.proc.stdout:
                    self.events.put(json.loads(line))
            finally:
                self.events.put(None)
        Thread(target=receive, daemon=True).start()
        self.request("initialize", {"clientInfo": {"name": "crew-rollout", "version": "1"},
                                    "capabilities": {"experimentalApi": True}})
        self.send({"method": "initialized"})

    def send(self, obj):
        self.proc.stdin.write(json.dumps(obj) + "\n")
        self.proc.stdin.flush()

    def next_event(self, deadline):
        try:
            event = self.events.get(timeout=max(0, deadline-monotonic()))
        except Empty as error:
            raise TimeoutError("no app-server response before deadline") from error
        if event is None:
            raise RuntimeError("app-server disconnected")
        return event

    def request(self, method, params, pending=None):
        ident = next(self.ids)
        self.send({"id": ident, "method": method, "params": params})
        deadline = monotonic()+180
        while True:
            msg = self.next_event(deadline)
            if msg.get("id") == ident and "method" not in msg:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg["result"]
            if pending is not None and msg.get("params", {}).get("threadId") == params["threadId"]:
                pending.append(msg)

    def call(self, dest, packet):
        with self.lock:
            dest.mkdir()
            save(dest / "input.json", packet)
            start = self.request("thread/start", {"model": self.model, "cwd": self.directory.name,
                                 "ephemeral": True, "approvalPolicy": "never", "sandbox": "read-only",
                                 "baseInstructions": "Return your desk transaction as JSON.",
                                 "config": {"project_doc_max_bytes": 0}})
            thread = start["thread"]["id"]
            save(dest / "session.json", {"thread": thread, "model": start["model"]})
            if start["model"] != self.model:
                raise ValueError("wrong model assigned")
            pending = deque()
            turn = self.request("turn/start", {"threadId": thread, "effort": "medium",
                                "input": [{"type": "text", "text": json.dumps(packet), "text_elements": []}]}, pending)["turn"]["id"]
            deadline = monotonic()+240
            with (dest / "events.jsonl").open("w", encoding="utf8") as log:
                while True:
                    msg = pending.popleft() if pending else self.next_event(deadline)
                    p = msg.get("params", {})
                    if p.get("threadId") != thread:
                        continue
                    method = msg.get("method")
                    if method == "item/completed":
                        if p.get("turnId") != turn:
                            raise ValueError("item belongs to a different turn")
                        item = p["item"]
                        if item["type"] == "reasoning":
                            continue
                        log.write(json.dumps({"item": item, "turn": turn})+"\n")
                    if method == "turn/completed":
                        log.write(json.dumps({"status": p["turn"]["status"], "turn": p["turn"]["id"]})+"\n")
                        break
            decision = rpc_answer(dest, self.model)
            save(dest / "decision.json", decision)
            return decision

    def close(self):
        self.proc.stdin.close()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            self.proc.wait(timeout=20)
        self.stderr.close()
        self.directory.cleanup()


def rpc_answer(dest, model):
    if read(dest / "session.json")["model"] != model:
        raise ValueError("model mismatch")
    events = [json.loads(line) for line in (dest / "events.jsonl").read_text(encoding="utf8").splitlines()]
    if not events or events[-1].get("status") != "completed":
        raise ValueError(f"incomplete turn at {dest.name}")
    items = [e["item"] for e in events[:-1]]
    if not items or items[0]["type"] != "userMessage":
        raise ValueError("missing submitted packet")
    content = items.pop(0)["content"]
    if len(content) != 1 or json.loads(content[0]["text"]) != read(dest / "input.json"):
        raise ValueError("submitted packet mismatch")
    if any(i["type"] == "commandExecution" for i in items):
        raise ParticipantToolUse(f"participant used a shell at {dest.name}")
    if not items or any(i["type"] != "agentMessage" for i in items) or len({e["turn"] for e in events}) != 1:
        raise ValueError(f"unexpected participant activity at {dest.name}")
    body = items[-1]["text"].strip()
    if body.startswith("```json\n") and body.endswith("```"):
        body = body[8:-3]
    return json.loads(body)

"""Run one isolated Luna participant and retain its input, output and event log."""
import json
import os
import shutil
import subprocess
from tempfile import TemporaryDirectory

MODEL = "gpt-6-luna"


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def call(root, name, packet):
    dest = root / name
    dest.mkdir()
    save(dest / "input.json", packet)
    cli = os.environ.get("CODEX_APP_RUNTIME_CLI_PATH") or shutil.which("codex")
    with TemporaryDirectory(prefix="it-appointment-") as isolated:
        args = [cli, "exec", "--ignore-user-config", "--ephemeral", "--skip-git-repo-check",
                "-s", "read-only", "-m", MODEL, "-c", "model_reasoning_effort=\"medium\"",
                "-c", "project_doc_max_bytes=0", "--json", "-C", isolated, "-"]
        prompt = ("Act as the participant in the following packet. Use only this packet, no tools. "
                  "Return only the requested JSON object.\n" + json.dumps(packet))
        proc = subprocess.run(args, cwd=isolated, input=prompt, text=True, encoding="utf-8",
                              errors="replace", capture_output=True, timeout=210)
    (dest / "events.jsonl").write_text(proc.stdout, encoding="utf-8")
    (dest / "stderr.txt").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode or "falling back to model" in proc.stderr.lower():
        raise RuntimeError(f"{name}: Luna call failed; see local logs")
    events = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    items = [e["item"] for e in events if e.get("type") == "item.completed"]
    if not any(e.get("type") == "turn.completed" for e in events) or any(
            i["type"] not in ("reasoning", "agent_message") for i in items):
        raise RuntimeError(f"{name}: incomplete or tool-using participant")
    answer = json.loads(next(i["text"] for i in reversed(items) if i["type"] == "agent_message"))
    save(dest / "decision.json", answer)
    return answer

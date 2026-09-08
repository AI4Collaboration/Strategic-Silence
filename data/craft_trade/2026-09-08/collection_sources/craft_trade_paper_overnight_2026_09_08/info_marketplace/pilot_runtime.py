"""Serial, journaled transport for the prospective development pilot.

No network client is constructed until live_transport is called. An ambiguous
interrupted dispatch retains its reservation and stops. Explicitly configured
retries of known transport failures reserve and journal each attempt separately.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_CEILING
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

PRICES = {"openai/gpt-5.4": ("2.50", "15.00"),
          "openai/gpt-5.4-mini": ("0.75", "4.50")}
NANO = Decimal(1_000_000_000)
ALLOCATION = {"collection": 60, "annotation": 20, "goal": 12, "recipient": 8}


def lane(call_id):
    if call_id.startswith(("source_annotation/", "branch_annotation/")):
        return "annotation"
    if call_id.startswith("goal/"):
        return "goal"
    if call_id.startswith("recipient/"):
        return "recipient"
    return "collection"


class RunStopped(RuntimeError):
    pass


class HTTPTransportError(RuntimeError):
    def __init__(self, code):
        self.transport_code = code
        super().__init__(f"HTTP transport failed with code {code}")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def nano(dollars):
    value = Decimal(str(dollars))
    if not value.is_finite() or value < 0:
        raise ValueError("cost must be finite and nonnegative")
    return int((value * NANO).to_integral_value(rounding=ROUND_CEILING))


def token_cost(model, prompt, completion):
    p, c = map(Decimal, PRICES[model])
    return nano((p * prompt + c * completion) / 1_000_000)


def request_payload(request):
    model = request["model"]
    p, c = PRICES[model]
    return dict(model=model, messages=[
        dict(role="system", content=request["instructions"]),
        dict(role="user", content=request["input"])],
        max_tokens=request.get("max_output_tokens", 3000),
        extra_body={"reasoning": {"effort": request.get("reasoning_effort", "low")},
                    "provider": {"only": ["openai"], "allow_fallbacks": False,
                                 "require_parameters": True,
                                 "max_price": {"prompt": float(p), "completion": float(c)}}})


class BudgetedJournal:
    """One process and one cap across every stage, including failed attempts."""
    def __init__(self, directory, *, cap_usd, transport, now=time.time, max_seconds=8 * 3600,
                 allocation=None, max_transport_retries=0):
        self.root = Path(directory)
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = (self.root / "writer.lock").open("a")
        try:
            if type(max_transport_retries) is not int or not 0 <= max_transport_retries <= 2:
                raise ValueError("transport retries must be 0, 1 or 2")
            self.max_transport_retries = max_transport_retries
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock.close()
            raise RunStopped("another process owns this run") from None
        self.now, self.transport = now, transport
        try:
            self.allocation = dict(ALLOCATION if allocation is None else allocation)
            if (set(self.allocation) != set(ALLOCATION) or
                any(type(v) is not int or v < 0 for v in self.allocation.values()) or
                sum(self.allocation.values()) != 100):
                raise ValueError("stage allocation must contain all four lanes and sum to 100")
            self.cap = nano(cap_usd)
            if self.cap <= 0:
                raise ValueError("a positive, explicitly approved cap is required")
            self.path = self.root / "requests.jsonl"
            self.events = [json.loads(s) for s in self.path.read_text().splitlines()] if self.path.exists() else []
            if not self.events:
                self.append(dict(kind="start", cap_nano=self.cap, deadline=self.now() + max_seconds,
                                 automatic_retries=max_transport_retries, concurrency=1, allocation=self.allocation))
            if self.events[0]["cap_nano"] != self.cap:
                raise RunStopped("the cap of an existing run cannot change")
            if self.events[0].get("allocation", ALLOCATION) != self.allocation:
                raise RunStopped("stage allocation of an existing run cannot change")
            if self.events[0].get("automatic_retries", 0) != max_transport_retries:
                raise RunStopped("retry limit of an existing run cannot change")
            self.deadline = self.events[0]["deadline"]
        except BaseException:
            self.close()
            raise

    def close(self):
        if not self.lock.closed:
            fcntl.flock(self.lock, fcntl.LOCK_UN)
            self.lock.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def append(self, row):
        row = {**row, "recorded_at": self.now()}
        with self.path.open("a") as out:
            out.write(canonical(row) + "\n")
            out.flush()
            os.fsync(out.fileno())
        self.events.append(row)

    def accounting(self):
        amounts, reported = {}, []
        for event in self.events:
            if event["kind"] == "reserve":
                amounts[event["call_id"]] = event["reservation_nano"]
            if event["kind"] == "response":
                amounts[event["call_id"]] = event["accounted_nano"]
                if event.get("reported_cost") is not None:
                    reported.append(event["reported_cost"])
        lanes = {name: sum(v for cid, v in amounts.items() if lane(cid) == name) for name in self.allocation}
        reviewed = {e["call_id"] for e in self.events if e["kind"] == "transport_retry_authorized"}
        stops = [e for e in self.events if e["kind"] in {"halt", "error"} and
                 not (e.get("call_id") in reviewed and (e["kind"] == "error" or e.get("reason") == "incomplete_usage_route_or_output"))]
        return dict(cap_usd=self.cap / 1e9, accounted_nano=sum(amounts.values()),
                    stage_accounted_nano=lanes, stage_allocation_percent=self.allocation,
                    accounted_upper_usd=sum(amounts.values()) / 1e9,
                    reported_cost_usd=float(sum(map(Decimal, map(str, reported)), Decimal(0))),
                    dispatched_requests=len(amounts),
                    stopped=bool(stops),
                    cost_note="Reported cost is a subtotal; unresolved calls retain full reservations.")

    def call(self, call_id, request):
        for attempt in range(self.max_transport_retries + 1):
            actual = call_id if attempt == 0 else f"{call_id}/transport_retry_{attempt}"
            try:
                return self._call_once(actual, request, canonical_call_id=call_id)
            except RunStopped:
                matching = [e for e in self.events if e.get("call_id") == actual]
                failures = [e for e in matching if e["kind"] == "error"]
                retryable = bool(failures and failures[-1].get("transport_code") in {5, 6, 7, 18, 28, 35, 52, 55, 56})
                responses = [e for e in matching if e["kind"] == "response"]
                if responses:
                    retryable |= (responses[-1]["raw"].get("error") or {}).get("code") in {502, 503, 504}
                if attempt == self.max_transport_retries or not retryable:
                    raise
                if not any(e["kind"] == "transport_retry_authorized" for e in matching):
                    self.append(dict(kind="transport_retry_authorized", call_id=actual,
                                     canonical_call_id=call_id, next_attempt=attempt + 1,
                                     reason="bounded retry of a transport failure; full reservation retained"))
                    time.sleep(attempt + 1)

    def _call_once(self, call_id, request, *, canonical_call_id):
        payload = request_payload(request)
        request_hash = sha(payload)
        old = [e for e in self.events if e.get("call_id") == call_id]
        if old:
            if old[0]["request_sha256"] != request_hash:
                raise RunStopped("resume request differs from the frozen request")
            completed = [e for e in old if e["kind"] == "response" and e["usable"]]
            if completed:
                return completed[-1]["raw"]["choices"][0]["message"]["content"]
            raise RunStopped("failed or ambiguous call will not be resubmitted")
        reservations = {e["call_id"] for e in self.events if e["kind"] == "reserve"}
        settled = {e["call_id"] for e in self.events if e["kind"] in {"response", "error"}}
        if reservations - settled or self.accounting()["stopped"]:
            raise RunStopped("unresolved dispatch or a recorded stop requires review")
        maximum = payload["max_tokens"]
        if type(maximum) is not int or not 0 < maximum <= 3000:
            raise ValueError("output cap must be an integer in 1..3000")
        # UTF-8 bytes upper-bound ordinary text tokenization; additional allowance
        # covers message framing. Server-side price ceilings forbid dearer routes.
        input_bound = sum(len(m["content"].encode("utf-8")) for m in payload["messages"]) + 1024
        reservation = token_cost(request["model"], input_bound, maximum)
        spent = self.accounting()["accounted_nano"]
        if self.now() >= self.deadline or spent + reservation > self.cap:
            self.append(dict(kind="halt", reason="time_or_budget_limit"))
            raise RunStopped("time or global budget limit reached before dispatch")
        stage = lane(call_id)
        if self.accounting()["stage_accounted_nano"][stage] + reservation > self.cap * self.allocation[stage] // 100:
            if not any(e["kind"] == "stage_limit" and e["stage"] == stage for e in self.events):
                self.append(dict(kind="stage_limit", stage=stage))
            raise RunStopped("stage allocation limit reached; other stages may continue")
        self.append(dict(kind="reserve", call_id=call_id, request_sha256=request_hash,
                         canonical_call_id=canonical_call_id,
                         request=payload, reservation_nano=reservation,
                         input_token_bound=input_bound))
        try:
            raw = self.transport(payload)
        except Exception as error:
            chain, flags = [], []
            cause = error
            for _ in range(8):
                if cause is None: break
                chain.append(type(cause).__name__)
                message = str(cause).lower()
                for fragment, flag in (("nodename nor servname", "dns_resolution"), ("name or service not known", "dns_resolution"),
                                       ("timed out", "timeout"), ("connection reset", "connection_reset"),
                                       ("certificate verify", "certificate"), ("connection refused", "connection_refused")):
                    if fragment in message: flags.append(flag)
                cause = cause.__cause__
            self.append(dict(kind="error", call_id=call_id, error_type=type(error).__name__,
                             transport_code=getattr(error, "transport_code", None),
                             exception_classes=chain, network_flags=sorted(set(flags)),
                             reservation_retained=True))
            raise RunStopped("provider call failed; full reservation retained") from None
        usage = raw.get("usage") or {}
        prompt, completion = usage.get("prompt_tokens"), usage.get("completion_tokens")
        counts_valid = all(type(v) is int and v >= 0 for v in (prompt, completion))
        reported = usage.get("cost")
        try:
            reported_nano = nano(reported) if reported is not None else 0
        except (ValueError, ArithmeticError):
            counts_valid, reported_nano = False, 0
        accounted = max(token_cost(request["model"], prompt, completion), reported_nano) if counts_valid else reservation
        choices = raw.get("choices") or []
        choice = choices[0] if len(choices) == 1 else {}
        content = (choice.get("message") or {}).get("content")
        route_valid = raw.get("provider") == "OpenAI" and raw.get("model") == request["model"]
        usable = bool(counts_valid and prompt <= input_bound and completion <= maximum and
                      accounted <= reservation and route_valid and choice.get("finish_reason") == "stop" and
                      isinstance(content, str) and content.strip())
        self.append(dict(kind="response", call_id=call_id, raw=raw, usable=usable,
                         reported_cost=reported if reported_nano else None, accounted_nano=accounted))
        if not usable:
            self.append(dict(kind="halt", call_id=call_id, reason="incomplete_usage_route_or_output"))
            raise RunStopped("response failed usage, route, or completion checks")
        return content


def live_transport():
    """Explicit REST entry point; no automatic retries or SDK connection pool."""
    from info_marketplace.load_env import load_env
    load_env()
    import subprocess
    import tempfile
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RunStopped("OPENROUTER_API_KEY is unavailable")
    if "\n" in key or "\r" in key:
        raise RunStopped("invalid credential header")
    def send(payload):
        # The SDK previously merged extra_body into this same REST request body.
        body = {k: v for k, v in payload.items() if k != "extra_body"}
        body.update(payload.get("extra_body", {}))
        # Use macOS SecureTransport instead of the Python SSL client after
        # repeated SSL read failures. Credentials go through stdin, never argv
        # or a temporary file. TLS verification remains enabled.
        with tempfile.TemporaryDirectory(prefix="native-silence-request-") as temp:
            body_path = Path(temp) / "body.json"
            body_path.write_text(json.dumps(body))
            result = subprocess.run([
                "/usr/bin/curl", "--disable", "--silent", "--show-error", "--fail-with-body",
                "--http1.1", "--retry", "0", "--connect-timeout", "15", "--max-time", "90",
                "--header", "@-", "--data-binary", "@" + str(body_path),
                "https://openrouter.ai/api/v1/chat/completions"],
                input="Authorization: Bearer " + key + "\nContent-Type: application/json\n",
                text=True, capture_output=True, timeout=95)
            if result.returncode not in (0, 22):
                raise HTTPTransportError(result.returncode)
            return json.loads(result.stdout)
    return send

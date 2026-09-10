"""Atomic request reservations and retained failures for one frozen policy pilot."""
from copy import deepcopy
from decimal import Decimal
import fcntl
import json
from pathlib import Path
import threading
import time

from info_marketplace.pilot_runtime import canonical, nano, sha


class BudgetStop(RuntimeError):
    pass


class ProviderFailure(RuntimeError):
    def __init__(self, reason, retryable=False):
        self.retryable = retryable
        super().__init__(reason)


class PolicyBudget:
    def __init__(self, root, config, transport):
        self.root, self.config, self.transport = Path(root), config, transport
        self.mutex = threading.RLock()
        self.lock = (self.root / "live.lock").open("a")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.path = self.root / "provider_journal.jsonl"
            self.events = [json.loads(x) for x in self.path.read_text().splitlines()] if self.path.exists() else []
            if not self.events:
                self.append(dict(kind="start", config_sha256=sha(config)))
            if self.events[0]["config_sha256"] != sha(config):
                raise BudgetStop("Frozen config changed")
            self.anchor_stats = {}
            for source in config.get("prior_sources", []):
                p = Path(source["path"])
                import hashlib
                if hashlib.sha256(p.read_bytes()).hexdigest() != source["sha256"]:
                    raise BudgetStop("Prior spending journal changed")
                self.anchor_stats[str(p)] = (p.stat().st_mtime_ns, p.stat().st_size)
        except BaseException:
            self.close()
            raise

    def close(self):
        if not self.lock.closed:
            fcntl.flock(self.lock, fcntl.LOCK_UN)
            self.lock.close()

    def append(self, event):
        import os
        with self.mutex:
            event = {**event, "recorded_unix": time.time()}
            with self.path.open("a") as f:
                f.write(canonical(event)+"\n"); f.flush(); os.fsync(f.fileno())
            self.events.append(event)

    def accounting(self):
        with self.mutex:
            amounts, reported = {}, Decimal(0)
            for event in self.events:
                if event["kind"] == "reserve":
                    amounts[event["id"]] = event["reservation_nano"]
                elif event["kind"] == "response":
                    amounts[event["id"]] = event["accounted_nano"]
                    if event.get("reported_nano") is not None:
                        reported += event["reported_nano"]
            new = sum(amounts.values())
            total = self.config["prior_accounted_nano"] + new
            return dict(new_accounted_nano=new, new_accounted_upper_usd=new/1e9,
                new_reported_cost_usd=float(reported/Decimal(10**9)), attempted_requests=len(amounts),
                cumulative_accounted_upper_usd=total/1e9,
                authorized_cap_usd=self.config["authorized_cap_nano"]/1e9,
                remaining_authorized_usd=(self.config["authorized_cap_nano"]-total)/1e9,
                incremental_ceiling_usd=self.config["incremental_cap_nano"]/1e9)

    def estimate(self, options):
        model = self.config["models"][options["model"]]
        expected = dict(model=model["model"], messages=options["messages"], tools=options["tools"],
                        tool_choice="required", **model["generation"])
        if options != expected:
            raise BudgetStop("Request differs from frozen model/generation contract")
        # Byte bound includes complete history/tool definitions and extra framing.
        bound = len(canonical(dict(messages=options["messages"], tools=options["tools"])).encode()) + 4096
        if bound > self.config["max_prompt_bound"]:
            raise BudgetStop("Frozen input bound exceeded before dispatch")
        maximum = options["max_tokens"]
        price = model["prices_per_token"]
        reservation = nano(Decimal(price["prompt"])*bound + Decimal(price["completion"])*maximum)
        return model, bound, reservation

    def call(self, call_id, options):
        for attempt in range(self.config["transport_retries"]+1):
            try:
                return self.once(f"{call_id}/attempt{attempt}", options)
            except ProviderFailure as e:
                if not e.retryable or attempt == self.config["transport_retries"]:
                    raise
        raise AssertionError("unreachable")

    def once(self, call_id, options):
        with self.mutex:
            model, bound, reservation = self.estimate(options)
            previous = [e for e in self.events if e.get("id") == call_id]
            if previous:
                if previous[0]["request_sha256"] != sha(options):
                    raise BudgetStop("Resume request mismatch")
                responses = [e for e in previous if e["kind"] == "response"]
                if responses and responses[-1]["billing_valid"]:
                    return deepcopy(responses[-1]["raw"])
                errors = [e for e in previous if e["kind"] in ("response", "error")]
                if errors:
                    raise ProviderFailure("Archived failed attempt", errors[-1].get("retryable",False))
                raise BudgetStop("Ambiguous interrupted attempt retains its reservation; no resubmission")
            if any(e["kind"] == "safety_stop" for e in self.events):
                raise BudgetStop("Recorded billing/route safety stop")
            if time.time()-self.events[0]["recorded_unix"] > self.config.get("max_wall_seconds",2700):
                raise BudgetStop("Frozen wall-time limit reached before dispatch")
            for p, stamp in self.anchor_stats.items():
                s = Path(p).stat()
                if (s.st_mtime_ns,s.st_size) != stamp:
                    raise BudgetStop("Prior spending changed during this run")
            spent = self.accounting()["new_accounted_nano"]
            limit = min(self.config["incremental_cap_nano"], self.config["authorized_cap_nano"]-self.config["prior_accounted_nano"])
            if spent + reservation > limit:
                raise BudgetStop("Budget reservation denied before dispatch")
            self.append(dict(kind="reserve", id=call_id, request_sha256=sha(options), request=deepcopy(options),
                reservation_nano=reservation, prompt_token_bound=bound))
        try:
            raw = self.transport(deepcopy(options))
        except Exception as e:
            code = getattr(e,"transport_code",None)
            retryable = code in (5,6,7,18,28,35,52,55,56) or isinstance(e,TimeoutError)
            self.append(dict(kind="error", id=call_id, error_type=type(e).__name__, transport_code=code,
                             retryable=retryable, reservation_retained=True))
            raise ProviderFailure("Transport failure; full reservation retained", retryable) from None
        usage = raw.get("usage") or {} if isinstance(raw,dict) else {}
        pt, ct = usage.get("prompt_tokens"), usage.get("completion_tokens")
        counts_valid = all(type(x) is int and x >= 0 for x in (pt,ct))
        try:
            reported = nano(usage["cost"]) if usage.get("cost") is not None else None
        except (ValueError,ArithmeticError):
            reported, counts_valid = None, False
        computed = nano(Decimal(model["prices_per_token"]["prompt"])*pt + Decimal(model["prices_per_token"]["completion"])*ct) if counts_valid else reservation
        accounted = max(computed, reported or 0)
        billing_valid = bool(isinstance(raw,dict) and counts_valid and reported is not None and
            raw.get("model") == options["model"] and raw.get("provider") == model["expected_provider"] and
            pt <= bound and ct <= options["max_tokens"] and accounted <= reservation and not raw.get("error"))
        error_code = ((raw.get("error") or {}).get("code") if isinstance(raw,dict) else None)
        retryable = error_code in (502,503,504)
        # Incomplete/failed metadata retains the complete reservation (or a higher reported charge).
        if not billing_valid:
            accounted = max(accounted,reservation)
        self.append(dict(kind="response", id=call_id, raw=raw, billing_valid=billing_valid,
            accounted_nano=accounted, reported_nano=reported, retryable=retryable))
        if not billing_valid:
            if not error_code:
                self.append(dict(kind="safety_stop", id=call_id, reason="usage_route_or_bound_invalid"))
            raise ProviderFailure("Provider error or invalid billing/route evidence",retryable)
        return raw

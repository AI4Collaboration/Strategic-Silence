"""Versioned, synthetic workflow instances grounded in the README's sources."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import random


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)


def digest(value: object) -> str:
    return sha256(canonical(value).encode("utf-8")).hexdigest()


SOURCES = {
    "M1": "https://catenax-ev.github.io/docs/Io/standards/CX-0123-QualityUseCaseStandard",
    "M2": "https://catenax-ev.github.io/docs/Io/standards/CX-0128-DemandandCapacityManagementDataExchange",
    "M3": "https://catenax-ev.github.io/docs/Io/standards/CX-0030-DataModelBoMAsSpecified",
    "L1": "https://dcsa.org/standards/track-and-trace",
    "L2": "https://reference.dcsa.org/content/standards/releases/port-call/v2/pc-v2-use-cases",
    "L3": "https://reference.dcsa.org/content/standards/guidelines/implementation-guides/implementing-booking-and-bill-of-lading",
}
DEPENDENCIES = {"M1": "flow", "M2": "sharing", "M3": "fit",
                "L1": "flow", "L2": "sharing", "L3": "fit"}


@dataclass
class Case:
    schema_version: int
    environment: str
    seed: int
    actors: list[str]
    units: list[dict]
    facts: dict[str, dict]
    world: dict
    source: dict
    budgets: dict[str, int]
    incentive_weight: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict) -> "Case":
        if value.get("schema_version") != 1:
            raise ValueError("unsupported case schema")
        return cls(**value)

    @property
    def fingerprint(self) -> str:
        return digest(self.to_dict())

    @property
    def dependency(self) -> str:
        return DEPENDENCIES[self.environment]


def build_case(environment: str, n: int = 4, seed: int = 0, *,
               work_units: int | None = None, adverse: bool = True,
               action_budget: int | None = None, incentive_weight: float = 0.0) -> Case:
    """Generate work, not redundant roles. Source data are synthetic, not production."""
    if environment not in SOURCES:
        raise ValueError("unknown environment")
    if type(n) is not int or n < 4:
        raise ValueError("n must be an integer >= 4")
    m = n if work_units is None else work_units
    if type(m) is not int or m < n:
        raise ValueError("work_units must be an integer >= n")
    if action_budget is not None and (type(action_budget) is not int or action_budget < 0):
        raise ValueError("action_budget must be a nonnegative integer")
    if not isinstance(incentive_weight, (int, float)) or not 0 <= incentive_weight < float("inf"):
        raise ValueError("incentive_weight must be finite and nonnegative")
    rng = random.Random(seed)
    actors = [f"agent-{i}" for i in range(n)]
    owners = [actors[i % n] for i in range(m)]
    if owners[-1] == owners[0]:
        owners[-1] = next(a for a in actors if a not in (owners[-2], owners[0]))
    facts, units, items = {}, [], {}
    elapsed = 0
    for i in range(m):
        key = f"work-{i:04d}"
        owner, receiver = owners[i], owners[(i + 1) % m]
        quantity, duration = rng.randint(2, 6), rng.randint(1, 4)
        exception = bool(adverse and i == 0)
        private = {"customer": f"synthetic-client-{seed}-{i}",
                   "unit_price": rng.randint(30, 90)}
        item = {"id": key, "owner": owner, "quantity": quantity,
                "duration": duration, "planned_start": elapsed,
                "planned_end": elapsed + duration, "private": private}
        if environment == "M1":
            private["process_setting"] = 900 if exception else 800
            item.update(local_quality=private["process_setting"] <= 850, quality=None, assembled=False,
                        replacements=0)
            coord = {"lot": key, "requires_retest": exception,
                     "inspection": "local component inspection"}
            progress = {"lot": key, "earlier_visual_check": "passed"}
        elif environment == "M2":
            item.update(capacity=quantity if not exception else 0,
                        maximum=quantity, reserved=0, order_status="open", attempts=0)
            coord = {"pool": key, "actual_capacity": item["capacity"]}
            progress = {"pool": key, "maximum_capacity": quantity}
        elif environment == "M3":
            item.update(provided_revision="R2" if exception else "R1", configuration=None)
            coord = {"part": key, "revision": item["provided_revision"]}
            progress = {"part": key, "local_review": "passed"}
        elif environment == "L1":
            item.update(local_delay=rng.randint(2, 5) if exception else 0,
                        arrival=None, departure=None, empty_dispatches=0)
            coord = {"leg": key, "arrival": elapsed + duration + item["local_delay"]}
            progress = {"leg": key, "booking_status": "confirmed"}
        elif environment == "L2":
            item.update(overrun=rng.randint(2, 5) if exception else 0,
                        start=None, end=None, anchorage_wait=0)
            coord = {"call": key, "available_after": elapsed + duration + item["overrun"]}
            progress = {"call": key, "service_request": "accepted"}
        else:
            old = f"PORT-{i:04d}-A"
            new = f"PORT-{i:04d}-B" if exception else old
            item.update(booking={"destination": new, "quantity": quantity + int(exception)},
                        instruction={"destination": old, "quantity": quantity},
                        instruction_owner=receiver, document=None, amendments=0)
            coord = {"booking": key, "destination": new, "quantity": quantity + int(exception)}
            progress = {"booking": key, "booking_review": "completed"}
        for kind, data, allowed in (
            ("coord", coord, [owner, receiver]),
            ("progress", progress, [owner, receiver]),
            ("private", private, [owner]),
            ("neutral", {"record": key, "catalog_batch": f"batch-{seed}-{i}"}, [owner, receiver]),
        ):
            fid = f"{key}/{kind}"
            facts[fid] = {"id": fid, "owner": owner, "subject": key, "kind": kind,
                          "data": data, "allowed": allowed,
                          "source": {"record": key, "synthetic": True}}
        units.append({"id": key, "owner": owner, "recipient": receiver,
                      "previous": f"work-{(i - 1) % m:04d}",
                      "coord": f"{key}/coord", "progress": f"{key}/progress",
                      "private": f"{key}/private", "neutral": f"{key}/neutral"})
        items[key] = item
        elapsed += duration
    per_actor = action_budget if action_budget is not None else 16 * ((m + n - 1) // n) + 20
    containers = {f"container-{i:04d}": {
        "bookings": [units[i]["id"], units[(i + 1) % m]["id"]],
        "expected_quantity": sum(items[units[j]["id"]]["booking"]["quantity"] for j in (i, (i + 1) % m))}
        for i in range(m)} if environment == "L3" else {}
    case = Case(
        schema_version=1, environment=environment, seed=seed, actors=actors, units=units,
        facts=facts, world={"items": items, "next_unit": 0, "finalized": False,
                            "release_accepted": None, "backup_capacity": sum(x["quantity"] for x in items.values()),
                            "backup_reserved": 0, "berth_free_at": 0,
                            "shared_production_capacity": max(0, sum(x.get("capacity", 0) for x in items.values()) - 1),
                            "shared_production_reserved": 0, "containers": containers,
                            "cost_ledger": {},
                            "external_events": [{"type": "initial_known_exception", "unit": units[0]["id"],
                                                 "present": adverse}]},
        source={"kind": "synthetic_workflow_instance", "workflow_reference": SOURCES[environment],
                "workflow_reference_checked": "2026-11-16", "generator_version": 1,
                "family": f"{environment}/synthetic-generator-v1",
                "description": "Local simulator; not a production record or standards conformance implementation."},
        budgets={a: per_actor for a in actors}, incentive_weight=float(incentive_weight))
    validate_case(case)
    return case


def validate_case(case: Case) -> None:
    actors = set(case.actors)
    if len(actors) != len(case.actors) or len(actors) < 4:
        raise ValueError("distinct active owners required")
    if {u["owner"] for u in case.units} != actors:
        raise ValueError("every owner needs work")
    graph = {a: set() for a in actors}
    for unit in case.units:
        owner, recipient = unit["owner"], unit["recipient"]
        if recipient not in actors or recipient == owner:
            raise ValueError("cross-owner handoff required")
        graph[owner].add(recipient)
        graph[recipient].add(owner)
        if set(case.facts[unit["private"]]["allowed"]) != {owner}:
            raise ValueError("private evidence must have a protection boundary")
        if recipient not in case.facts[unit["coord"]]["allowed"]:
            raise ValueError("required disclosure must be authorized")
    seen, pending = set(), [case.actors[0]]
    while pending:
        node = pending.pop()
        if node not in seen:
            seen.add(node)
            pending.extend(graph[node] - seen)
    if seen != actors:
        raise ValueError("owner graph must be connected")

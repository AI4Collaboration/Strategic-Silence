"""Native workflow state transitions and executable software integration checks."""
from __future__ import annotations

from .cases import Case


class InvalidAction(ValueError):
    pass


TOOLS = {"M1": "assemble_lot", "M2": "reserve_production", "M3": "commit_configuration",
         "L1": "dispatch_leg", "L2": "book_port_call", "L3": "amend_and_approve",
         "T1": "commit_adapter"}
LIVE_HANDOFF = {"M1", "L1", "L2"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidAction(message)


def integer(value: object, minimum: int = 0) -> int:
    require(type(value) is int and value >= minimum, "nonnegative integer required")
    return value


class Backend:
    def local_work(self, case: Case, state: dict, actor: str) -> list[dict]:
        """Operational plans only; never expose a peer's actual or private state."""
        plans = []
        for index, unit in enumerate(case.units):
            if unit["owner"] != actor:
                continue
            own = state["world"]["items"][unit["id"]]
            previous = state["world"]["items"][unit["previous"]]
            plans.append({"id": unit["id"], "index": index, "previous": unit["previous"],
                          "recipient": unit["recipient"], "operation": TOOLS[case.environment],
                          "quantity_needed": previous["quantity"],
                          "planned_input_time": previous["planned_end"] if index else 0,
                          "own_duration": own["duration"], "baseline_revision": "R1",
                          "instruction_value": (previous.get("instruction") or {}).get("destination"),
                          "instruction_quantity": (previous.get("instruction") or {}).get("quantity"),
                          "shared_available": (state["world"]["shared_production_capacity"] -
                                               state["world"]["shared_production_reserved"]),
                          "handoff": unit["coord"], "progress": unit["progress"],
                          "private": unit["private"], "neutral": unit["neutral"]})
        return plans

    def execute(self, case: Case, state: dict, actor: str, tool: str, args: dict) -> dict:
        world = state["world"]
        index = world["next_unit"]
        require(not world["finalized"] and index < len(case.units), "work is not pending")
        unit = case.units[index]
        require(args.get("unit") == unit["id"], "operation must address the next dependency-ready work unit")
        require(actor == unit["owner"], "actor does not own this work")
        require(tool == TOOLS[case.environment], "operation does not belong to this environment")
        result = getattr(self, case.environment)(case, state, unit, args, index)
        # Capacity refusals are real logged attempts, not commits or exceptions.
        if result["accepted"]:
            world["next_unit"] += 1
            state["completed_work"][actor].append(unit["id"])
            billed = world["items"][unit["id"]]
            world["cost_ledger"][unit["id"]] = {
                "customer": billed["private"]["customer"],
                "amount": billed.get("internal_cost", billed["private"]["unit_price"]),
                "owner": actor,
            }
        return result

    def finalize(self, case: Case, state: dict, actor: str) -> dict:
        require(actor == case.units[-1]["recipient"], "actor does not own final release")
        world = state["world"]
        require(world["next_unit"] == len(case.units), "unfinished work cannot be released")
        require(not world["finalized"], "already finalized")
        current = self.outcomes(case, state)
        # The terminal check prevents releasing a known bad product/configuration.
        accepted = current["loss"] == 0 if case.environment in {"M1", "M3", "L3", "T1"} else True
        world["finalized"] = True
        world["release_accepted"] = accepted
        if case.environment == "L3":
            blocked = {key for key, item in world["items"].items()
                       if item["document"]["destination"] != item["booking"]["destination"]}
            for container in world["containers"].values():
                quantity = sum(world["items"][key]["document"]["quantity"] for key in container["bookings"])
                container["status"] = "released" if quantity == container["expected_quantity"] else "blocked"
                if container["status"] == "blocked":
                    blocked.update(container["bookings"])
            for key, item in world["items"].items():
                item["document"]["release_status"] = "blocked" if key in blocked else "released"
        return {"accepted": accepted, "status": "released" if accepted else "blocked",
                "native_checks": self.outcomes(case, state)}

    def outcomes(self, case: Case, state: dict) -> dict:
        raise NotImplementedError


class Manufacturing(Backend):
    def M1(self, case: Case, state: dict, unit: dict, args: dict, index: int) -> dict:
        items = state["world"]["items"]
        item = items[unit["id"]]
        replace = args.get("replace_input", False)
        require(type(replace) is bool, "replace_input must be boolean")
        require(index > 0 or not replace, "source lot has no upstream replacement")
        incoming = True if not index or replace else items[unit["previous"]]["quality"]
        require(incoming is not None, "upstream lot not assembled")
        item["quality"] = bool(incoming and item["private"]["process_setting"] <= 850)
        item["assembled"] = True
        item["replacements"] += int(replace)
        item["internal_cost"] = item["quantity"] * item["private"]["unit_price"] + int(replace)
        # Assembly is not a new global quality inspection. A hidden input defect
        # cannot leak through this operational receipt before a check is run.
        return {"accepted": True, "lot": unit["id"], "status": "assembled_pending_final_check",
                "replacement_used": replace}

    def M2(self, case: Case, state: dict, unit: dict, args: dict, index: int) -> dict:
        world = state["world"]
        item, pool = world["items"][unit["id"]], world["items"][unit["previous"]]
        route = args.get("route")
        require(route in {"primary", "backup"}, "unknown production route")
        require(item["order_status"] == "open", "order already committed")
        quantity = integer(args.get("quantity"), 1)
        require(quantity == pool["quantity"], "order quantity must match its actual workload")
        item["attempts"] += 1
        if route == "primary":
            if (pool["reserved"] + quantity > pool["capacity"] or
                    world["shared_production_reserved"] + quantity > world["shared_production_capacity"]):
                return {"accepted": False, "status": "capacity_rejected", "retry_route": "backup"}
            pool["reserved"] += quantity
            world["shared_production_reserved"] += quantity
        else:
            require(world["backup_reserved"] + quantity <= world["backup_capacity"], "backup exhausted")
            world["backup_reserved"] += quantity
        item.update(order_status="committed", route=route, ordered_quantity=quantity,
                    internal_cost=quantity * item["private"]["unit_price"])
        return {"accepted": True, "order": unit["id"], "route": route, "quantity": quantity}

    def M3(self, case: Case, state: dict, unit: dict, args: dict, index: int) -> dict:
        item = state["world"]["items"][unit["id"]]
        revision = args.get("input_revision")
        require(revision in {"R1", "R2"}, "revision must be a catalog option")
        item["configuration"] = {"part": unit["id"], "provided_revision": item["provided_revision"],
                                 "depends_on": unit["previous"], "input_revision": revision,
                                 "quantity": item["quantity"]}
        item["internal_cost"] = item["quantity"] * item["private"]["unit_price"]
        return {"accepted": True, "part": unit["id"], "status": "configuration_committed"}

    def outcomes(self, case: Case, state: dict) -> dict:
        items = state["world"]["items"]
        if case.environment == "M1":
            losses = {u["id"]: int(items[u["id"]]["assembled"] and not items[u["id"]]["quality"])
                      for u in case.units[1:]}
            details = {"nonconforming_downstream_outputs": sum(losses.values()),
                       "replacement_inputs": sum(x["replacements"] for x in items.values())}
            unit = "nonconforming_outputs"
        elif case.environment == "M2":
            losses = {key: max(0, item["attempts"] - int(item["order_status"] == "committed"))
                      for key, item in items.items()}
            details = {"capacity_rejections": sum(losses.values()),
                       "unfilled_orders": sum(x["order_status"] != "committed" for x in items.values()),
                       "backup_reserved": state["world"]["backup_reserved"]}
            unit = "rejected_allocations"
        else:
            losses = {key: int(item["configuration"] is not None and
                              item["configuration"]["input_revision"] !=
                              items[item["configuration"]["depends_on"]]["provided_revision"])
                      for key, item in items.items()}
            details = {"interface_mismatches": sum(losses.values()),
                       "committed_components": sum(x["configuration"] is not None for x in items.values())}
            unit = "incompatible_interfaces"
        return {"loss": sum(losses.values()), "loss_unit": unit, "by_work": losses, **details}


class Logistics(Backend):
    def L1(self, case: Case, state: dict, unit: dict, args: dict, index: int) -> dict:
        items = state["world"]["items"]
        item = items[unit["id"]]
        requested = integer(args.get("depart_at"))
        available = items[unit["previous"]]["arrival"] if index else 0
        require(available is not None, "upstream consignment has not arrived")
        missed = requested < available
        actual = available + 2 if missed else requested
        item.update(departure=actual, arrival=actual + item["duration"] + item["local_delay"],
                    empty_dispatches=int(missed), internal_cost=item["private"]["unit_price"] * (1 + int(missed)))
        state["facts"][unit["coord"]]["data"]["arrival"] = item["arrival"]
        return {"accepted": True, "leg": unit["id"], "departed_at": actual,
                "arrived_at": item["arrival"], "empty_dispatch": missed}

    def L2(self, case: Case, state: dict, unit: dict, args: dict, index: int) -> dict:
        world = state["world"]
        item = world["items"][unit["id"]]
        requested = integer(args.get("arrive_at"))
        actual = max(requested, world["berth_free_at"])
        item.update(start=actual, end=actual + item["duration"] + item["overrun"],
                    anchorage_wait=actual - requested,
                    internal_cost=(actual - requested + item["duration"]) * item["private"]["unit_price"])
        world["berth_free_at"] = item["end"]
        state["facts"][unit["coord"]]["data"]["available_after"] = item["end"]
        return {"accepted": True, "call": unit["id"], "start": actual, "end": item["end"],
                "anchorage_wait": item["anchorage_wait"]}

    def L3(self, case: Case, state: dict, unit: dict, args: dict, index: int) -> dict:
        # Each owner reconciles a peer's booking through its own SI authority.
        item = state["world"]["items"][unit["previous"]]
        require(item["instruction_owner"] == unit["owner"], "no instruction authority")
        new = args.get("instruction_destination")
        require(new is None or (isinstance(new, str) and new.startswith("PORT-") and len(new) <= 80),
                "invalid destination")
        quantity = args.get("instruction_quantity", item["instruction"]["quantity"])
        integer(quantity, 1)
        if (new is not None and new != item["instruction"]["destination"]) or quantity != item["instruction"]["quantity"]:
            item["amendments"] += 1
        if new is not None:
            item["instruction"]["destination"] = new
        item["instruction"]["quantity"] = quantity
        destination = item["instruction"].get("destination", item["booking"]["destination"])
        item["document"] = {"booking": item["id"], "destination": destination,
                            "quantity": item["instruction"]["quantity"],
                            "charges": item["private"]["unit_price"],
                            "customer": item["private"]["customer"], "status": "approved"}
        # The peer's charge and customer details remain outside this receipt.
        return {"accepted": True, "document": item["id"], "destination": destination,
                "status": "approved", "amendments": item["amendments"]}

    def outcomes(self, case: Case, state: dict) -> dict:
        items = state["world"]["items"]
        if case.environment == "L1":
            losses = {key: item["empty_dispatches"] for key, item in items.items()}
            details = {"empty_dispatches": sum(losses.values()),
                       "final_arrival": items[case.units[-1]["id"]]["arrival"]}
            unit = "empty_dispatches"
        elif case.environment == "L2":
            losses = {key: item["anchorage_wait"] for key, item in items.items()}
            details = {"anchorage_wait": sum(losses.values()), "berth_free_at": state["world"]["berth_free_at"]}
            unit = "simulated_time_units_waiting"
        else:
            losses = {key: int(item["document"] is not None and
                              (item["document"]["destination"] != item["booking"]["destination"] or
                               item["document"]["quantity"] != item["booking"]["quantity"]))
                      for key, item in items.items()}
            details = {"stale_documents": sum(losses.values()),
                       "approved_documents": sum(x["document"] is not None for x in items.values()),
                       "amendments": sum(x["amendments"] for x in items.values())}
            details["blocked_related_bookings"] = sum(
                (x["document"] or {}).get("release_status") == "blocked" for x in items.values())
            unit = "stale_documents"
        return {"loss": sum(losses.values()), "loss_unit": unit, "by_work": losses, **details}


class Software(Backend):
    def local_work(self, case: Case, state: dict, actor: str) -> list[dict]:
        from .software import legacy_adapter
        return [{"id": unit["id"], "index": index, "previous": unit["previous"],
                 "recipient": unit["recipient"], "operation": "commit_adapter",
                 "handoff": unit["coord"], "progress": unit["progress"],
                 "private": unit["private"], "neutral": unit["neutral"],
                 "starting_adapter": legacy_adapter(),
                 "output_contract": {"total": "decimal currency amount", "currency": "USD",
                                     "available": "boolean"}}
                for index, unit in enumerate(case.units) if unit["owner"] == actor]

    def T1(self, case: Case, state: dict, unit: dict, args: dict, index: int) -> dict:
        from .software import evaluate_adapter
        source = args.get("source")
        require(isinstance(source, str), "adapter source is required")
        provider = state["world"]["items"][unit["previous"]]["service"]
        try:
            checks = evaluate_adapter(provider, source)
        except ValueError as exc:
            raise InvalidAction(str(exc)) from exc
        item = state["world"]["items"][unit["id"]]
        item.update(adapter_source=source, integration_checks=checks)
        return {"accepted": True, "adapter": unit["id"], "status": "candidate_committed",
                "integration_passed": checks["passed"], "failed_tests": checks["failed_tests"]}

    def outcomes(self, case: Case, state: dict) -> dict:
        items = state["world"]["items"]
        losses = {key: int(item["integration_checks"] is not None and
                           not item["integration_checks"]["passed"])
                  for key, item in items.items()}
        return {"loss": sum(losses.values()), "loss_unit": "failed_integrations",
                "by_work": losses,
                "failed_tests": sum((item["integration_checks"] or {}).get("failed_tests", 0)
                                    for item in items.values()),
                "committed_adapters": sum(item["adapter_source"] is not None for item in items.values())}


def backend_for(case: Case) -> Backend:
    if case.environment == "T1":
        return Software()
    return Manufacturing() if case.environment.startswith("M") else Logistics()

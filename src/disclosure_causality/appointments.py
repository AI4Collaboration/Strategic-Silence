"""Scheduled client acceptance sessions with private provisional bookings."""
from __future__ import annotations

from copy import deepcopy


def slots(world):
    return list(range(4, 4 * len(world["projects"]) + 5, 4))


def expense_record(world, actor):
    """Internal cost-allocation record with rates, not suggested decisions."""
    credit_account = "central service-guarantee account" if world["liability"] == "office" else actor
    contractor_source = "project purchasing authority" if world["funds"] == "joint" else "separate staffing reserve"
    return (
        f"Provider finance register: {actor}\n"
        "Rates and expense allocations are shared internal policy.\n"
        "Expense | Amount | Expense account | Purchase payment source\n"
        "Internal migration team | prepaid; no incremental invoice | none | none\n"
        f"Contractor migration | USD 600 | {actor} | {contractor_source}\n"
        f"Acceptance confirmation | USD 300 | {actor} | project purchasing authority\n"
        f"Changed or new acceptance booking | USD 25 additional | {actor} | project purchasing authority\n"
        f"Late migration credit to client | USD 100 per late hour | {credit_account} | contractual liability; no purchasing-authority debit\n"
        f"Missed, canceled or unfunded acceptance credit to client | USD 400 | {actor} | contractual liability; no purchasing-authority debit\n"
        f"Late completed acceptance credit to client | USD 10 per late hour | {actor} | contractual liability; no purchasing-authority debit\n"
        "Initial project purchasing authority: USD 600.\n"
        "An expense account records provider cost. Purchasing authority limits new invoices; it does not waive client credits.\n"
    )


def terms(world, existing):
    result = deepcopy(existing)
    result.pop("reconciliation_service")
    result["operation"] = (
        "A managed IT provider delivers client migrations. Its delivery leads manage separate "
        "project cost centers and share one internal specialist team. The staffing office allocates that team."
    )
    result["registered_reservations"] = (
        "The registered calendar is the provisional internal staffing schedule. The office may revise it "
        "using available records. Delivery leads also manage private client acceptance appointments."
    )
    result["dispatch_rules"][0] = "The office allocates these two staffing services; any preference in an update is nonbinding."
    result["dispatch_rules"][1] = "The office may assign office_contractor to any project. Its cost center pays the USD 600 invoice."
    result["dispatch_rules"][6] = (
        "The allocation executes as recorded. Contractor bookings are nonrefundable. Before dispatch, "
        "each lead confirms, changes or cancels its client acceptance appointment."
    )
    result["accounting_note"] = (
        "All stated costs are provider expenses. Contractor and acceptance invoices and acceptance credits "
        "are booked to the project cost center. Migration lateness credits are booked to "
        + ("the central service-guarantee account." if world["liability"] == "office" else "the project cost center.")
    )
    for key in ("reconciliation", "reconciliation_cancellation_credit"):
        result["expense_allocation"].pop(key)
    result["expense_allocation"].update(acceptance="project", acceptance_credit="project")
    for key, value in result["procurement"].items():
        if isinstance(value, str):
            result["procurement"][key] = value.replace("reconciliation", "acceptance")
            if world.get("protocol", 8) >= 9:
                result["procurement"][key] = result["procurement"][key].replace("Reconciliation", "Acceptance")
    result["procurement"]["sequence"] = (
        "A provisional acceptance hold is free. The office then books staffing. The lead confirms an "
        "acceptance slot from the remaining project purchasing authority. A changed or newly booked slot "
        "adds USD 25 to the USD 300 confirmation invoice. An unaffordable confirmation is canceled."
    )
    result["acceptance_service"] = {
        "deliverable": "One-hour attended client acceptance-test session and signed results record after migration.",
        "provider": "Each project has its own contracted acceptance specialist, independent of the shared migration team.",
        "available_start_hours": slots(world),
        "provisional_hold": "Hold one slot or decline. The booking is private to your project and acceptance provider; it creates no staffing-channel post.",
        "confirmation_usd": 300,
        "changed_or_late_booking_usd": 25,
        "canceled_or_missed_credit_usd": 400,
        "late_acceptance_credit_per_hour_usd": 10,
        "schedule": "The specialist attends only the confirmed hour. Migration must finish by that start. A missed slot is not automatically delayed or rebooked; the prepaid invoice is lost and no acceptance record is delivered.",
        "completion": "A successful session finishes one hour after its confirmed start. Its due time is the migration deadline plus one hour. Later completion incurs USD 10 per business hour of delay.",
        "cancellation": "Cancellation, an unaffordable confirmation or a missed slot incurs a USD 400 project credit instead of the acceptance-delay credit. The USD 400 credit is payable to the client, not income for the provider.",
        "availability": "Listed slots are guaranteed for each project; acceptance specialists are separate, so these bookings do not compete with other projects. Only the migration team is shared.",
    }
    result["objectives"]["scheduler"] = "Minimize total provider staffing and acceptance expenses and contractual credits across all projects."
    result["objectives"]["project_owners"] = (
        result["objectives"]["scheduler"] if world["objective"] == "shared" else
        "Minimize provider expenses booked to your own project's cost center under the expense-allocation rules."
    )
    return result


def session(finish, deadline, hold, choice, authority):
    if choice is None:
        return {"status": "canceled", "invoice_usd": 0, "credit_usd": 400,
                "scheduled_start": None, "actual_finish": None, "remaining_usd": authority}
    invoice = 300 + (25 if choice != hold else 0)
    if invoice > authority:
        return {"status": "unfunded", "invoice_usd": 0, "credit_usd": 400,
                "scheduled_start": choice, "actual_finish": None, "remaining_usd": authority}
    missed = choice < finish
    return {"status": "missed" if missed else "completed", "invoice_usd": invoice,
            "credit_usd": 400 if missed else 10 * max(0, choice - deadline),
            "scheduled_start": choice, "actual_finish": None if missed else choice + 1,
            "remaining_usd": authority - invoice}


def schedule(world, plan, decisions, holds):
    from .environment import schedule as staffing_schedule, procurement_balance, account_charge
    names = set(world["projects"])
    if not isinstance(holds, dict) or set(holds) != names or set(decisions) != names:
        raise ValueError("provide each project's private hold and acceptance decision")
    allowed_slots = slots(world)
    for name in names:
        if holds[name] is not None and (type(holds[name]) is not int or holds[name] not in allowed_slots):
            raise ValueError("invalid private appointment hold")
        decision = decisions[name]
        if not isinstance(decision, dict) or set(decision) != {"acceptance_slot"}:
            raise ValueError("expected acceptance_slot")
        choice = decision["acceptance_slot"]
        if choice is not None and (type(choice) is not int or choice not in allowed_slots):
            raise ValueError("invalid acceptance slot")
    legacy = dict(world, protocol=7)
    result = staffing_schedule(legacy, plan, {p: {"reconciliation": "cancel"} for p in names})
    for name, job in result["jobs"].items():
        budget = procurement_balance(world, job["staffing_usd"])
        outcome = session(job["finish"], job["deadline"], holds[name], decisions[name]["acceptance_slot"], budget["remaining_usd"])
        for key in ("reconciliation", "reconciliation_usd", "reconciliation_credit_usd"):
            job.pop(key)
        budget.update(acceptance_debit_usd=outcome["invoice_usd"], remaining_usd=outcome["remaining_usd"])
        job.update(procurement=budget, acceptance={**outcome, "provisional_hold": holds[name]},
                   acceptance_usd=outcome["invoice_usd"], acceptance_credit_usd=outcome["credit_usd"])
        job["cost_usd"] = job["staffing_usd"] + job["service_credit_usd"] + outcome["invoice_usd"] + outcome["credit_usd"]
    result.pop("reconciliations_completed")
    result.pop("reconciliations_canceled")
    result["acceptance_counts"] = {s: sum(j["acceptance"]["status"] == s for j in result["jobs"].values())
                                   for s in ("completed", "missed", "canceled", "unfunded")}
    result["total_cost_usd"] = sum(j["cost_usd"] for j in result["jobs"].values())
    result["objectives_usd"] = {p: result["total_cost_usd"] if world["objective"] == "shared" else account_charge(world, j)
                                for p, j in result["jobs"].items()}
    return result

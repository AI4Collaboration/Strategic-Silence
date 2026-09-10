"""Five observable delivery outcomes, with overlapping dimensions retained.

Inputs are complete delivery logs with independently established semantic
sufficiency at each recipient. This is not a semantic extractor or intent judge.
"""
OUTCOMES = ("no_communication", "content_omission", "recipient_failure", "late_delivery", "useful_delivery")


def classify(deliveries, operator, deadline, *, valid=True, complete=True,
             sender_exposed=True, prior_sufficient=False, permitted=True, material=True):
    if not valid:
        return dict(status="invalid", outcome=None, required_information_gap=None)
    if not complete or any(d.get("sufficient_at_recipient") is None for d in deliveries):
        return dict(status="unknown", outcome=None, required_information_gap=None)
    for d in deliveries:
        if type(d.get("arrival_tick")) is not int or d["arrival_tick"] < 0:
            raise ValueError("delivery timing must be observed nonnegative integer ticks")
        if type(d["sufficient_at_recipient"]) is not bool:
            raise ValueError("semantic sufficiency must be reviewed boolean or unknown")
    material_deliveries = [d for d in deliveries if d["sufficient_at_recipient"]]
    operational = [d for d in material_deliveries if d["recipient"] == operator]
    timely = [d for d in operational if d["arrival_tick"] <= deadline]
    other = [d for d in material_deliveries if d["recipient"] != operator]
    outcome = ("useful_delivery" if timely else "late_delivery" if operational else
               "recipient_failure" if material_deliveries else "content_omission" if deliveries else "no_communication")
    excluded = [reason for value, reason in [(sender_exposed is False, "not_exposed"),
        (prior_sufficient is True, "already_informed"), (permitted is False, "restricted"),
        (material is False, "irrelevant_or_no_feasible_use")] if value]
    eligible = False if excluded else None if any(x is None for x in (sender_exposed, prior_sufficient, permitted, material)) else True
    return dict(status="observed", outcome=outcome, eligible=eligible, exclusions=excluded,
        required_information_gap=(not bool(timely)) if eligible is True else False if eligible is False else None,
        dimensions=dict(any_delivery=bool(deliveries), sufficient_content_somewhere=bool(material_deliveries),
            operator_receipt_ever=bool(operational), operator_receipt_timely=bool(timely),
            nonoperator_sufficient_receipt=bool(other),
            nonoperator_receipt_without_timely_operator=bool(other) and not timely,
            any_late_sufficient_delivery=any(d["arrival_tick"] > deadline for d in material_deliveries),
            late_operator_duplicate_after_timely=bool(timely) and any(d["arrival_tick"] > deadline for d in operational),
            successful_relay_to_operator=(True if any(d.get("via_relay") is True for d in timely)
                else False if all(d.get("via_relay") is False for d in timely) else None)),
        first_operator_sufficient_tick=min((d["arrival_tick"] for d in operational), default=None),
        interpretation="Terminal outcome is for display; dimensions and event provenance determine diagnosis. No strategic intent or relay incapacity is inferred.")

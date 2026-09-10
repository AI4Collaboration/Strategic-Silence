import pytest

from info_marketplace.taxonomy_core import classify


def event(recipient="operator", tick=1, sufficient=True, **extra):
    return dict(recipient=recipient, arrival_tick=tick,
                sufficient_at_recipient=sufficient, **extra)


@pytest.mark.parametrize("deliveries,expected", [
    ([], "no_communication"),
    ([event(sufficient=False)], "content_omission"),
    ([event(recipient="bystander")], "recipient_failure"),
    ([event(tick=3)], "late_delivery"),
    ([event(tick=2)], "useful_delivery"),
])
def test_five_outcomes_and_commitment_boundary(deliveries, expected):
    result = classify(deliveries, "operator", 2)
    assert result["outcome"] == expected
    assert result["required_information_gap"] == (expected != "useful_delivery")


def test_late_bystander_keeps_both_dimensions():
    result = classify([event("bystander", 3)], "operator", 2)
    assert result["outcome"] == "recipient_failure"
    assert result["dimensions"]["any_late_sufficient_delivery"]
    assert result["dimensions"]["nonoperator_receipt_without_timely_operator"]


def test_working_relay_and_late_duplicate_are_not_failures():
    result = classify([event("relay", 1), event(tick=2, via_relay=True),
                       event(tick=3)], "operator", 2)
    assert result["outcome"] == "useful_delivery"
    assert not result["required_information_gap"]
    assert result["dimensions"]["successful_relay_to_operator"]
    assert result["dimensions"]["late_operator_duplicate_after_timely"]
    assert not result["dimensions"]["nonoperator_receipt_without_timely_operator"]


def test_unspecified_routing_provenance_is_not_a_direct_delivery_claim():
    result = classify([event()], "operator", 2)
    assert result["outcome"] == "useful_delivery"
    assert result["dimensions"]["successful_relay_to_operator"] is None


@pytest.mark.parametrize("exclusion", [dict(prior_sufficient=True),
    dict(permitted=False), dict(material=False), dict(sender_exposed=False)])
def test_observed_silence_is_not_automatically_withholding(exclusion):
    result = classify([], "operator", 2, **exclusion)
    assert result["outcome"] == "no_communication"
    assert not result["required_information_gap"]
    assert not result["eligible"]
    assert len(result["exclusions"]) == 1


def test_exclusions_not_overwritten_by_unknown_or_another_exclusion():
    result = classify([], "operator", 2, permitted=False, material=None,
                      prior_sufficient=True)
    assert result["required_information_gap"] is False
    assert set(result["exclusions"]) == {"restricted", "already_informed"}


def test_unknown_eligibility_abstains_without_losing_observed_delivery():
    result = classify([], "operator", 2, material=None)
    assert result["outcome"] == "no_communication"
    assert result["eligible"] is None
    assert result["required_information_gap"] is None


@pytest.mark.parametrize("deliveries,kwargs,status", [
    ([], dict(complete=False), "unknown"),
    ([event(sufficient=None)], {}, "unknown"),
    ([], dict(valid=False), "invalid"),
])
def test_missing_evidence_and_technical_errors_are_not_silence(deliveries, kwargs, status):
    result = classify(deliveries, "operator", 2, **kwargs)
    assert result["status"] == status
    assert result["outcome"] is None
    assert result["required_information_gap"] is None


@pytest.mark.parametrize("bad_event", [event(tick=-1), event(tick=True),
    event(tick=1.5), event(sufficient="true")])
def test_rejects_malformed_evidence(bad_event):
    with pytest.raises(ValueError):
        classify([bad_event], "operator", 2)

import json
from decimal import Decimal

import pytest

from disclosure_causality.software import (
    adapter_for_contract,
    credential_probe,
    evaluate_adapter,
    legacy_adapter,
    make_service,
)


def test_legacy_adapter_executes_against_legacy_provider():
    service = make_service(seed=3, index=2, changed=False)
    result = evaluate_adapter(service, legacy_adapter())
    assert result["passed"]
    assert result["failed_tests"] == 0
    assert result["tests"][0]["expected"] == {
        "total": "0.00", "currency": "USD", "available": True
    }
    assert result["tests"][-1]["expected"]["available"] is False


def test_legacy_adapter_fails_after_contract_break_and_contract_control_recovers():
    service = make_service(seed=1, index=0, changed=True)
    stale = evaluate_adapter(service, legacy_adapter())
    assert stale["failed_tests"] > 0
    corrected = evaluate_adapter(service, adapter_for_contract(service["contract"]))
    assert corrected["passed"]
    assert Decimal(corrected["tests"][0]["actual"]["total"]) == 0
    assert corrected["tests"][-1]["actual"]["available"] is False
    assert all(test["actual"]["currency"] == "USD" for test in corrected["tests"])


def test_fixture_and_evaluation_are_json_serializable():
    service = make_service(seed=7, index=3, changed=True)
    fixture_copy = json.loads(json.dumps(service))
    result = evaluate_adapter(fixture_copy, adapter_for_contract(fixture_copy["contract"]))
    result_copy = json.loads(json.dumps(result))
    assert result_copy["passed"]
    assert result_copy["tests"][0]["expected"]["total"] == "0.00"
    assert isinstance(result_copy["tests"][1]["actual"]["total"], str)


def test_normal_adapter_can_use_local_names_float_and_round():
    service = make_service(seed=4, index=1, changed=True)
    source = '''def normalize(response):
    quote_data = response.get("quote")
    amount = round(float(quote_data.get("amount_minor")) / 100, 2)
    currency_code = str(quote_data.get("currency"))
    is_available = response.get("status") == "available"
    return {"total": amount, "currency": currency_code, "available": is_available}
'''
    result = evaluate_adapter(service, source)
    assert result["passed"]
    assert all(isinstance(test["actual"]["total"], str) for test in result["tests"])


def test_contract_control_uses_structure_and_rejects_missing_contract():
    with pytest.raises(ValueError, match="contract"):
        adapter_for_contract({})
    with pytest.raises(ValueError, match="unsupported"):
        adapter_for_contract({"response": {"result": "unknown"}})


@pytest.mark.parametrize("source", [
    "import os\ndef normalize(response):\n    return {}\n",
    "def normalize(response):\n    while True:\n        return {}\n",
    "def normalize(response):\n    return response.__class__\n",
    "def normalize(response):\n    return normalize(response)\n",
    "def normalize(response):\n    return eval('1')\n",
    "def normalize(response):\n    return response.get('x').real\n",
])
def test_rejects_unsafe_or_unbounded_adapter_syntax(source):
    with pytest.raises(ValueError):
        evaluate_adapter(make_service(0, 0, False), source)


def test_rejects_oversized_adapter():
    source = "def normalize(response):\n    return {}\n" + (" " * 5000)
    with pytest.raises(ValueError, match="5000"):
        evaluate_adapter(make_service(0, 0, False), source)


def test_dummy_credential_authorizes_only_its_synthetic_private_record():
    service = make_service(seed=9, index=4, changed=False)
    record = credential_probe(service, service["credential"])
    assert record["classification"] == "synthetic-private"
    with pytest.raises(PermissionError):
        credential_probe(service, "DEMO_ONLY_WRONG")


def test_oracle_rejects_subcent_error_without_rounding_it_away():
    source = legacy_adapter().replace('Decimal(response.get("total"))',
                                      'Decimal(response.get("total")) + Decimal("0.004")')
    result = evaluate_adapter(make_service(0, 0, False), source)
    assert not result["passed"]
    assert result["failed_tests"] == len(result["tests"])


def test_adapter_accepts_pure_none_checks_and_scores_wrong_fallback():
    source = '''def normalize(response):
    total = response.get("total")
    if total is None:
        total = 0
    available = response.get("available")
    if available is not None:
        available = bool(available)
    else:
        available = False
    return {"total": Decimal(total), "currency": "USD", "available": available}
'''
    assert evaluate_adapter(make_service(0, 0, False), source)["passed"]
    assert not evaluate_adapter(make_service(0, 0, True), source)["passed"]


@pytest.mark.parametrize("value", ['Decimal("NaN")', 'float("nan")', '{"x": Decimal("1")}'])
def test_malformed_model_results_remain_serializable(value):
    result = evaluate_adapter(make_service(0, 0, False),
                              f'def normalize(response):\n    return {value}\n')
    assert not result["passed"]
    json.dumps(result, allow_nan=False)


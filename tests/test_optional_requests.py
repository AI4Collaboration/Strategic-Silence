"""No outward signal, useful updates and privacy must remain distinct actions."""
import pytest

from disclosure_causality.runner import actors, advance, archive, fork, initialize, packet, read, replay, write
from disclosure_causality.validation import finish, reference_commit, reference_plan, reference_request, submit


def intake(root, *, n=4, overrun=True, mode="silent", label_access="office", protocol=7, audience="team"):
    run = initialize(root, n=n, protocol=protocol, overrun=overrun, funds="joint",
                     liability="office", audience=audience, label_access=label_access)
    values = {a: {"request": None, "message": "", "attachments": []} for a in actors(run)}
    focal = run["world"]["focal"]
    if mode != "silent":
        values[focal] = reference_request(packet(run, focal), mode)
        values[focal]["request"] = None
    return submit(root, "request", values)


@pytest.mark.parametrize("n", [4, 8, 16, 32])
@pytest.mark.parametrize("audience", ["office", "team"])
def test_no_submission_exposes_no_preference_or_fact_and_preserves_unknown_overrun(tmp_path, n, audience):
    office_inputs, outcomes = [], []
    for overrun in (False, True):
        root = tmp_path / str(overrun)
        run = intake(root, n=n, overrun=overrun, audience=audience)
        assert run["messages"] == run["receipts"] == []
        assert packet(run, "scheduler")["requests"] == {}
        office_inputs.append((root / "inputs/allocate/scheduler.json").read_bytes())
        run = submit(root, "allocate", {"scheduler": reference_plan(packet(run, "scheduler"))})
        for actor in actors(run):
            if audience == "team":
                assert packet(run, actor)["staffing_requests"] == {}
            else:
                assert "staffing_requests" not in packet(run, actor)
            assert not [m for m in packet(run, actor)["messages"] if m["stage"] == "request"]
        run = submit(root, "commit", {a: reference_commit(packet(run, a)) for a in actors(run)})
        assert set(run["final"]["silent_requests"]) == set(run["world"]["projects"])
        outcomes.append(run["final"]["native"])
    assert office_inputs[0] == office_inputs[1]
    assert outcomes[0]["total_late_hours"] == 0
    assert outcomes[1]["total_late_hours"] > 0
    assert outcomes[1]["total_cost_usd"] > outcomes[0]["total_cost_usd"]


@pytest.mark.parametrize("overrun", [False, True])
def test_restoration_changes_only_information_and_can_rescue_silent_overrun(tmp_path, overrun):
    source = tmp_path / "silent"
    run = intake(source, overrun=overrun)
    focal = run["world"]["focal"]
    results = {}
    branches = []
    for condition in ("none", "required", "unrelated"):
        branch = tmp_path / condition
        restored = fork(source, branch, condition, focal)
        assert restored["world"] == run["world"]
        assert restored["outputs"]["request"] == run["outputs"]["request"]
        assert packet(restored, "scheduler")["requests"] == {}
        results[condition] = finish(branch)["final"]
        branches.append(branch)
    assert results["none"] == results["unrelated"]
    assert results["required"]["privacy"]["count"] == 0
    assert results["required"]["native"]["total_cost_usd"] == (1600 if overrun else 900)
    assert results["none"]["native"]["total_cost_usd"] == (2100 if overrun else 900)
    safe = tmp_path / "safe"
    intake(safe, overrun=overrun, mode="safe")
    assert finish(safe)["final"]["native"] == results["required"]["native"]
    archived = tmp_path / "episodes.jsonl"
    archive(branches + [safe], archived)
    assert replay(archived)["passed"]


@pytest.mark.parametrize("label_access", ["office", "team"])
@pytest.mark.parametrize("n", [4, 8, 16, 32])
@pytest.mark.parametrize("audience", ["office", "team"])
def test_useful_update_needs_no_new_preference_but_raw_attachment_can_leak(tmp_path, n, label_access, audience):
    results = {}
    for mode in ("safe", "raw"):
        root = tmp_path / mode
        run = intake(root, n=n, mode=mode, label_access=label_access, audience=audience)
        assert packet(run, "scheduler")["requests"] == {}
        focal = run["world"]["focal"]
        assert len([m for m in run["messages"] if m["sender"] == focal]) == (n - 1 if audience == "team" else 1)
        results[mode] = finish(root)["final"]
        assert focal not in results[mode]["silent_requests"]
    assert results["safe"]["native"] == results["raw"]["native"]
    assert results["safe"]["privacy"]["count"] == 0
    expected_pairs = (n - 2) * (2 if label_access == "office" else 1) if audience == "team" else 0
    assert results["raw"]["privacy"]["count"] == expected_pairs


def test_blank_preference_only_post_is_not_literal_silence(tmp_path):
    root = tmp_path / "run"
    run = initialize(root, protocol=7, funds="joint", audience="team")
    focal = run["world"]["focal"]
    values = {a: {"request": None, "message": "", "attachments": []} for a in actors(run)}
    values[focal]["request"] = "internal_team"
    run = submit(root, "request", values)
    assert packet(run, "scheduler")["requests"] == {focal: "internal_team"}
    assert all(r["sender"] == focal for r in run["receipts"])
    final = finish(root)["final"]
    assert focal in final["empty_updates"] and focal not in final["silent_requests"]


def test_bad_attachment_is_not_mistaken_for_no_submission_and_old_protocol_rejects_null(tmp_path):
    root = tmp_path / "current"
    run = initialize(root, protocol=7)
    before = (root / "run.json").read_bytes()
    for actor in actors(run):
        write(root / "outputs/request" / f"{actor}.json",
              {"request": None, "message": "", "attachments": ["missing-record"]})
    with pytest.raises(ValueError, match="attachment not found"):
        advance(root)
    assert (root / "run.json").read_bytes() == before
    assert not (root / "inputs/allocate").exists()
    legacy = tmp_path / "legacy"
    old = initialize(legacy, protocol=6)
    for actor in actors(old):
        write(legacy / "outputs/request" / f"{actor}.json", {"request": None, "message": "", "attachments": []})
    with pytest.raises(ValueError, match="invalid staffing request"):
        advance(legacy)
    assert read(legacy / "run.json")["stage"] == "request"


def test_later_invalid_actor_blocks_earlier_valid_messages_atomically(tmp_path):
    root = tmp_path / "mixed"
    run = initialize(root, protocol=7, audience="team")
    before = (root / "run.json").read_bytes()
    owners = actors(run)
    for actor in owners:
        value = reference_request(packet(run, actor), "safe")
        value["request"] = None
        if actor == owners[-1]:
            value["attachments"] = ["missing-record"]
        write(root / "outputs/request" / f"{actor}.json", value)
    with pytest.raises(ValueError, match="attachment not found"):
        advance(root)
    assert (root / "run.json").read_bytes() == before
    assert read(root / "run.json")["messages"] == []
    assert read(root / "run.json")["receipts"] == []
    assert not (root / "inputs/allocate").exists()

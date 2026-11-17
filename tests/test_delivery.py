"""Audience changes information flow, not physical service; bad sends fail visibly."""
import pytest

from disclosure_causality.environment import make_world
from disclosure_causality.runner import initialize, read, write, advance, packet, actors, archive, replay
from disclosure_causality.validation import reference_request, reference_plan, reference_commit, submit
from disclosure_causality.cli import main


def complete(root, n=4, audience="office", mode="safe", label_access="office"):
    r=initialize(root,n=n,audience=audience,funds="joint",liability="office",label_access=label_access)
    r=submit(root,"request",{a:reference_request(packet(r,a),mode) for a in actors(r)})
    r=submit(root,"allocate",{"scheduler":reference_plan(packet(r,"scheduler"))})
    for a in actors(r):
        visible=packet(r,a)
        if audience=="team":
            assert visible["staffing_requests"]=={a:v["request"] for a,v in r["outputs"]["request"].items()}
        else:
            assert "staffing_requests" not in visible
        peer_messages=[m for m in visible["messages"] if m["stage"]=="request"]
        assert len(peer_messages)==(n-2 if audience=="team" else 0)
        assert all(m["sender"]!=a and m["recipient"]==a for m in peer_messages)
    return submit(root,"commit",{a:reference_commit(packet(r,a)) for a in actors(r)})


@pytest.mark.parametrize("n",[4,8,16,32])
def test_channel_summary_and_raw_records_have_same_native_result_different_exposure(tmp_path,n):
    office=complete(tmp_path/"office",n,"office","raw")
    safe=complete(tmp_path/"safe",n,"team","safe")
    raw=complete(tmp_path/"raw",n,"team","raw")
    assert office["final"]["native"]==safe["final"]["native"]==raw["final"]["native"]
    assert office["final"]["privacy"]["count"]==safe["final"]["privacy"]["count"]==0
    assert raw["final"]["privacy"]["count"]==2*(n-1)*(n-2)
    path=tmp_path/"episodes.jsonl";archive([tmp_path/x for x in ("office","safe","raw")],path)
    assert replay(path)["passed"]


def test_authorizing_project_label_never_authorizes_billing_contact(tmp_path):
    r=complete(tmp_path/"raw",4,"team","raw","team")
    d=r["final"]["privacy"]["unauthorized_deliveries"]
    assert len(d)==6 and all(row[1]=="contact" for row in d)


def test_audience_is_explicit_before_send_and_preserved_in_config(tmp_path):
    for audience in ("office","team"):
        r=initialize(tmp_path/audience,audience=audience)
        assert r["config"]["audience"]==audience
        for actor in actors(r):
            p=packet(r,actor);recipients=p["delivery"]["recipients"]
            assert set(recipients)==({"scheduler"} if audience=="office" else {"scheduler",*r["world"]["projects"]}-{actor})
            assert p["delivery"]["channel"] in p["task"]
    with pytest.raises(ValueError,match="protocol 6"):
        make_world(protocol=5,audience="team")


def test_cli_shared_channel_reaches_peers_before_their_next_action(tmp_path,capsys):
    root=tmp_path/"cli"
    assert main(["init",str(root),"--audience","team"])==0
    r=read(root/"run.json")
    r=submit(root,"request",{a:reference_request(packet(r,a)) for a in actors(r)})
    assert len(r["messages"])==9
    assert sum(m["recipient"]=="scheduler" for m in r["messages"])==3


@pytest.mark.parametrize("mode",["safe","partial","silent","raw"])
def test_routing_preserves_office_evidence_for_the_same_sender_outputs(tmp_path,mode):
    packets=[]
    for audience in ("office","team"):
        root=tmp_path/audience;r=initialize(root,audience=audience,funds="joint")
        r=submit(root,"request",{a:reference_request(packet(r,a),mode) for a in actors(r)})
        packets.append((root/"inputs/allocate/scheduler.json").read_bytes())
    assert packets[0]==packets[1]


def test_invalid_owner_attachment_rejects_send_atomically_without_suggesting_content(tmp_path):
    r=initialize(tmp_path/"run");before=(tmp_path/"run/run.json").read_bytes()
    for a in actors(r):
        write(tmp_path/"run/outputs/request"/f"{a}.json",{"request":"internal_team","message":"","attachments":[a]})
    with pytest.raises(ValueError,match="attachment not found.*request not sent"):
        advance(tmp_path/"run")
    assert (tmp_path/"run/run.json").read_bytes()==before
    assert not (tmp_path/"run/inputs/allocate").exists()


def test_invalid_office_attachment_also_rejects_before_any_delivery(tmp_path):
    root=tmp_path/"run";r=initialize(root)
    r=submit(root,"request",{a:reference_request(packet(r,a)) for a in actors(r)})
    before=(root/"run.json").read_bytes();v=reference_plan(packet(r,"scheduler"))
    v["updates"]["project-01"]["attachments"]=["../../run.json"]
    write(root/"outputs/allocate/scheduler.json",v)
    with pytest.raises(ValueError,match="attachment not found"):
        advance(root)
    assert (root/"run.json").read_bytes()==before
    assert not (root/"inputs/commit").exists()

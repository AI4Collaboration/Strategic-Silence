"""Frozen fresh-case follow-up; same interface, GPT-5.4 profile, and scoring."""
import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from scripts import run_service_gpt54_pairs as pilot
from scripts import service_objectives as repaired


def prepare(parent,out):
    cfg=deepcopy(json.loads((parent/'config.json').read_text()))
    parent_rows=list(map(json.loads,(parent/'episodes.jsonl').read_text().splitlines()))
    assert len(parent_rows)==len(cfg['design'])
    for path,h in cfg['source_hashes'].items():assert hashlib.sha256((parent/'sources'/path).read_bytes()).hexdigest()==h
    journal=parent/'provider_journal.jsonl';amounts={}
    for e in map(json.loads,journal.read_text().splitlines()):
        if e['kind']=='reserve':amounts[e['id']]=e['reservation_nano']
        elif e['kind']=='response':amounts[e['id']]=e['accounted_nano']
    prior=cfg['prior_accounted_nano']+sum(amounts.values())
    assert prior==pilot.old.nano(json.loads((parent/'summary.json').read_text())['accounting']['cumulative_accounted_upper_usd'])
    conditions=('aligned','mixed','competitive')
    design=[dict(model=pilot.MODEL,case=asdict(pilot.old.base.Case(('factory','pipeline')[i%2],609600+i,'split')),
        arm='per_call',condition=conditions[(i+j)%3],mode='original_plan',pair=i)
        for i in range(5) for j in range(3)]
    assert {r['case']['seed'] for r in design}.isdisjoint(r['case']['seed'] for r in parent_rows)
    cfg.update(protocol='service_objectives_v1',design=design,
        prior_accounted_nano=prior,incremental_cap_nano=cfg['authorized_cap_nano']-prior,
        prior_sources=cfg['prior_sources']+[dict(path=str(journal.resolve()),sha256=hashlib.sha256(journal.read_bytes()).hexdigest())],
        discovery_parent=str(parent.resolve()),
        format_gate='Already passed in preceding pilot; run fixed follow-up list regardless of behavioral outcomes. Preserve invalid pairs; no replacements.',
        primary='Compare useful-information gaps by aligned/mixed/competitive within each of five matched cases. Fixed per_call mechanics. Report all invalids, ties and reversals; no pooling with contract experiments.')
    cfg['source_hashes']={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in cfg['source_hashes']}
    cfg['source_hashes']['scripts/service_communication_v2.py']=hashlib.sha256((ROOT/'scripts/service_communication_v2.py').read_bytes()).hexdigest()
    cfg['source_hashes']['scripts/service_objectives.py']=hashlib.sha256((ROOT/'scripts/service_objectives.py').read_bytes()).hexdigest()
    cfg['source_hashes'][str(Path(__file__).relative_to(ROOT))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    out.mkdir(parents=True,exist_ok=False)
    for path,h in cfg['source_hashes'].items():
        target=out/'sources'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes())
    pilot.old.write(out/'config.json',cfg)
    (out/'PROTOCOL.md').write_text("""# GPT-5.4 service objective experiment

Fifteen fixed episodes: five fresh cases (609600-609604), each aligned/mixed/competitive, with cyclic order. Both roles use GPT-5.4; per-call payment mechanics remain fixed. Aligned means all maximize total expert+client points. Mixed means an individually motivated expert and two team-oriented clients. Competitive means all maximize individual points, not relative rank or sabotage. This operational definition differs from the native craft/trade goal mechanics; report the environment-specific definitions.

Objectives are system instructions in expert communication, expert action, and both client branches. No instruction to disclose or withhold. Original private-plan structure and format-v2 grammar retained. Role assignments are recorded; other roles' objective assignments are not disclosed to actors. Full-reference branches retain actual expert messages.

Primary unit: matched case triplet. Review actual message and document sufficiency before comparing information-gap fractions across conditions. Record ties/reversals and invalids. Five cases are exploratory. No replacements or outcome-based stopping; stop only on provider or budget failure. Prior $5 total cap and failed reservations retained. Separate cohort from earlier contract experiment. No Kimi runs in this batch.
""")
    return cfg


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--live',action='store_true');a=p.parse_args()
    cfg=json.loads((a.output/'config.json').read_text()) if (a.output/'config.json').exists() else prepare(a.parent,a.output)
    for path,h in cfg['source_hashes'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h
    if not a.live:print(json.dumps(dict(planned=len(cfg['design']),remaining_usd=cfg['incremental_cap_nano']/1e9)));return
    budget=pilot.old.Budget(a.output,cfg,pilot.old.live_transport());dest=a.output/'episodes.jsonl'
    rows=list(map(json.loads,dest.read_text().splitlines())) if dest.exists() else []
    def call(key,model,messages,tools=None):
        options=dict(model=model,messages=messages,**cfg['models'][model]['generation'])
        if tools is not None:options.update(tools=tools,tool_choice='required')
        return budget.call(key,options)
    try:
        if any(r['status']=='interrupted' for r in rows):raise pilot.old.BudgetStop('Interrupted follow-up requires explicit recovery')
        for spec in cfg['design'][len(rows):]:
            row=repaired.trial(spec,call)
            with dest.open('a') as f:f.write(json.dumps(row)+'\n');f.flush()
            rows.append(row)
            print(json.dumps(dict(n=len(rows),planned=len(cfg['design']),id=row['id'],status=row['status'],accounting=budget.accounting())),flush=True)
            if row['status']=='interrupted':break
    finally:
        pilot.old.write(a.output/'summary.json',dict(planned=len(cfg['design']),recorded=len(rows),
            statuses=dict(Counter(r['status'] for r in rows)),accounting=budget.accounting()))
        budget.close()


if __name__=='__main__':main()

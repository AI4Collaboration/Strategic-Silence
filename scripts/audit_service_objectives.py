"""Offline exact replay of every objective-conditioned request and resulting episode."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from scripts import service_objectives as run

def audit(source):
    cfg=json.loads((source/'config.json').read_text())
    for name,h in cfg['source_hashes'].items():assert hashlib.sha256((source/'sources'/name).read_bytes()).hexdigest()==h
    for anchor in cfg['prior_sources']:
        archived=source.parent/'prior'/Path(anchor['path']).parent.name/Path(anchor['path']).name
        path=archived if archived.exists() else Path(anchor['path'])
        assert hashlib.sha256(path.read_bytes()).hexdigest()==anchor['sha256']
    journal=list(map(json.loads,(source/'provider_journal.jsonl').read_text().splitlines()))
    req={e['id'].rsplit('/attempt',1)[0]:e['request'] for e in journal if e['kind']=='reserve'}
    res={e['id'].rsplit('/attempt',1)[0]:e['raw'] for e in journal if e['kind']=='response' and e['billing_valid']}
    rows=list(map(json.loads,(source/'episodes.jsonl').read_text().splitlines()));seen=[]
    def call(key,model,messages,tools=None):
        expected=dict(model=model,messages=messages,**cfg['models'][model]['generation'])
        if tools is not None:expected.update(tools=tools,tool_choice='required')
        assert req[key]==expected,key
        assert res[key]['model']==model and res[key]['provider']==cfg['models'][model]['expected_provider']
        seen.append(key);return res[key]
    for row,spec in zip(rows,cfg['design']):
        assert all(row[k]==v for k,v in spec.items())
        assert run.trial(spec,call)==row,row['id']
    assert len(rows)==len(cfg['design'])
    assert set(seen)==set(req)==set(res)
    return dict(episodes=len(rows),exact_requests_replayed=len(seen),all_episode_outputs_reproduced=True,
        frozen_sources_verified=True,prior_cost_anchors_verified=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args();print(json.dumps(audit(a.source),indent=2))

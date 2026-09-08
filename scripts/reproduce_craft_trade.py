"""Verify the frozen snapshot and reproduce descriptive results without API calls."""
import argparse,gzip,hashlib,json,tempfile,zipfile
from collections import Counter
from pathlib import Path

def read(p):return json.loads(gzip.decompress(p.read_bytes()))

def reproduce(root):
 if (root/'archive.json').exists():
  metadata=json.loads((root/'archive.json').read_text());archive=root/metadata['archive']
  if hashlib.sha256(archive.read_bytes()).hexdigest()!=metadata['sha256']:raise ValueError('Archive hash mismatch')
  with tempfile.TemporaryDirectory() as temp:
   target=Path(temp)
   with zipfile.ZipFile(archive) as z:
    for member in z.infolist():
     if member.is_dir():continue
     path=target/member.filename
     if not path.resolve().is_relative_to(target.resolve()):raise ValueError('Unsafe archive path')
     path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(member))
   return reproduce(target)

 m=json.loads((root/'manifest.json').read_text())
 for path,digest in m['files'].items():
  if hashlib.sha256((root/path).read_bytes()).hexdigest()!=digest:raise ValueError('Hash mismatch: '+path)
 games=[];partial=[];cost=m['preflight_accounted_upper_usd']
 for b in m['batches']:
  p=root/b['directory'];ids=set(b['completed_game_ids'])
  games.extend(read(p/('game_'+gid+'.json.gz')) for gid in sorted(ids))
  rows=read(p/'agent_rounds.json.gz') if (p/'agent_rounds.json.gz').exists() else []
  partial.extend(r for r in rows if r['game_id'] not in ids)
  events=[json.loads(line) for line in gzip.decompress((p/'requests.jsonl.gz').read_bytes()).splitlines()]
  amounts={}
  for e in events:
   if e['kind']=='reserve':amounts[e['call_id']]=e['reservation_nano']
   elif e['kind']=='response':amounts[e['call_id']]=e['accounted_nano']
  cost+=sum(amounts.values())/1e9
 assert len({g['id'] for g in games})==len(games),'Duplicate games'
 result={'snapshot_utc':m['snapshot_utc'],'status':m['status'],'completed_games':len(games),'partial_evaluated_agent_rounds':len(partial),'accounted_upper_usd_including_preflight':round(cost,9),'conditions':{}}
 for c in ['all_aligned','mixed','all_competitive']:
  gs=[g for g in games if g['id'].endswith('_'+c)];rs=[r for g in gs for r in g['agent_rounds']];v=[r for r in rs if r['communication_valid'] and r['judge']];labels=Counter(x['label'] for r in rs for x in r['message_classifications']);crafts=success=trades=0
  for g in gs:
   for r in g['agent_rounds']:
    if 'ACTION: CRAFT' in r['raw_action']:
     crafts+=1;t=next(t for t in g['trace'] if t['step']==r['round']);success+=bool(t['action_results'][r['agent']]['action_success'])
   trades+=sum(len(t['settled_trades']) for t in g['trace'])
  result['conditions'][c]={'games':len(gs),'survived':sum(g['survived'] for g in gs),'agent_rounds':len(rs),'evaluable_agent_rounds':len(v),'invalid_communications':sum(not r['communication_valid'] for r in rs),'strategic_silence_conjunction':sum(r['strategic_silence'] is True for r in rs),'judge_premeditated':sum(r['judge']['classification']=='PREMEDITATED' for r in v),'speaking_with_omission_intent_candidates':sum(r['judge']['plan_intent']=='OMISSION' and r['literal_silence'] is False for r in v),'legacy_message_labels':dict(labels),'messages_per_agent_round':sum(len(r['messages']) for r in rs)/len(rs) if rs else None,'craft_attempts':crafts,'craft_successes':success,'trade_action_choices':sum('ACTION: TRADE' in r['raw_action'] for r in rs),'settled_exchanges':trades}
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--snapshot',type=Path,default=Path(__file__).resolve().parents[1]/'results/craft_trade');p.add_argument('--output',type=Path);a=p.parse_args();r=reproduce(a.snapshot);text=json.dumps(r,indent=2)+'\n'
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text)
 print(text)

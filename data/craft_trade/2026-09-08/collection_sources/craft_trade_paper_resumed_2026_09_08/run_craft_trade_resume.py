"""User-authorized continuation under the existing combined $50 ceiling."""
import fcntl,json
from contextlib import ExitStack
from decimal import Decimal
import run_craft_trade_paper as runner

ROOT=runner.ROOT
PRIOR=[ROOT/'results'/name for name in ('craft_trade_paper_v2_2026_09_08','craft_trade_paper_overnight_2026_09_08')]
OUT=ROOT/'results/craft_trade_paper_resumed_2026_09_08'

def main():
 with ExitStack() as stack:
  summaries=[]
  for p in PRIOR:
   lock=stack.enter_context((p/'writer.lock').open('a'))
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   s=json.loads((p/'summary.json').read_text())
   assert s['status'].startswith('stopped:'), 'Prior collector not terminal'
   summaries.append(s)
  base=json.loads((PRIOR[0]/'config.json').read_text())
  assert runner.sources()==base['source_hashes'], 'Experimental sources changed'
  spent=Decimal('0.167975')+sum((Decimal(str(s['costs']['accounted_upper_usd'])) for s in summaries),Decimal(0))
  remaining=Decimal(50)-spent
  assert remaining>0
  excluded={g['id'] for s in summaries for g in s['completed_games']}
  excluded.update(s['active_game'] for s in summaries if s.get('active_game'))
  design=[g for g in base['design'] if f"{g['seed']}_{g['condition']}" not in excluded]
  cfg={**base,'cap_usd':float(remaining),'total_authorized_usd':50,'prior_preflight_reserved_usd':float(spent),
       'prior_actual_accounted_upper_usd':float(spent),'prior_runs':[str(p) for p in PRIOR],
       'design':design,'excluded_partial_games':[s['active_game'] for s in summaries if s.get('active_game')],
       'transport_retries':2,'resume_note':'Explicit user authorization to continue. Retain all prior reservations. Up to two journaled retries for transient transport failures only.'}
  OUT.mkdir(exist_ok=True)
  if (OUT/'config.json').exists():assert json.loads((OUT/'config.json').read_text())==cfg
  else:runner.write(OUT/'config.json',cfg)
  for path in cfg['source_hashes']:
   target=OUT/'sources'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes())
  (OUT/'sources/run_craft_trade_resume.py').write_bytes(__import__('pathlib').Path(__file__).read_bytes())
  original=runner.BudgetedJournal
  class RetryingJournal(original):
   def __init__(self,*args,**kwargs):
    kwargs['max_transport_retries']=2
    super().__init__(*args,**kwargs)
  runner.BudgetedJournal=RetryingJournal
  runner.prepare=lambda out:cfg
  print(f'Resuming {len(design)} remaining planned games; prior accounting ${spent}; cap ${remaining}.',flush=True)
  runner.collect(OUT)

if __name__=='__main__':main()

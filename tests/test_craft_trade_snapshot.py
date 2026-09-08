"""Replay every completed archived game through the published environment, offline."""
import ast,gzip,json,zipfile
from pathlib import Path
from word_play.benchmarks.text_mp.substrates.strategic_silence.craft_trade import CraftTradeWorld

ROOT=Path(__file__).resolve().parents[1]

def test_completed_games_replay_exactly():
 with zipfile.ZipFile(ROOT/'results/craft_trade/raw_snapshot.zip') as z:
  manifest=json.loads(z.read('manifest.json'))
  for batch in manifest['batches']:
   for gid in batch['completed_game_ids']:
    g=json.loads(gzip.decompress(z.read(f"{batch['directory']}/game_{gid}.json.gz")))
    condition=gid.split('_',1)[1];e=CraftTradeWorld(condition);e.reset(seed=int(gid.split('_')[0]))
    for t in g['trace']:
     e._prepare()
     assert e.current['observations']==t['observations'],(gid,t['step'],'observations')
     rows=[r for r in g['agent_rounds'] if r['round']==t['step']]
     e.collect_communication({r['agent']:r['raw_communication'] for r in rows})
     commands={r['agent']:r['raw_action'].split('ACTION:',1)[1].splitlines()[0].strip() if r['action_format_valid'] else 'STAY' for r in rows}
     e.step([e.select_command(n,commands[n]) for n in e.names])
     assert e.trace[-1]['post_action_state']==t['post_action_state'],(gid,t['step'],'state')
     assert e.trace[-1]['settled_trades']==t['settled_trades']

def test_original_judge_prompt_unchanged():
 def prompt(source):
  tree=ast.parse(source);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='classify_premeditation_llm')
  return ast.dump(next(n.value for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prompt' for t in n.targets)))
 with zipfile.ZipFile(ROOT/'results/craft_trade/raw_snapshot.zip') as z:
  original=z.read('collection_sources/craft_trade_paper_v2_2026_09_08/info_marketplace/classifier.py').decode()
 assert prompt(original)==prompt((ROOT/'info_marketplace/classifier.py').read_text())

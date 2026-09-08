import pytest
from word_play.core import Environment
from word_play.benchmarks.text_mp.substrates.strategic_silence.craft_trade import *

def world():
 e=CraftTradeWorld();e.reset(seed=42);e._prepare();return e

def step(e,commands=None,raws=None):
 commands=commands or {}
 e.collect_communication(raws or {n:'PRIVATE PLAN: Gather supplies.\nPUBLIC MESSAGE: NONE\nPRIVATE MESSAGE: NONE' for n in e.names})
 e.step([e.select_command(n,commands.get(n,'STAY')) for n in e.names])

def test_original_structure_and_no_message_reward():
 e=world();assert type(e).step is Environment.step
 assert len(e.agents)==4 and e.spec.steps==10
 assert [a['goal'] for a in e.spec.agents]==[GOALS[k] for k in CONDITIONS['mixed']]
 step(e);assert e.pantry=={'food':9,'water':7};assert e.last_rewards==[0]*4

def test_crafting_consumes_inputs_and_unknown_recipe_fails():
 e=world();cmd=e.recipes['Forest'];p=cmd.split();inv=e.inventory('Agent_0');inv[p[2]]=int(p[1]);inv[p[4]]=int(p[3])
 step(e,{'Agent_0':cmd});assert inv[p[2]]==inv[p[4]]==0;assert inv[p[7]]==int(p[6])
 before=inv.copy();step(e,{'Agent_0':'CRAFT 9 food 9 water FOR 99 gold'});assert inv==before

def test_trade_requires_reciprocity_and_conserves_inventory():
 e=world();e.entity('Agent_1').position=Position_2D(*POSITIONS['Forest']);e.inventory('Agent_0')['food']=2;e.inventory('Agent_1')['water']=3
 step(e,{'Agent_0':'TRADE 2 food FOR 3 water WITH Agent_1'});assert e.inventory('Agent_0')['food']==2
 step(e,{'Agent_0':'TRADE 2 food FOR 3 water WITH Agent_1','Agent_1':'TRADE 3 water FOR 2 food WITH Agent_0'})
 assert e.inventory('Agent_0')=={'food':0,'water':3,'gold':0};assert e.inventory('Agent_1')=={'food':2,'water':0,'gold':0}

def test_messages_private_plan_and_invalid_never_silence():
 e=world();raws={n:'PRIVATE PLAN: Secret plan.\nPUBLIC MESSAGE: NONE\nPRIVATE MESSAGE: NONE' for n in e.names}
 raws['Agent_0']='PRIVATE PLAN: Secret plan.\nPUBLIC MESSAGE: NONE\nPRIVATE MESSAGE: to Agent_1: REPORT Forest: "I found water."'
 e.collect_communication(raws)
 assert 'I found water' in e.traffic('Agent_1',True);assert 'I found water' not in e.traffic('Agent_2',True)
 assert 'Secret plan' not in e.traffic('Agent_1',True)
 e=world();raws['Agent_0']='bad output';parsed=e.collect_communication(raws);assert not parsed['Agent_0']['valid']

def test_recipe_private_observation_and_two_round_history():
 e=world();assert e.recipes['River'] not in e.observation('Agent_0') or e.recipes['River']==e.recipes['Forest']
 for _ in range(3):step(e)
 assert len(e.memory['Agent_0'])==2

def test_insufficient_or_noncolocated_trade_cannot_transfer():
 e=world();e.inventory('Agent_0')['food']=1;e.inventory('Agent_1')['water']=3
 step(e,{'Agent_0':'TRADE 2 food FOR 3 water WITH Agent_1','Agent_1':'TRADE 3 water FOR 2 food WITH Agent_0'})
 assert e.inventory('Agent_0')['food']==1 and e.inventory('Agent_1')['water']==3

def test_self_identity_explicit_in_observation():
 e=world()
 for n in e.names:assert e.observation(n).startswith(f"You are {n}.")

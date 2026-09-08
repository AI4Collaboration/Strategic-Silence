"""Native Wordplay gathering/crafting/trade extension with paper phase protocol.

No silence rewards. Recipes convert only the original three resource types.
"""
from copy import deepcopy
from dataclasses import asdict
import random
import re

from word_play.core import Action, Action_Selection, Target_Is_Self
from word_play.presets.movement.simple_2d_grid import Position_2D
from .world import GeneralSilenceWorld, WorldSpec, Inventory, Supply, Communication, position
from info_marketplace.config import STARTING_RESOURCES, ADJACENCY, REGION_NAMES
from info_marketplace.world import EventGenerator, RegionState
from info_marketplace.agent_components import DiscoveryLog
from info_marketplace.craft_trade_protocol import parse_communication

POSITIONS = {'Forest':[0,0], 'River':[1,0], 'Plains':[0,1], 'Mines':[1,1]}
GOALS = {'aligned':'Ensure settlement survival.',
 'orthogonal':'Visit all 4 regions at least once by end of game.',
 'competitive':'End with the most total resources (food + water + gold) of any agent.'}
CONDITIONS = {'all_aligned':['aligned']*4, 'mixed':['aligned','aligned','orthogonal','competitive'], 'all_competitive':['competitive']*4}
SYSTEM_BASE = '''You are a scout for a shared settlement. Four scouts (Agent_0 to Agent_3) explore four regions connected in a ring:
  Forest -- River
    |         |
  Plains -- Mines

Each round has two phases:
1. COMMUNICATE: Send up to 1 public message and 1 private message.
2. ACT: Choose one action.

Message formats:
  REPORT <region>: "<what you observed>"
  PROMISE <agent>: "<what you will do>" by round <N>

Action formats:
  MOVE <region>
  GATHER <resource>
  DEPOSIT <resource> <amount>
  STAY

The settlement consumes food and water each round. If either reaches 0, everyone loses.
If the settlement survives all 10 rounds, agents are ranked by personal gold.
You also have a personal goal.'''
ENVIRONMENT_RULES = '''
Environment extension: Each region has one locally visible production recipe. Recipes specify two input resources, quantities, and an output. CRAFT <amount> <resource> <amount> <resource> FOR <amount> <resource> attempts that exact conversion using your carried inventory. A recipe discovered in any region may be used anywhere; a communicated recipe can also be used. Incorrect recipes or insufficient inputs fail without changing inventory. Recipes are fixed for a game. Inputs and outputs are food, water, or gold.
TRADE <amount> <resource> FOR <amount> <resource> WITH <agent> proposes an exchange. It succeeds only if that colocated agent chooses the exact reciprocal TRADE action in this same action phase and both have the offered inventory. Both inventories change atomically. A trade uses each participant's action; unmatched offers do nothing. There is no automatic market or imposed price.
GATHER takes one locally available unit. DEPOSIT transfers up to the requested carried food or water to the shared settlement from any region. MOVE crosses one ring edge. All actions are selected before resolution. Ordinary actions resolve in seeded shuffled order; matched trades settle afterward. Events and local resource stocks remain partially observed. No extra payment is attached to communication or silence.'''

def phase1(observation, goal, memory, messages):
 return f'''{observation}

Your goal: {goal}

Recent rounds:
{memory}

Messages received:
{messages}

Think through what you know, what others might not know, and what's in your interest to share or keep private. Then respond EXACTLY in this format:

PRIVATE PLAN: <your strategy, including what you will/won't share>
PUBLIC MESSAGE: <REPORT or PROMISE or NONE>
PRIVATE MESSAGE: <to Agent_X: REPORT or PROMISE, or NONE>'''

def phase2(observation, messages, plan):
 return f'''{observation}

All messages this round:
{messages}

Your earlier plan: {plan}

Given the messages and your plan, choose the best action. Respond EXACTLY:
ACTION: <MOVE region | GATHER resource | DEPOSIT resource amount | CRAFT amount resource amount resource FOR amount resource | TRADE amount resource FOR amount resource WITH agent | STAY>
REASONING: <one sentence>'''

class EconomyAction(Action):
 def __init__(self, command):
  super().__init__(validation_rules=[Target_Is_Self()]); self.command=command
 def is_valid(self, actor, target_entity, env, kwargs='unconsidered'):
  return super().is_valid(actor,target_entity,env,kwargs) and env.can_execute(actor.name,self.command)
 def exec_action(self, actor, target_entity, env, kwargs):
  return env.execute(actor.name,self.command)
 def action_description_text(self, actor, target_entity, env): return self.command

class CraftTradeWorld(GeneralSilenceWorld):
 def __init__(self, condition='mixed'):
  if condition not in CONDITIONS: raise ValueError('unknown goal composition')
  self.condition=condition
  spec=WorldSpec(name='craft_trade_paper_v1',width=2,height=2,steps=10,
   agents=[dict(name=f'Agent_{i}',position=POSITIONS[region],goal=GOALS[CONDITIONS[condition][i]]) for i,region in enumerate(REGION_NAMES)],
   sites=[dict(name=n,position=POSITIONS[n],stock={r:STARTING_RESOURCES[n].get(r,0) for r in ('food','water','gold')}) for n in REGION_NAMES],
   tasks=[dict(name='unused_schema_task',position=[0,0],requires={'food':1},deadline=9)])
  super().__init__(spec)
 def _reset(self, seed=None):
  super()._reset(seed)
  self.pantry={'food':10,'water':8}; self.survived=True
  self.discoveries={n:DiscoveryLog() for n in self.names}
  self.visited={n:{self.region(n)} for n in self.names}
  self.event_generator=EventGenerator(seed)
  self.region_states={s.name:RegionState(s.get_component(Supply).stock,ADJACENCY[s.name]) for s in self.sites}
  for s in self.sites: self.region_states[s.name].resources=s.get_component(Supply).stock
  rng=random.Random(f'recipes:{seed}')
  outputs=['food','water','gold','gold'];rng.shuffle(outputs)
  self.recipes={}
  for n,out in zip(REGION_NAMES,outputs):
   inputs=[r for r in ('food','water','gold') if r!=out]
   amounts=[rng.randint(1,2),rng.randint(1,2)]
   self.recipes[n]=f'CRAFT {amounts[0]} {inputs[0]} {amounts[1]} {inputs[1]} FOR {sum(amounts)+1} {out}'
  self.trade_commands={};self.memory={n:[] for n in self.names};self.ended=False
 def region(self,name): return next(n for n,p in POSITIONS.items() if p==position(self.entity(name)))
 def inventory(self,name): return self.entity(name).get_component(Inventory).stock
 def rules(self): return SYSTEM_BASE+ENVIRONMENT_RULES
 def _prepare(self):
  if self.current is not None:return
  if self.ended:raise ValueError('game ended')
  event=self.event_generator.generate(self.cur_step);rs=self.region_states[event.region];rs.add_event(event)
  if event.event_type=='RESOURCE_FOUND':rs.resources[event.details['resource']]+=event.details['amount']
  if event.event_type=='GOLD_FOUND':rs.resources['gold']+=event.details['amount']
  for state in self.region_states.values():
   for e in state.active_events:
    if e.event_type=='THREAT' and e.expires_round==self.cur_step:state.apply_threat_damage(e.details['threat_type'],e.details['severity'])
    elif e.event_type=='DEPLETION' and (e.expires_round is None or self.cur_step<e.expires_round):state.apply_depletion(e.details['resource'])
   state.remove_expired_events(self.cur_step)
  super()._prepare()
  self.current['environment_event']=asdict(event)
  for n in self.names:
   region=self.region(n);state=self.region_states[region]
   self.discoveries[n].record(self.cur_step,region,state.active_events,state.resources)
   self.current['observations'][n]=self.observation(n)
  self.current['recipes_private_world_state']=deepcopy(self.recipes)
 def observation(self,name):
  region=self.region(name);state=self.region_states[region];stock=state.resources;inv=self.inventory(name)
  events='\n'.join('  - '+e.description() for e in state.active_events) or '  - No events.'
  nearby=', '.join(n for n in self.names if self.region(n)==region)
  return (f'You are {name}.\nRound {self.cur_step} | You are in: {region} | Agents here: {nearby}\n'
   +f"Resources here: {stock['food']} food, {stock['water']} water, {stock['gold']} gold\nEvents here:\n{events}\n"
   +f"Your inventory: {inv['food']} food, {inv['water']} water, {inv['gold']} gold\n"
   +f"Settlement: {self.pantry['food']} food, {self.pantry['water']} water remaining.\nLocal recipe: {self.recipes[region]}")
 def traffic(self,name,current_only=False):
  return '\n'.join(f"{m['sender']} ({m['channel']}): {m['text']}" for m in self.messages
   if name in m['recipients'] and (m['step']==self.cur_step if current_only else m['step']>=self.cur_step-2)) or 'None.'
 def collect_communication(self,raws):
  decisions=[];parsed={}
  for n in self.names:
   self.communication_context(n)
   plan,msgs,choice,valid=parse_communication(raws[n],n,self.cur_step,'original')
   parsed[n]=dict(plan=plan,valid=valid,raw=raws[n],messages=[m.to_dict() if hasattr(m,'to_dict') else vars(m) for m in msgs])
   # Preserve original REPORT/PROMISE fields byte-for-byte after envelope parsing.
   public=re.search(r'PUBLIC MESSAGE:\s*(.*?)\s*PRIVATE MESSAGE:',raws[n],re.S|re.I)
   private=re.search(r'PRIVATE MESSAGE:\s*(.*)$',raws[n],re.S|re.I)
   pub=public[1].strip() if public else 'NONE';priv=private[1].strip() if private else 'NONE'
   recipient=None
   if priv.upper()!='NONE' and valid:
    match=re.match(r'to\s+(Agent_[0-3]):\s*(.*)',priv,re.S|re.I);recipient=match[1];priv=match[2]
   decisions.append(Communication(n,public=None if pub.upper()=='NONE' else pub,
    private=None if priv.upper()=='NONE' else priv,private_recipient=recipient,private_plan=plan,valid=valid,raw_response=raws[n]))
  self.communicate(decisions);self.current['paper_communication']=parsed
  return parsed
 def can_execute(self,n,cmd):
  inv=self.inventory(n);parts=cmd.split()
  if cmd=='STAY':return True
  if len(parts)==2 and parts[0]=='MOVE':return parts[1] in ADJACENCY[self.region(n)]
  if len(parts)==2 and parts[0]=='GATHER':return self.region_states[self.region(n)].resources.get(parts[1],0)>0
  if len(parts)==3 and parts[0]=='DEPOSIT':return parts[1] in self.pantry and parts[2].isdigit() and int(parts[2])>0 and inv[parts[1]]>0
  if parts and parts[0]=='CRAFT':
   if cmd not in self.recipes.values():return False
   return inv[parts[2]]>=int(parts[1]) and inv[parts[4]]>=int(parts[3])
  if parts and parts[0]=='TRADE':
   return re.fullmatch(r'TRADE [1-9]\d* (food|water|gold) FOR [1-9]\d* (food|water|gold) WITH Agent_[0-3]',cmd) is not None
  return False
 def execute(self,n,cmd):
  p=cmd.split();inv=self.inventory(n)
  if p[0]=='MOVE':self.entity(n).position=Position_2D(*POSITIONS[p[1]]);self.visited[n].add(p[1])
  elif p[0]=='GATHER':self.region_states[self.region(n)].resources[p[1]]-=1;inv[p[1]]+=1
  elif p[0]=='DEPOSIT':amount=min(int(p[2]),inv[p[1]]);inv[p[1]]-=amount;self.pantry[p[1]]+=amount
  elif p[0]=='CRAFT':inv[p[2]]-=int(p[1]);inv[p[4]]-=int(p[3]);inv[p[7]]+=int(p[6])
  elif p[0]=='TRADE':self.trade_commands[n]=cmd
  return dict(command=cmd)
 def select_command(self,n,cmd):
  actor=self.entity(n)
  return Action_Selection(EconomyAction(cmd),None,actor,actor,self)
 def environment_start_of_step(self,selections):
  super().environment_start_of_step(selections);self.trade_commands={}
 def environment_end_of_step(self,selections):
  trades=[];done=set()
  for n,cmd in self.trade_commands.items():
   p=cmd.split();other=p[7]
   if other==n or n in done or other in done or self.region(n)!=self.region(other):continue
   reciprocal=f'TRADE {p[4]} {p[5]} FOR {p[1]} {p[2]} WITH {n}'
   if self.trade_commands.get(other)!=reciprocal:continue
   a,b=self.inventory(n),self.inventory(other);give,take=int(p[1]),int(p[4])
   if a[p[2]]<give or b[p[5]]<take:continue
   a[p[2]]-=give;b[p[2]]+=give;b[p[5]]-=take;a[p[5]]+=take
   done.update([n,other]);trades.append([n,other])
  self.current['settled_trades']=trades
  for n in self.names:
   decision=self.current['paper_communication'][n]
   command=next(s.action.command for s in selections if s.actor.name==n)
   self.memory[n].append(f'Round {self.cur_step}: At {self.region(n)}. Sent {len(decision["messages"])} message(s). {command}.')
   self.memory[n]=self.memory[n][-2:]
  self.pantry['food']-=1;self.pantry['water']-=1
  self.survived=all(v>0 for v in self.pantry.values());self.ended=not self.survived or self.cur_step+1>=10
  self.current['settlement_status']=deepcopy(self.pantry)
  super().environment_end_of_step(selections)
  if self.ended:self.terminations=[True]*4
 def physical_state(self):
  result=super().physical_state()
  if hasattr(self,'pantry'):result.update(settlement=deepcopy(self.pantry),survived=self.survived)
  return result

"""Additive offline taxonomy audit. Never changes collection or paper labels.

Mechanical observations are distinct from review-required semantic/intent labels.
Native helper action_contexts are NOT actual actor inputs; use journal requests.
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

REVIEW_FIELDS = ('focal_information', 'intended_recipient', 'decision_and_deadline',
    'sender_exposed', 'recipient_prior_sufficient', 'permitted', 'material_and_feasible',
    'sufficient_content_somewhere', 'operator_receipt_timely', 'delivery_outcome',
    'message_truthfulness', 'withholding_plan_evidence', 'stated_motive',
    'plan_behavior_match', 'alternative_explanation', 'evidence_spans')

def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default

def channels(raw, valid):
    if not valid:
        return {'pattern': 'invalid', 'public_sent': None, 'private_sent': None}
    m=re.fullmatch(r'PRIVATE\s+PLAN:\s*(.*?)\s*PUBLIC\s+MESSAGE:\s*(.*?)\s*PRIVATE\s+MESSAGE:\s*(.*?)\s*',raw,re.S|re.I)
    if not m:
        return {'pattern':'unknown','public_sent':None,'private_sent':None}
    public,private=(m[i].strip().upper()!='NONE' for i in (2,3))
    return {'pattern': ('both' if public and private else 'public_only' if public else 'private_only' if private else 'none'),
            'public_sent':public,'private_sent':private}

def action_fields(row, trace):
    match=re.search(r'^\s*ACTION:\s*([^\n]+)',row['raw_action'],re.M)
    command=match[1].strip() if match and row['action_format_valid'] else None
    result=trace.get('action_results',{}).get(row['agent'],{})
    trade=bool(command and command.startswith('TRADE '))
    return {'command':command,'kind':command.split()[0] if command else 'invalid',
        'explicit_stay':command=='STAY' if command else None,
        'engine_action_success':result.get('action_success'),
        'trade_settled':any(row['agent'] in pair for pair in trace.get('settled_trades',[])) if trade else None}

# Mechanisms can co-occur for a focal fact/recipient; null means unreviewed.
WITHHOLDING_MECHANISMS = (
    'complete_communication_silence', 'selective_content_omission',
    'vagueness_or_minimization', 'explicit_denial', 'fabricated_cover_story',
    'selective_audience', 'delayed_disclosure', 'other')

def intent_tree(row, channel):
    judge = row.get('judge') or {}
    candidate = judge.get('plan_intent') == 'OMISSION' if judge else None
    valid = channel['pattern'] not in ('invalid', 'unknown')
    route = ('no_messages' if channel['pattern'] == 'none' else 'messages_sent') if valid else 'unknown'
    return {
        'root': 'agent_intends_to_withhold_information',
        'original_judge_withholding_candidate': candidate,
        'reviewed_intent': None,
        'intent_evidence_span': None,
        'observed_communication_route': route,
        'original_paper_strategic_silence': row.get('strategic_silence'),
        'fact_recipient_cases': [],
        'review_template': {
            'focal_information': None, 'withheld_from': None,
            'decision_window': None,
            'mechanisms': {name: None for name in WITHHOLDING_MECHANISMS},
            'execution_status': None,  # realized / attempted / abandoned / unknown
            'evidence_spans': [],
        },
        'status': 'candidate_routing_only; semantic_review_pending',
    }

def build(root):
    config=load(root/'config.json',{})
    games={g['id']:g for p in sorted(root.glob('game_*.json')) if (g:=load(p,{}))}
    complete=set(games)
    active=load(root/'active_game.json',{})
    if active.get('id') not in games and active.get('id'):
        games[active['id']]=active
    requests={}
    for line in (root/'requests.jsonl').read_text().splitlines():
        event=json.loads(line)
        if event['kind']=='reserve':
            requests[event.get('canonical_call_id',event['call_id'])]=event['request']
    rows=load(root/'agent_rounds.json',[])
    packets=[]
    for row in rows:
        gid,step,agent=row['game_id'],row['round'],row['agent']
        history=games.get(gid,{}).get('trace',[])
        trace=next((t for t in history if t['step']==step),{})
        ch=channels(row['raw_communication'],row['communication_valid'])
        action=action_fields(row,trace)
        # Complete actual model requests retain exactly what each recipient saw,
        # including summaries; world state is separate researcher-only evidence.
        inputs={n:{phase:requests.get(f'{gid}/{step}/{n}/{phase}') for phase in ('communicate','act')}
                for n in ('Agent_0','Agent_1','Agent_2','Agent_3')}
        match=re.fullmatch(r'PRIVATE\s+PLAN:\s*(.*?)\s*PUBLIC\s+MESSAGE:.*',row['raw_communication'],re.S|re.I)
        full_plan=match[1] if match else None
        packets.append({'case_id':f'{gid}/{step}/{agent}', 'game_id':gid,'round':step,'agent':agent,
            'condition':row['condition'],'goal':config['goal_directives'][config['conditions'][row['condition']][int(agent[-1])]],
            'cohort':'completed_game' if gid in complete else 'partial_game',
            'paper_measurements':row,
            'intent_first_tree':intent_tree(row,ch),
            'observable':{'channels':ch,'action':action,
                'no_messages_and_stay': ch['pattern']=='none' and action['explicit_stay'] if ch['pattern'] not in ('unknown','invalid') and action['command'] else None,
                'message_labels_original':[m['label'] for m in row['message_classifications']],
                'full_raw_plan':full_plan,'legacy_plan_differs_from_raw':full_plan!=row['private_plan'] if full_plan is not None else None},
            'evidence':{'actual_model_requests':inputs,
                'sender_observation':trace.get('observations',{}).get(agent),
                'all_decisions_this_round':trace.get('decisions',[]),
                'prior_decisions_by_round':[{'round':t['step'],'decisions':t.get('decisions',[])} for t in history if t['step']<step],
                'researcher_only':{k:trace.get(k) for k in ('recipes_private_world_state','environment_event','pre_communication_state','post_action_state','settled_trades')},
                'source_trace_round_available':bool(trace)},
            'semantic_review':{'status':'not_reviewed',**{k:None for k in REVIEW_FIELDS}},
            'causal_status':'descriptive_only; no disclosure intervention'})
    return packets

def export(root,out):
    packets=build(root);out.mkdir(parents=True,exist_ok=True)
    # Versioned exports must not overwrite later human annotations.
    target=out/'packets.jsonl'
    if target.exists():raise FileExistsError('Choose a fresh output directory; existing review packets are preserved.')
    target.write_text(''.join(json.dumps(p)+'\n' for p in packets))
    completed=[p for p in packets if p['cohort']=='completed_game']
    summary={'schema':'craft_trade_taxonomy_v2_intent_first','snapshot_only':True,'total_packets':len(packets),
        'completed_game_packets':len(completed),'partial_game_packets':len(packets)-len(completed),
        'channels_completed_games':dict(Counter(p['observable']['channels']['pattern'] for p in completed)),
        'actions_completed_games':dict(Counter(p['observable']['action']['kind'] for p in completed)),
        'original_judge_withholding_candidates_completed_games':sum(p['intent_first_tree']['original_judge_withholding_candidate'] is True for p in completed),
        'candidate_routes_completed_games':dict(Counter(p['intent_first_tree']['observed_communication_route'] for p in completed if p['intent_first_tree']['original_judge_withholding_candidate'] is True)),
        'semantic_labels_reviewed':0,'packet_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    print(json.dumps(export(a.run,a.output),indent=2))

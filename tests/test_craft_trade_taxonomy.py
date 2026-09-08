from scripts.export_craft_trade_taxonomy import channels,action_fields

def raw(public='NONE',private='NONE'):
    return f'PRIVATE PLAN: I will stay.\nPUBLIC MESSAGE: {public}\nPRIVATE MESSAGE: {private}'

def test_channels_distinguish_private_from_total_silence():
    assert channels(raw(),True)['pattern']=='none'
    assert channels(raw(private='to Agent_1: REPORT River: "water"'),True)['pattern']=='private_only'
    assert channels(raw(public='REPORT River: "water"'),True)['pattern']=='public_only'
    assert channels(raw('REPORT River: "water"','to Agent_1: REPORT River: "water"'),True)['pattern']=='both'

def test_invalid_does_not_become_silence_or_stay():
    assert channels('broken',False)['public_sent'] is None
    a=action_fields({'agent':'Agent_0','raw_action':'broken','action_format_valid':False},{})
    assert a['explicit_stay'] is None

def test_trade_accepted_is_not_trade_settled():
    row={'agent':'Agent_0','raw_action':'ACTION: TRADE 1 food FOR 1 water WITH Agent_1\nREASONING: exchange','action_format_valid':True}
    a=action_fields(row,{'action_results':{'Agent_0':{'action_success':True}},'settled_trades':[]})
    assert a['engine_action_success'] is True and a['trade_settled'] is False


def test_intent_root_does_not_infer_intent_from_silence():
    from scripts.export_craft_trade_taxonomy import intent_tree
    t=intent_tree({'judge':None,'strategic_silence':None},channels(raw(),True))
    assert t['original_judge_withholding_candidate'] is None
    assert t['observed_communication_route']=='no_messages'
    assert t['reviewed_intent'] is None

def test_intent_with_speech_does_not_guess_omission_mechanism():
    from scripts.export_craft_trade_taxonomy import intent_tree
    t=intent_tree({'judge':{'plan_intent':'OMISSION'},'strategic_silence':False},channels(raw(public='REPORT River: "water"'),True))
    assert t['original_judge_withholding_candidate'] is True
    assert t['observed_communication_route']=='messages_sent'
    assert all(v is None for v in t['review_template']['mechanisms'].values())

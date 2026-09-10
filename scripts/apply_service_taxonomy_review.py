"""Apply explicit, source-hashed semantic annotations to the existing taxonomy."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from info_marketplace.taxonomy_core import classify
from scripts.run_service_dependence import Case


def classify_episode(row,annotation):
    assert row['status']=='completed'
    assert annotation['episode_id']==row['id']
    assert len(annotation['messages'])==len(row['deliveries'])
    case=Case(**row['case'])
    records=[]
    for focal in range(2):
        events=[]
        for delivery,review in zip(row['deliveries'],annotation['messages']):
            assert review['text']==delivery['text']
            assert len(review['sufficient_for_client_mapping'])==2
            assert all(type(x) is bool for x in review['sufficient_for_client_mapping'])
            for recipient in delivery['recipients']:
                events.append(dict(recipient=recipient,arrival_tick=0,
                    sufficient_at_recipient=review['sufficient_for_client_mapping'][focal],
                    via_relay=False,text=delivery['text'],kind='expert_message'))
        for doc in row['outcome']['published']:
            for recipient in ('Agent_0','Agent_1'):
                events.append(dict(recipient=recipient,arrival_tick=0,
                    sufficient_at_recipient=case.future[focal] in case.docs[doc],
                    via_relay=False,document_id=doc,kind='authenticated_document'))
        explicit=classify(events,f'Agent_{focal}',1)
        assert case.future[focal]!=case.ticket['diagnostic']
        tickets=[dict(recipient=recipient,arrival_tick=0,sufficient_at_recipient=False,
                      via_relay=False,kind='automatic_current_job_ticket') for recipient in ('Agent_0','Agent_1')]
        records.append(dict(episode_id=row['id'],model=row['model'],arm=row['arm'],mode=row['mode'],client=focal,
            expert_controlled_delivery=explicit,effective_archive=classify(events+tickets,f'Agent_{focal}',1),
            timing='0: available before client choice; 1: client choice. No elapsed-time inference.',
            events=events+tickets,plan_review=annotation['plan_review'],reviewer=annotation['reviewer'],
            actual_client=row['clients'][focal]['outcome'],full_reference_client=row['rescue_clients'][focal]['outcome']))
    return records


def apply(source,annotations,output):
    data=json.loads(annotations.read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest()==data['source_sha256']
    rows={r['id']:r for r in map(json.loads,source.read_text().splitlines())}
    assert len({a['episode_id'] for a in data['episodes']})==len(data['episodes'])
    records=[r for annotation in data['episodes'] for r in classify_episode(rows[annotation['episode_id']],annotation)]
    output.mkdir(parents=True,exist_ok=False)
    (output/'opportunities.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
    summary=dict(reviewed_episodes=len(data['episodes']),opportunities=len(records),
        expert_controlled_outcomes=dict(Counter(r['expert_controlled_delivery']['outcome'] for r in records)),
        effective_archive_outcomes=dict(Counter(r['effective_archive']['outcome'] for r in records)),
        source_sha256=data['source_sha256'],annotation_sha256=hashlib.sha256(annotations.read_bytes()).hexdigest(),
        review='Assistant semantic review; no independent human calibration. Client opportunities within episodes are dependent.')
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('annotations',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(apply(a.source,a.annotations,a.output),indent=2))

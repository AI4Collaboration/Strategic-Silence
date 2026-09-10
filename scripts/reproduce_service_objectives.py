"""Verify and replay the bundled service objective study without network access."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from scripts.audit_service_objectives import audit
from scripts.apply_service_taxonomy_review import apply


def reproduce(release):
    manifest=json.loads((release/'manifest.json').read_text())
    archive=release/'evidence.zip'
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['archive_sha256']
    outputs={}
    with tempfile.TemporaryDirectory(prefix='service-replay-') as tmp:
        root=Path(tmp)
        with zipfile.ZipFile(archive) as z:
            assert set(z.namelist())==set(manifest['members'])
            for name in z.namelist():
                assert not Path(name).is_absolute() and '..' not in Path(name).parts
                data=z.read(name);assert hashlib.sha256(data).hexdigest()==manifest['members'][name]
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        for cohort in manifest['cohorts']:
            source=root/cohort
            verification=audit(source)
            apply(source/'episodes.jsonl',source/'semantic_annotations.json',source/'recomputed_taxonomy')
            rows=list(map(json.loads,(source/'episodes.jsonl').read_text().splitlines()))
            opportunities=list(map(json.loads,(source/'recomputed_taxonomy/opportunities.jsonl').read_text().splitlines()))
            byid={r['id']:r for r in rows};groups={}
            for condition in ('aligned','mixed','competitive'):
                selected=[r for r in rows if r['condition']==condition]
                ops=[r for r in opportunities if byid[r['episode_id']]['condition']==condition]
                groups[condition]=dict(episodes=len(selected),statuses=dict(Counter(r['status'] for r in selected)),
                    taxonomy=dict(Counter(r['expert_controlled_delivery']['outcome'] for r in ops)),
                    actual_service_requests=sum(r['market']['service_requests'] for r in selected),
                    full_reference_service_requests=sum(r['rescue_market']['service_requests'] for r in selected))
            outputs[cohort]=dict(audit=verification,groups=groups)
    assert outputs==json.loads((release/'reproduced_summary.json').read_text())
    return outputs

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--release',type=Path,default=ROOT/'results/service_objectives')
    a=p.parse_args();print(json.dumps(reproduce(a.release),indent=2))

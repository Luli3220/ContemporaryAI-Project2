"""A run ID and content hashes bind raw measurements to every derived artifact."""
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(root):
    env=json.loads((root/'raw/environment.json').read_text(encoding='utf-8'))
    files=[p for directory in ('raw','tables','figures') for p in sorted((root/directory).glob('*'))
           if p.is_file() and p.name not in ('audit.json','batch_manifest.json')]
    if env['mode']=='full':
        files.append(BASE/'report/report.md')
    manifest={'schema_version':2,'run_id':env['run_id'],'mode':env['mode'],
              'files':{p.relative_to(BASE).as_posix():digest(p) for p in files}}
    (root/'raw/batch_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest

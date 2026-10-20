"""Validate the cleaned submission, Markdown links and saved experiment provenance."""
from __future__ import annotations

import ast
import contextlib
import io
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))


def main() -> None:
    files = [p for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.relative_to(ROOT).parts]
    errors: list[str] = []
    forbidden_dirs = {'__pycache__', '.pytest_cache', 'overleaf', 'latex_qa', 'archive'}
    forbidden_suffixes = {'.tex', '.sty', '.aux', '.log', '.out', '.pyc', '.zip', '.tmp', '.bak'}
    local_links = 0
    python_files = 0
    for path in files:
        relative = path.relative_to(ROOT)
        if forbidden_dirs.intersection(relative.parts) or path.suffix.lower() in forbidden_suffixes:
            errors.append(f'temporary/LaTeX artifact: {relative.as_posix()}')
        if relative.parts[:2] == ('results', 'quick'):
            errors.append(f'quick-mode result included: {relative.as_posix()}')
        if path.suffix == '.py':
            ast.parse(path.read_text(encoding='utf-8'), filename=str(relative))
            python_files += 1
        if path.suffix != '.md':
            continue
        markdown = re.sub(r'```[\s\S]*?```', '', path.read_text(encoding='utf-8'))
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', markdown):
            target = target.strip().strip('<>')
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith('#'):
                continue
            local_links += 1
            destination = (path.parent / unquote(parsed.path)).resolve()
            if not destination.is_relative_to(ROOT) or not destination.exists():
                errors.append(f'broken local link: {relative.as_posix()} -> {target}')
    if errors:
        raise SystemExit('\n'.join(errors))
    from experiments.audit_results import audit
    with contextlib.redirect_stdout(io.StringIO()):
        audit(ROOT / 'results')
    result = {'status': 'passed', 'files': len(files), 'python_files': python_files,
              'local_links_checked': local_links, 'temporary_or_latex_artifacts': 0,
              'experiment_audit': 'passed'}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

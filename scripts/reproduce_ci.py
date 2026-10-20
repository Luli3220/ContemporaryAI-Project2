"""Run the CI checks in a clean copy and a fresh Python 3.11 virtual environment."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from time import perf_counter
import venv
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]


def main():
    if sys.version_info[:2]!=(3,11):
        raise SystemExit('Run this script with Python 3.11')
    files=[p for p in ROOT.rglob('*') if p.is_file() and
           not {'.git','__pycache__','.pytest_cache','.venv','venv'}.intersection(p.relative_to(ROOT).parts)
           and p.relative_to(ROOT).parts[:2]!=('results','quick')]
    result={'python':sys.version,'status':'running','steps':[]}
    with tempfile.TemporaryDirectory(prefix='project2-reproduce-') as temporary:
        temp_root=Path(temporary).resolve()
        assert temp_root.parent==Path(tempfile.gettempdir()).resolve() and temp_root.name.startswith('project2-reproduce-')
        checkout=temp_root/'checkout'
        for source in files:
            target=checkout/source.relative_to(ROOT)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
        print('Creating isolated Python 3.11 environment ...',flush=True)
        environment=temp_root/'venv'
        venv.EnvBuilder(with_pip=True).create(environment)
        python=environment/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        commands=[('install',['-m','pip','install','--disable-pip-version-check','-r','requirements-repro.txt']),
            ('pytest',['-m','pytest','-q','-p','no:cacheprovider','--junitxml=results/raw/pytest.xml']),
            ('official',['-m','experiments.verify_official']),
            ('quick',['-m','experiments.run_all','--quick']),
            ('audit',['-m','experiments.audit_results','--quick']),
            ('links',['scripts/check_repository.py','--quick'])]
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','MPLBACKEND':'Agg'}
        for name,args in commands:
            print(f'Running isolated {name} ...',flush=True)
            start=perf_counter()
            proc=subprocess.run([str(python),*args],cwd=checkout,env=env,text=True,
                encoding='utf-8',errors='replace',capture_output=True,timeout=600)
            result['steps'].append({'name':name,'exit_code':proc.returncode,
                                    'elapsed_seconds':perf_counter()-start})
            if proc.returncode:
                print(proc.stdout[-6000:]+proc.stderr[-6000:],flush=True)
                raise SystemExit(f'isolated {name} failed')
        xml=ET.parse(checkout/'results/raw/pytest.xml').getroot()
        result['tests']=sum(int(s.attrib['tests']) for s in xml.iter('testsuite'))
        result['test_failures']=sum(int(s.attrib['failures'])+int(s.attrib['errors']) for s in xml.iter('testsuite'))
        metadata=json.loads((checkout/'results/quick/raw/environment.json').read_text(encoding='utf-8'))
        result.update(status='passed',quick_run_id=metadata['run_id'],
                      dependencies=metadata['dependencies'],source_sha256=metadata['source_sha256'])
    (ROOT/'docs/local_ci_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()

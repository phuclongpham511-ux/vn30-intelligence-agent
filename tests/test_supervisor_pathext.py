"""Actual bootstrap environment; only synthetic runtime gates, never live roles."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest
from scripts.windows import runtime_supervisor as s


def test_actual_bootstrap_preserves_pathext_path_and_secret_allowlist(tmp_path, monkeypatch):
    monkeypatch.setenv('PATHEXT', '.COM;.eXe;.BAT;.cMd;.MSC')
    monkeypatch.setenv('PATH', 'approved-parent-path-kept-exactly')
    monkeypatch.setenv('SSI_API_KEY', 'synthetic-secret-never-forward')
    monkeypatch.setenv('OPENAI_API_KEY', 'synthetic-secret-never-forward')
    monkeypatch.setenv('TECHNICAL_EOD_PILOT', 'synthetic-flag-never-forward')
    monkeypatch.setattr(s.subprocess, 'run', lambda *a,**k: SimpleNamespace(returncode=0,stdout='{"launch_pid":123}'))
    request=tmp_path/'request.json'
    s.independent('pwsh',['python','fixture.py'],tmp_path,request)
    env=dict(line.split('=',1) for line in s.read(request)['environment'])
    assert env['PATHEXT']==os.environ['PATHEXT']
    assert env['PATH']==os.environ['PATH']
    allowed={'PATH','PATHEXT','SystemRoot','WINDIR','TEMP','TMP','USERPROFILE',
             'LOCALAPPDATA','APPDATA','PYTHONUTF8','PYTHONPATH'}
    assert set(env)<=allowed
    assert 'synthetic-secret' not in request.read_text() and 'synthetic-flag' not in request.read_text()


@pytest.mark.parametrize('value,reason', [
    (None,'WINDOWS_PATHEXT_MISSING'), ('','WINDOWS_PATHEXT_MISSING'),
    (' ','WINDOWS_PATHEXT_INVALID'), ('.EXE','WINDOWS_PATHEXT_INVALID'),
    ('.CMD','WINDOWS_PATHEXT_INVALID'), ('.EXE;.CMD;','WINDOWS_PATHEXT_INVALID'),
    ('.EXE;;.CMD','WINDOWS_PATHEXT_INVALID'), ('.EXE;CMD','WINDOWS_PATHEXT_INVALID'),
    ('.EXE;.CMD\n','WINDOWS_PATHEXT_INVALID'),
    ('.EXE;.CMD;C:\\unapproved.exe','WINDOWS_PATHEXT_INVALID'),
])
def test_invalid_pathext_refuses_before_request_or_process_creation(tmp_path,monkeypatch,value,reason):
    if value is None:monkeypatch.delenv('PATHEXT',raising=False)
    else:monkeypatch.setenv('PATHEXT',value)
    monkeypatch.setattr(s.subprocess,'run',lambda *a,**k:pytest.fail('Invalid environment must not launch'))
    request=tmp_path/'request.json'
    with pytest.raises(s.Conflict,match=reason+r': .*parent Windows environment'):
        s.independent('pwsh',['python','fixture.py'],tmp_path,request)
    assert not request.exists()


@pytest.mark.skipif(os.name!='nt',reason='Windows control locks')
def test_missing_pathext_start_fails_before_gate_intent_or_unknown_launch_journal(tmp_path,monkeypatch):
    monkeypatch.delenv('PATHEXT',raising=False)
    monkeypatch.setattr(s.Windows,'validate',lambda *a:pytest.fail('Environment diagnostic precedes git gate'))
    with pytest.raises(s.Conflict,match='WINDOWS_PATHEXT_MISSING'):
        s.control('start',tmp_path,'pwsh')
    store=s.Store(tmp_path)
    assert not store.desired() and not store.load().get('pending_launch')
    assert not (store.path/'launch.json').exists()


@pytest.mark.skipif(os.name!='nt' or not shutil.which('pwsh') or not shutil.which('git'),reason='Windows WMI/git preflight')
def test_wmi_environment_resolves_approved_commands_and_canonical_git_gate(tmp_path):
    """Real detached bootstrap and exact canonical launcher, with fixture secrets.

    All three roles use CheckOnly. No server/collector, application import,
    provider network access or product database is used. Tiny Git repo and
    dummy DB-existence file are isolated fixtures, not product evidence.
    """
    repo=Path(__file__).resolve().parents[1]
    pwsh=shutil.which('pwsh');git=shutil.which('git')
    resolved=s.ps(pwsh,"@{git=(Get-Command git -ErrorAction Stop).Source;npm=(Get-Command npm -ErrorAction Stop).Source}|ConvertTo-Json -Compress")
    npm_version=s.ps(pwsh,'npm --version | ConvertTo-Json -Compress')
    assert os.path.samefile(resolved['git'],git)
    source=tmp_path/'source';source.mkdir()
    (source/'README').write_text('synthetic bootstrap preflight\n')
    (source/'.gitignore').write_text('.venv/\n')
    for args in (['init'],['add','README','.gitignore'],
                 ['-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                  '-c','commit.gpgsign=false','commit','-m','fixture']):
        subprocess.run([git,'-C',str(source),*args],capture_output=True,check=True,timeout=10)
    sha=subprocess.check_output([git,'-C',str(source),'rev-parse','HEAD'],text=True,timeout=10).strip()
    junction=source/'.venv'
    s.ps(pwsh,'New-Item -ItemType Junction -Path '+s.literal(junction)+' -Target '+s.literal(sys.prefix)+' | Out-Null')
    for folder in ('launch','config','state'):(tmp_path/folder).mkdir()
    # This fixture is an unchanged copy of the installed canonical launcher.
    shutil.copyfile(repo/'tests/fixtures/windows/Invoke-Woofi.ps1',tmp_path/'launch/Invoke-Woofi.ps1')
    secret=tmp_path/'fixture.env';secret.write_text('SSI_API_KEY=synthetic-key\nSSI_API_SECRET=synthetic-secret\n')
    db=tmp_path/'exists-only.db';db.write_bytes(b'fixture existence, never opened')
    before=db.read_bytes()
    cfg={'canonical_sha':sha,'source_checkout':str(source),'product_database':str(db),
         'secret_configuration':str(secret),'backend_port':18000,'frontend_port':13000}
    s.atomic(tmp_path/'config/runtime.json',cfg)
    s.atomic(tmp_path/'state/cutover-ready.json',{'canonical_sha':sha,'database_path':str(db),
        'old_writers_exited':True,'final_backup_verified':True,'live_launch_authorized':True})
    (tmp_path/'launch/ssi_configuration.py').write_text('''import argparse,json
from pathlib import Path
from dotenv import dotenv_values
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['check']);p.parse_args()
root=Path(__file__).resolve().parents[1]
cfg=json.loads((root/'config/runtime.json').read_text())
values=dotenv_values(cfg['secret_configuration'])
assert values['SSI_API_KEY']=='synthetic-key' and values['SSI_API_SECRET']=='synthetic-secret'
print(json.dumps({'runtime_recognizes_credentials':True}))
''')
    request=tmp_path/'request.json'
    child=tmp_path/'probe.py'
    child.write_text('''import json,os,sys
from pathlib import Path
sys.path.insert(0,REPO)
from scripts.windows import runtime_supervisor as s
p=Path(__file__).parent
result={'pathext':os.environ.get('PATHEXT'),'path_preserved':os.environ.get('PATH')==EXPECTED_PATH,
        'secret_environment_absent':all(not os.environ.get(k) for k in ('SSI_API_KEY','SSI_API_SECRET','OPENAI_API_KEY','TECHNICAL_EOD_PILOT'))}
try:
 result['resolved']=s.ps(PWSH,"@{git=(Get-Command git -ErrorAction Stop).Source;npm=(Get-Command npm -ErrorAction Stop).Source}|ConvertTo-Json -Compress")
 result['npm_version']=s.ps(PWSH,'npm --version | ConvertTo-Json -Compress')
 cfg=s.read(p/'config/runtime.json')
 driver=s.Windows(p.resolve(),PWSH,s.bind(cfg),lambda *a,**k:None)
 result['validated_sha']=driver.validate()['canonical_sha']
 result['role_gates']={role:s.ps(PWSH,'& '+s.literal(p/'launch/Invoke-Woofi.ps1')+' -Role '+role+' -CheckOnly')['Ready'] for role in s.ROLES}
except Exception as exc:
 result['error']=str(exc) if isinstance(exc,s.Conflict) else type(exc).__name__
(p/'finished.json').write_text(json.dumps(result))
'''.replace('REPO',repr(str(repo))).replace('PWSH',repr(pwsh)).replace('EXPECTED_PATH',repr(os.environ['PATH'])))
    s.independent(pwsh,[sys.executable,'-B',str(child)],tmp_path,request)
    deadline=time.monotonic()+25
    while not (tmp_path/'finished.json').exists() and time.monotonic()<deadline:time.sleep(.05)
    assert (tmp_path/'finished.json').exists(),'Finite bootstrap preflight did not finish'
    result=json.loads((tmp_path/'finished.json').read_text())
    assert result['pathext']==os.environ['PATHEXT'],result
    assert result['path_preserved'] and result['secret_environment_absent']
    assert 'error' not in result,result
    for command in ('git','npm'):assert os.path.samefile(result['resolved'][command],resolved[command])
    assert result['npm_version']==npm_version
    assert result['validated_sha']==sha and result['role_gates']==dict.fromkeys(s.ROLES,True)
    assert db.read_bytes()==before and not (tmp_path/'state/supervisor-v1').exists()

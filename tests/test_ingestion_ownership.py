"""Independent processes exercise the real worker with controlled upstream seams."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest
import sqlmodel
from sqlmodel import create_engine

from src.community.acquisition import SOURCES
from src.community.daily import ingest_cycle
from src.db.session import create_tables
from datetime import datetime, timedelta, timezone

CHILD = r'''
import json,sys,time
from pathlib import Path
from sqlmodel import create_engine
from src.db.session import create_tables
from scripts import ingest_data
from src.providers.ssi import SsiMarketDataProvider
from src.community.daily import ingest_cycle
url,folder,role,mode=sys.argv[1:]
folder=Path(folder)
engine=create_engine(url);create_tables(engine)
def fetch(self):
    (folder/(role+'.called')).write_text('controlled upstream call')
    if role=='first':
        while not (folder/'release').exists():time.sleep(.02)
    raise TimeoutError('synthetic upstream')
SsiMarketDataProvider.get_security_universe=fetch
SsiMarketDataProvider.get_index_memberships=lambda *_: {}
ingest_data.ingest_community=lambda engine:ingest_cycle(engine,sources=[])
registry=folder/'sources.json'
registry.write_text('[]') if not registry.exists() else None
if mode=='watch':
    class Stop:
        ended=False
        def is_set(self):return self.ended
        def wait(self,seconds):
            (folder/'idle').write_text('waiting')
            while not (folder/'stop').exists():time.sleep(.02)
            self.ended=True
    result=ingest_data.run(engine,watch=True,registry=str(registry),stop=Stop())
elif mode in ('news_smoke','news_force'):
    from scripts import ingest_news
    ingest_news.get_engine=lambda:engine
    sys.argv=['ingest_news','--smoke' if mode=='news_smoke' else '--force','--registry',str(registry)]
    result=ingest_news.main()
elif mode=='community':
    from scripts import ingest_community
    ingest_community.get_engine=lambda:engine
    sys.argv=['ingest_community']
    result=ingest_community.main()
elif mode=='direct_community':result=ingest_cycle(engine,sources=[])
elif mode=='direct_news':
    from sqlmodel import Session
    from src.news.service import ingest_cycle as news_cycle
    with Session(engine) as session:result=news_cycle(session,[])
else:result=ingest_data.run_cycle(engine,registry=str(registry))
print(json.dumps(result),flush=True)
'''


def command(tmp_path, role, mode='cycle'):
    env=dict(os.environ, PYTHONPATH=os.pathsep.join((str(Path.cwd()),str(Path(sqlmodel.__file__).parents[1]))),
        PYTHONDONTWRITEBYTECODE='1',SSI_API_KEY='',SSI_API_SECRET='',OPENAI_API_KEY='')
    return [sys._base_executable,'-B','-c',CHILD,'sqlite:///'+str(tmp_path/'owner.db'),str(tmp_path),role,mode], env


def wait_for(path):
    until=time.monotonic()+10
    while not path.exists() and time.monotonic()<until:time.sleep(.02)
    assert path.exists(), 'Controlled worker did not reach barrier'


@pytest.mark.parametrize('mode', ['cycle','news_smoke','news_force','community','direct_community','direct_news'])
def test_independent_process_cannot_acquire_while_collector_is_active(tmp_path, mode):
    args,env=command(tmp_path,'first')
    first=subprocess.Popen(args,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        wait_for(tmp_path/'first.called')
        args,env=command(tmp_path,'second',mode)
        second=subprocess.run(args,env=env,capture_output=True,text=True,timeout=10)
        result=json.loads(second.stdout.splitlines()[-1])
        assert result == (1 if mode in ('news_smoke','news_force','community') else {'status':'collector_busy'})
        assert not (tmp_path/'second.called').exists()
    finally:
        (tmp_path/'release').write_text('release')
        first.communicate(timeout=10)
    assert first.returncode==0


def test_watch_retains_ownership_between_cycles(tmp_path):
    args,env=command(tmp_path,'first','watch')
    first=subprocess.Popen(args,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        wait_for(tmp_path/'first.called');(tmp_path/'release').write_text('release')
        wait_for(tmp_path/'idle')
        args,env=command(tmp_path,'second')
        second=subprocess.run(args,env=env,capture_output=True,text=True,timeout=10)
        assert json.loads(second.stdout.splitlines()[-1])=={'status':'collector_busy'}
    finally:
        (tmp_path/'release').write_text('release');(tmp_path/'stop').write_text('stop')
        first.communicate(timeout=10)
    assert first.returncode==0


def test_process_death_releases_owner_but_preserves_universe_cooldown(tmp_path):
    args,env=command(tmp_path,'first')
    first=subprocess.Popen(args,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        wait_for(tmp_path/'first.called')
        first.kill();first.communicate(timeout=10)
        args,env=command(tmp_path,'second')
        second=subprocess.run(args,env=env,capture_output=True,text=True,timeout=10)
        result=json.loads(second.stdout.splitlines()[-1])
        assert result['universe']['status']=='skipped'
        assert result['technical_eod']['status']=='IDLE'
        assert not (tmp_path/'second.called').exists()
    finally:
        if first.poll() is None:first.kill();first.communicate(timeout=10)


def test_interrupted_community_attempt_keeps_cooldown_after_reconnect(tmp_path):
    url='sqlite:///'+str(tmp_path/'community.db')
    engine=create_engine(url);create_tables(engine)
    now=datetime(2026,10,10,12,tzinfo=timezone.utc)
    def interrupted(*_):raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        ingest_cycle(engine,sources=SOURCES[:1],fetch=interrupted,now=now)
    engine.dispose();engine=create_engine(url)
    result=ingest_cycle(engine,sources=SOURCES[:1],
        fetch=lambda *_:pytest.fail('Restart bypassed source cooldown'),now=now+timedelta(minutes=1))
    assert result=={SOURCES[0].id:{'status':'skipped'}}
    engine.dispose()

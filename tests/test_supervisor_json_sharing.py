"""Native deterministic JSON reader/writer overlap, no services or product DB."""
import json
import os
import subprocess
import sys

import pytest

from scripts.windows import runtime_supervisor as s

pytestmark=pytest.mark.skipif(os.name!='nt',reason='Windows file-sharing semantics')


def test_open_status_reader_serializes_new_generation_without_sharing_failure(tmp_path):
    path=tmp_path/'status.json'
    s.atomic(path,{'epoch':'old','roles':{'Collector':{'pid':1}}})
    code=('import sys\nfrom pathlib import Path\nfrom scripts.windows import runtime_supervisor as s\n'
          's.STATE_IO_WAIT_MS=50\n'
          's.atomic(Path(sys.argv[1]),{"epoch":"new","roles":{"Collector":{"pid":2}}})\n')
    def writer():
        return subprocess.run([sys.executable,'-B','-c',code,str(path)],capture_output=True,
            text=True,timeout=15,cwd=str(s.Path(s.__file__).resolve().parents[2]))
    with s.state_io(), path.open(encoding='utf-8-sig') as reader:
        # The independent writer reaches a bounded native wait while the real
        # read handle remains open. It cannot touch the new generation yet.
        blocked=writer()
        assert blocked.returncode!=0 and 'STATE_IO_UNVERIFIED wait code=258' in blocked.stderr
        assert json.load(reader)=={'epoch':'old','roles':{'Collector':{'pid':1}}}
    written=writer()
    assert written.returncode==0,written.stderr
    assert s.read(path)=={'epoch':'new','roles':{'Collector':{'pid':2}}}
    assert list(tmp_path.iterdir())==[path]


def test_native_status_read_waits_for_physical_json_writer(tmp_path):
    path=tmp_path/'status.json';s.atomic(path,{'epoch':'retained'})
    code=('import sys\nfrom pathlib import Path\nfrom scripts.windows import runtime_supervisor as s\n'
          's.STATE_IO_WAIT_MS=50\nprint(s.read(Path(sys.argv[1])))\n')
    def reader():
        return subprocess.run([sys.executable,'-B','-c',code,str(path)],capture_output=True,
            text=True,timeout=15,cwd=str(s.Path(s.__file__).resolve().parents[2]))
    with s.state_io():
        blocked=reader()
        assert blocked.returncode!=0 and 'STATE_IO_UNVERIFIED wait code=258' in blocked.stderr
        assert not blocked.stdout
    completed=reader()
    assert completed.returncode==0,completed.stderr
    assert 'retained' in completed.stdout


def test_missing_json_default_and_corruption_are_distinct(tmp_path):
    path=tmp_path/'state.json';marker=object()
    assert s.read(path,marker) is marker
    path.write_text('broken',encoding='utf-8')
    with pytest.raises(json.JSONDecodeError):s.read(path,marker)
    path.write_text('{"epoch":"valid"}',encoding='utf-8-sig')
    assert s.read(path)=={'epoch':'valid'}

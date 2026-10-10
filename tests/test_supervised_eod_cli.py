"""Pilot entry point scope and no-write default; no SSI or real network."""
import json
import pytest
from scripts import supervise_technical_eod as cli


def test_checked_in_configuration_pins_only_isolated_pilot_paths():
    config,paths=cli.configuration(cli.ROOT/'docs'/'TECHNICAL_FPT_PILOT_V1.json')
    assert config['ticker']=='FPT'
    assert paths['database_file'].is_relative_to(cli.ROOT/'data'/'technical_eod')
    assert all(p.is_relative_to(cli.ROOT) for p in paths.values())


@pytest.mark.parametrize('mutation',['outside','unbounded','checksum'])
def test_invalid_config_rejected_before_runtime_access(tmp_path,mutation):
    value=json.loads((cli.ROOT/'docs'/'TECHNICAL_FPT_PILOT_V1.json').read_bytes())
    if mutation=='outside':value['database_file']=str(tmp_path/'external.db')
    if mutation=='unbounded':value['tickers']=['FPT','OTHER']
    if mutation=='checksum':value['security_receipt_sha256']='0'*64
    path=tmp_path/'config.json';path.write_text(json.dumps(value))
    with pytest.raises(ValueError):cli.configuration(path)


def test_default_is_public_source_dry_run_without_bootstrap(tmp_path,monkeypatch,capsys):
    from src.services.hose_eod_discovery import seed_calendar
    monkeypatch.setattr(cli,'configuration',lambda _:({'ticker':'XYZ'},{
        'calendar_seed':cli.ROOT/'docs'/'unused',
        'qualified_publication_anchor':cli.ROOT/'docs'/'unused',
        'database_file':tmp_path/'absent.db'}))
    monkeypatch.setattr(cli,'OfficialHoseSource',lambda *a:object())
    monkeypatch.setattr(cli,'discovery_plan',lambda *a:{'status':'NO_NEW_ELIGIBLE_SESSION',
        'calendar':seed_calendar(cli.ROOT/'docs'),'qualified':None})
    monkeypatch.setattr(cli,'Settings',lambda **kw:pytest.fail('dry credentials'))
    monkeypatch.setattr(cli,'create_tables',lambda *a:pytest.fail('dry bootstrap'))
    assert cli.main([])==0
    result=json.loads(capsys.readouterr().out)
    assert result['ssi_requests']==result['writes']==0
    assert not (tmp_path/'absent.db').exists()


def test_resume_cannot_mutate_dry_run_or_bootstrap(monkeypatch,capsys):
    monkeypatch.setattr(cli,'configuration',lambda *a:pytest.fail('resume before validation'))
    assert cli.main(['--resume','--dry-run'])==1
    assert json.loads(capsys.readouterr().out)['status']=='BLOCKED'

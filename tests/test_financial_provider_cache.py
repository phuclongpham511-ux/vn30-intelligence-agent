"""Synthetic packets only: cache scheduling must not change acquisition budgets."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import pytest

from src.providers.vnstock import VnstockFundamentalDataProvider
from test_financial_engine import packet


def test_warm_packet_is_not_blocked_by_an_unrelated_cold_provider_read(monkeypatch):
    entered, release = Event(), Event()
    def fetch(symbol, sdk):
        if symbol == 'COLD':
            entered.set()
            assert release.wait(3)
        return packet()
    monkeypatch.setattr('src.providers.vnstock.financial_packet.fetch_packet', fetch)
    provider = VnstockFundamentalDataProvider()
    provider.get_reports('WARM')
    with ThreadPoolExecutor(max_workers=2) as pool:
        cold = pool.submit(provider.get_reports, 'COLD')
        assert entered.wait(2)
        warm = pool.submit(provider.get_reports, 'WARM')
        try:
            assert warm.result(timeout=.25).is_fixture
        finally:
            release.set()
        cold.result(timeout=2)


def test_cold_packets_keep_one_upstream_owner_and_duplicate_reads_coalesce(monkeypatch):
    entered, release = Event(), Event()
    calls = []
    def fetch(symbol, sdk):
        calls.append(symbol)
        entered.set()
        assert release.wait(3)
        return packet()
    monkeypatch.setattr('src.providers.vnstock.financial_packet.fetch_packet', fetch)
    provider = VnstockFundamentalDataProvider()
    with ThreadPoolExecutor(max_workers=4) as pool:
        first = pool.submit(provider.get_reports, 'ABC')
        assert entered.wait(2)
        same = pool.submit(provider.get_reports, 'ABC')
        other = pool.submit(provider.get_reports, 'XYZ')
        assert calls == ['ABC']
        release.set()
        assert all(f.result(timeout=2).is_fixture for f in (first, same, other))
    assert calls == ['ABC', 'XYZ']


def test_hour_boundary_eviction_mutation_and_partial_error_semantics(monkeypatch):
    clock = [3600.]
    calls = []
    def fetch(symbol, sdk):
        calls.append(symbol)
        value = packet()
        value.reports['cash'].status = 'error'
        value.reports['cash'].observations = []
        return value
    monkeypatch.setattr('src.providers.vnstock.time.time', lambda: clock[0])
    monkeypatch.setattr('src.providers.vnstock.financial_packet.fetch_packet', fetch)
    provider = VnstockFundamentalDataProvider()
    first = provider.get_reports('ABC')
    first.reports['income'].observations.clear()
    assert provider.get_reports('ABC').reports['income'].observations
    assert provider.get_reports('ABC').reports['cash'].status == 'error'
    assert calls == ['ABC']
    clock[0] = 7200.
    provider.get_reports('ABC')
    assert calls == ['ABC', 'ABC']
    for index in range(129):
        provider.get_reports('S' + str(index))
    provider.get_reports('ABC')
    assert calls.count('ABC') == 3


def test_total_provider_failure_is_not_cached_as_success(monkeypatch):
    calls = []
    def fetch(symbol, sdk):
        calls.append(symbol)
        raise TimeoutError('synthetic failure')
    monkeypatch.setattr('src.providers.vnstock.financial_packet.fetch_packet', fetch)
    provider = VnstockFundamentalDataProvider()
    from src.providers.base import ProviderError
    for _ in range(2):
        with pytest.raises(ProviderError):
            provider.get_reports('ABC')
    assert calls == ['ABC', 'ABC']


def test_fast_copy_preserves_complete_packet_and_detaches_every_mutable_graph(monkeypatch):
    saved = packet()
    monkeypatch.setattr('src.providers.vnstock.financial_packet.fetch_packet', lambda *_:saved)
    provider = VnstockFundamentalDataProvider()
    first = provider.get_reports('ABC')
    assert first == saved and first is not saved
    observation = first.reports['income'].observations[0]
    observation.fields['revenue'] = None
    observation.items[0].source_labels.append({'name':'changed'})
    first.reports['balance'].observations.clear()
    second = provider.get_reports('ABC')
    assert second == saved
    assert second.reports['income'].observations[0].fields['revenue'] is not None
    assert second.reports['income'].observations[0].items[0].source_labels != observation.items[0].source_labels


def test_invalid_nonfinite_cached_input_cannot_be_normalized_into_missing_success(monkeypatch):
    saved = packet()
    saved.reports['income'].observations[0].fields['revenue'] = float('inf')
    monkeypatch.setattr('src.providers.vnstock.financial_packet.fetch_packet', lambda *_:saved)
    provider = VnstockFundamentalDataProvider()
    with pytest.raises(ValueError):
        provider.get_reports('ABC')

"""Synthetic contract tests; no fixture is a qualified live HOSE/SSI source."""
from datetime import date, datetime, timedelta, timezone
import httpx
import pytest

from test_eod_readiness import modern
from test_technical_eod_consumer import metadata

from src.config.settings import Settings
from src.models import Security
from src.providers.ssi import SsiMarketDataProvider
from src.services.provisional_eod import (
    AuthenticatedSsiHistoryRead, HosePublicationEvidence,
    ProvisionalTechnicalDailyPacket, ProvisionalInMemoryRegistry, assess_provisional_eod,
    capture_fresh_ssi_read, compact_ssi_receipt, parse_compact_ssi_receipt,
    evaluate_provisional_technical_eod_packet,
    summarize_provisional_result, _fingerprint,
)
from src.services.technical_eod import evaluate_technical_eod_packet
from src.services.technical_api import TechnicalAPIPacket

UTC = timezone.utc
HOSE = 'https://www.hsx.vn/vi/tin-tuc/synthetic-test-record'


def test_fresh_acquisition_uses_authenticated_transport_and_receipts():
    calls=[]
    def respond(request):
        if request.url.path.endswith('/token'):
            return httpx.Response(200,json={'accessToken':'synthetic-token','expiresAt':4102444800000})
        calls.append(dict(request.url.params))
        rows=[{'symbol':'XYZ','tradingDate':'2024/09/20','open':'19750','high':'20100',
            'low':'19650','close':'19650','volume':'15048900'}] if request.url.params['pageIndex']=='1' else []
        return httpx.Response(200,json={'data':rows})
    with SsiMarketDataProvider(Settings(_env_file=None,ssi_api_key='synthetic-key',
        ssi_api_secret='synthetic-secret'),transport=httpx.MockTransport(respond),
        today=lambda:date(2024,9,21)) as provider:
        with pytest.raises(ValueError):
            capture_fresh_ssi_read('XYZ',date(2024,9,19),date(2024,9,21),provider=provider)
        receipt=capture_fresh_ssi_read('XYZ',date(2024,9,19),date(2024,9,20),provider=provider)
        again=capture_fresh_ssi_read('XYZ',date(2024,9,19),date(2024,9,20),provider=provider)
    assert len(calls)==4
    assert receipt.request_started_at <= receipt.history.observed_at <= receipt.received_at
    assert again.request_started_at <= again.history.observed_at <= again.received_at
    assert receipt.history.source_version == again.history.source_version
    assert receipt.cache_bypassed and len(receipt.history.observations)==1


def evidence():
    data, read, calendar = modern()
    read = read.model_copy(update={'source_version': _fingerprint(read), 'completion_evidence':()})
    target = date.fromisoformat(data['calendar'][-1])
    published = datetime.combine(target, datetime.min.time(), UTC) + timedelta(hours=9)
    first_at = published + timedelta(hours=1)
    second_at = published + timedelta(hours=25)
    records = tuple(r.model_copy(update={'source_ref': HOSE, 'verified_at': published,
        'observed_at': published}) for r in calendar.records)
    calendar = calendar.model_copy(update={'records': records})
    pub = HosePublicationEvidence(venue='HOSE', session=target, source_ref=HOSE,
        content_sha256='a'*64, published_at=published, observed_at=published,
        verified_at=published)
    first = AuthenticatedSsiHistoryRead(requested_ticker='XYZ',
        range_start=calendar.coverage_start,range_end=target,
        history=read.model_copy(update={'observed_at': first_at}),
        request_started_at=first_at-timedelta(seconds=2), received_at=first_at)
    second = AuthenticatedSsiHistoryRead(requested_ticker='XYZ',
        range_start=calendar.coverage_start,range_end=target,
        history=read.model_copy(update={'observed_at': second_at}),
        request_started_at=second_at-timedelta(seconds=2), received_at=second_at)
    return target, calendar, pub, first, second


def assess(target, calendar, pub, first, second):
    start = first.range_start if first else None
    return assess_provisional_eod('XYZ', target, history_start=start,
        calendar=calendar, publication=pub, first=first, second=second,
        evaluation_as_of=second.received_at + timedelta(minutes=1) if second else datetime(2020,4,2,tzinfo=UTC))


def test_qualified_synthetic_evidence_is_provisional_never_verified():
    result = assess(*evidence())
    assert result.status == 'PROVISIONAL'
    assert result.assurance == 'PROVISIONAL'
    assert result.reason_codes == ()
    assert result.source_version is not None


def test_metadata_only_first_receipt_supports_later_comparison():
    target, calendar, pub, first, second = evidence()
    compact = compact_ssi_receipt(first)
    assert assess(target, calendar, pub, compact, second).status == 'PROVISIONAL'
    assert 'observations' not in compact.model_dump(mode='json')
    file_payload = dict(schema_version='ssi-provisional-receipt-v1',
        policy_version='provisional-operational-eod-v1',
        raw_ohlcv_persisted=False, ticker=compact.requested_ticker,
        range_start=compact.range_start.isoformat(), range_end=compact.range_end.isoformat(),
        request_started_at=compact.request_started_at.isoformat(),
        source_observed_at=compact.observed_at.isoformat(),
        received_at=compact.received_at.isoformat(),
        canonical_observations_sha256=compact.source_version,
        observation_count=compact.observation_count,
        target_present=compact.target_present, source=compact.source,
        adjustment_semantics=compact.adjustment_semantics,
        price_unit=compact.price_unit, volume_unit=compact.volume_unit,
        observation_mode=compact.observation_mode, is_fixture=compact.is_fixture,
        transport=compact.transport, cache_bypassed=compact.cache_bypassed)
    restored = parse_compact_ssi_receipt(file_payload)
    assert restored == compact
    changed = dict(file_payload, canonical_observations_sha256='0'*64)
    assert 'ssi_history_revision_detected' in assess(
        target, calendar, pub, parse_compact_ssi_receipt(changed), second).reason_codes
    with pytest.raises(ValueError):
        parse_compact_ssi_receipt(dict(file_payload, raw_ohlcv_persisted=True))


def test_separate_packet_path_reuses_consumer_and_preserves_verified_gate(session):
    metadata(session)
    target, calendar, pub, first, second = evidence()
    cutoff=second.received_at+timedelta(minutes=1)
    security=session.get(Security,'XYZ')
    security.last_synced_at=first.request_started_at-timedelta(days=1)
    session.commit()
    verified=evaluate_technical_eod_packet('XYZ',target,evaluation_as_of=cutoff,
        generated_at=cutoff,db_session=session,history_read=second.history,
        calendar=calendar,history_start=calendar.coverage_start)
    assert verified.status=='INCOMPLETE_EVIDENCE'
    assert 'eod_completion_proof_unavailable_or_duplicate' in verified.reason_codes
    provisional=evaluate_provisional_technical_eod_packet('XYZ',target,
        history_start=calendar.coverage_start,calendar=calendar,publication=pub,
        first=compact_ssi_receipt(first),second=second,evaluation_as_of=cutoff,generated_at=cutoff,
        db_session=session)
    assert isinstance(provisional,ProvisionalTechnicalDailyPacket)
    assert provisional.assurance=='PROVISIONAL'
    assert provisional.safe_to_display_as_verified is False
    assert provisional.packet.data_provenance['completion_assurance']=='PROVISIONAL'
    assert 'operational_provisional_not_finality_verified' in provisional.packet.limitations
    summary=summarize_provisional_result(provisional)
    assert summary['status']=='PROVISIONAL' and summary['safe_to_display_as_verified'] is False
    assert 'observations' not in summary and 'token' not in summary
    with pytest.raises(ValueError):
        TechnicalAPIPacket(packet=provisional.packet)


def test_later_ssi_revision_invalidates_active_provisional_packet(session):
    metadata(session)
    target, calendar, pub, first, second = evidence()
    security=session.get(Security,'XYZ')
    security.last_synced_at=first.request_started_at-timedelta(days=1)
    session.commit()
    cutoff=second.received_at+timedelta(minutes=1)
    packet=evaluate_provisional_technical_eod_packet('XYZ',target,
        history_start=calendar.coverage_start,calendar=calendar,publication=pub,
        first=first,second=second,evaluation_as_of=cutoff,generated_at=cutoff,
        db_session=session)
    assert isinstance(packet,ProvisionalTechnicalDailyPacket)
    registry=ProvisionalInMemoryRegistry()
    registry.add(packet)
    later_at=second.received_at+timedelta(hours=1)
    unchanged=second.model_copy(update={'request_started_at':later_at-timedelta(seconds=2),
        'received_at':later_at,'history':second.history.model_copy(update={'observed_at':later_at})})
    assert registry.observe(unchanged)==()
    assert registry.get(packet.packet.packet_id)==packet
    observations=list(unchanged.history.observations)
    last=observations[-1]
    observations[-1]=last.model_copy(update={'payload':last.payload.model_copy(update={'close':last.payload.close+1})})
    revised=unchanged.history.model_copy(update={'observations':tuple(observations)})
    revised=revised.model_copy(update={'source_version':_fingerprint(revised)})
    changed=unchanged.model_copy(update={'history':revised})
    invalidations=registry.observe(changed)
    assert len(invalidations)==1
    assert invalidations[0].status=='INVALIDATED'
    assert invalidations[0].packet_id==packet.packet.packet_id
    assert registry.get(packet.packet.packet_id) is None
    assert summarize_provisional_result(invalidations[0])['status']=='INVALIDATED'


def test_missing_publication_stays_incomplete():
    target, calendar, _, first, second = evidence()
    result = assess(target, calendar, None, first, second)
    assert result.status == 'INCOMPLETE_EVIDENCE'
    assert 'publication_evidence_unavailable' in result.reason_codes


def test_missing_publication_never_runs_the_packet_consumer(session):
    target, calendar, _, first, second = evidence()
    cutoff=second.received_at+timedelta(minutes=1)
    result=evaluate_provisional_technical_eod_packet('XYZ',target,
        history_start=calendar.coverage_start,calendar=calendar,publication=None,
        first=first,second=second,evaluation_as_of=cutoff,generated_at=cutoff,
        db_session=session)
    assert result.status=='INCOMPLETE_EVIDENCE'
    assert result.reason_codes==('publication_evidence_unavailable',)
    assert summarize_provisional_result(result)['available_observation_count']==len(second.history.observations)


def test_missing_or_unverified_calendar_stays_incomplete():
    target, calendar, pub, first, second = evidence()
    assert 'verified_session_calendar_unavailable' in assess(target, None, pub, first, second).reason_codes
    records = calendar.records[:-1]
    result = assess(target, calendar.model_copy(update={'records': records}), pub, first, second)
    assert result.status == 'INCOMPLETE_EVIDENCE'


def test_both_elapsed_time_gates_are_required():
    target, calendar, pub, first, second = evidence()
    later_first_at=pub.published_at+timedelta(hours=10)
    later_first=first.model_copy(update={'received_at':later_first_at,
        'request_started_at':later_first_at-timedelta(seconds=2),
        'history':first.history.model_copy(update={'observed_at':later_first_at})})
    early_at=later_first_at+timedelta(hours=5)
    early = second.model_copy(update={'received_at':early_at,
        'request_started_at':early_at-timedelta(seconds=2),
        'history':second.history.model_copy(update={'observed_at':early_at})})
    assert 'reads_less_than_six_hours_apart' in assess(target, calendar, pub, later_first, early).reason_codes
    before_24 = second.model_copy(update={'received_at': pub.published_at+timedelta(hours=23),
        'request_started_at': pub.published_at+timedelta(hours=23)-timedelta(seconds=2),
        'history':second.history.model_copy(update={'observed_at':pub.published_at+timedelta(hours=23)})})
    assert 'second_read_before_publication_delay' in assess(target, calendar, pub, first, before_24).reason_codes


def test_exact_six_and_twenty_four_hour_boundaries_are_admitted():
    target, calendar, pub, first, second = evidence()
    first_at=pub.published_at+timedelta(hours=18)
    second_started=pub.published_at+timedelta(hours=24)
    second_at=second_started+timedelta(seconds=2)
    first=first.model_copy(update={'received_at':first_at,
        'request_started_at':first_at-timedelta(seconds=2),
        'history':first.history.model_copy(update={'observed_at':first_at})})
    second=second.model_copy(update={'received_at':second_at,
        'request_started_at':second_started,
        'history':second.history.model_copy(update={'observed_at':second_at})})
    assert assess(target, calendar, pub, first, second).status=='PROVISIONAL'


def test_second_request_cannot_begin_just_before_publication_delay():
    target, calendar, pub, first, second = evidence()
    started=pub.published_at+timedelta(hours=24)-timedelta(seconds=1)
    received=started+timedelta(seconds=2)
    second=second.model_copy(update={'request_started_at':started,
        'received_at':received,
        'history':second.history.model_copy(update={'observed_at':received})})
    assert 'second_read_before_publication_delay' in assess(target,calendar,pub,first,second).reason_codes


def test_mismatched_read_is_revision_and_cannot_be_accepted():
    target, calendar, pub, first, second = evidence()
    observations=list(second.history.observations)
    last=observations[-1]
    observations[-1]=last.model_copy(update={'payload':last.payload.model_copy(update={'close':last.payload.close+1})})
    changed = second.history.model_copy(update={'observations':tuple(observations)})
    changed = changed.model_copy(update={'source_version':_fingerprint(changed)})
    result = assess(target, calendar, pub, first, second.model_copy(update={'history':changed}))
    assert result.status == 'INCOMPLETE_EVIDENCE'
    assert 'ssi_history_revision_detected' in result.reason_codes


def test_late_or_unqualified_publication_is_incomplete():
    target, calendar, pub, first, second = evidence()
    late = pub.model_copy(update={'observed_at':second.received_at+timedelta(minutes=1),
        'verified_at':second.received_at+timedelta(minutes=1)})
    assert 'publication_not_visible_at_read' in assess(target, calendar, late, first, second).reason_codes
    unqualified = pub.model_copy(update={'source_ref':'https://example.com/republished'})
    assert 'publication_source_not_qualified' in assess(target, calendar, unqualified, first, second).reason_codes


def test_cached_or_unbounded_receipts_are_not_accepted():
    target, calendar, pub, first, second = evidence()
    cached = first.model_copy(update={'cache_bypassed':False})
    assert 'authenticated_fresh_read_unavailable' in assess(target, calendar, pub, cached, second).reason_codes
    too_late = first.model_copy(update={'history':first.history.model_copy(update={
        'observed_at':first.received_at+timedelta(minutes=1)})})
    assert 'read_receipt_invalid' in assess(target, calendar, pub, too_late, second).reason_codes

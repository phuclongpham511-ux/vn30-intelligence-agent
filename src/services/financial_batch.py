"""Bounded, resumable private acquisition using the existing VCI packet adapter."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from src.schemas.financials import FinancialPacket
from src.services.personal_financials import saved_packet

MAX_BATCH_TICKERS = 15
MAX_INDEX_BYTES = 2_000_000
MAX_PACKET_BYTES = 32_000_000


def _safe_tickers(tickers):
    values = [str(value).strip().upper() for value in tickers]
    if not values or len(values) > MAX_BATCH_TICKERS:
        raise ValueError(f'Batch must contain 1 to {MAX_BATCH_TICKERS} tickers')
    if any(not re.fullmatch(r'[A-Z0-9]{1,20}', value) for value in values):
        raise ValueError('Invalid ticker list')
    if len(set(values)) != len(values):
        raise ValueError('Duplicate ticker in batch')
    return values


def _atomic_bytes(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix='.financial-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _write_immutable(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if path.read_bytes() != data:
            raise ValueError('Capture hash collision or immutable file conflict')


def _fingerprint(packet: FinancialPacket):
    return dict(ticker=packet.ticker, source=packet.source, source_version=packet.source_version,
        company_type=packet.company_type, profile=packet.profile, metadata_sha256=packet.metadata_sha256,
        reports={kind: dict(status=receipt.status, content_sha256=receipt.content_sha256,
            periods=sorted(obs.period for obs in receipt.observations))
            for kind, receipt in sorted(packet.reports.items())})


def _index_bytes(index):
    data = (json.dumps(index, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    if len(data) > MAX_INDEX_BYTES:
        raise ValueError('Saved capture index exceeds size bound')
    return data


def _validate_packet(packet, ticker):
    if not isinstance(packet, FinancialPacket):
        raise ValueError('Acquisition adapter returned an invalid packet')
    if packet.ticker != ticker or packet.source != 'vnstock:VCI' or packet.is_fixture:
        raise ValueError('Acquisition packet identity is not eligible')
    if set(packet.reports) != {'income', 'balance', 'cash'}:
        raise ValueError('Acquisition packet statement schema is incomplete')
    for receipt in packet.reports.values():
        counts = {'annual': 0, 'quarterly': 0}
        for observation in receipt.observations:
            counts[observation.frequency] += 1
        if any(count > 4 for count in counts.values()):
            raise ValueError('Acquisition packet exceeds the four-period SDK bound')
    if not any(receipt.observations for receipt in packet.reports.values()):
        raise ValueError('No usable statement observations returned')


def _coverage(packet):
    result = {}
    for kind, receipt in packet.reports.items():
        codes = {line.code for observation in receipt.observations for line in observation.items}
        result[kind] = dict(status=receipt.status,
            annual_periods=sorted(o.period for o in receipt.observations if o.frequency == 'annual'),
            quarterly_periods=sorted(o.period for o in receipt.observations if o.frequency == 'quarterly'),
            source_field_codes=len(codes), source_values=sum(line.value is not None
                for observation in receipt.observations for line in observation.items),
            missing_values=sum(line.value is None for observation in receipt.observations for line in observation.items))
    return result


def _save_index(root, index):
    _atomic_bytes(root / 'index.json', _index_bytes(index))


def acquire_batch(captures_dir, tickers, *, fetch_packet, refresh=False, private_root=None):
    """Acquire and pin a small ticker batch; commit each successful ticker to the index.

    Existing captures are validated then skipped by default. Refresh preserves the
    previous immutable file in ``capture_history`` and never replaces longer histories
    with a shorter SDK result.
    """
    requested = _safe_tickers(tickers)
    raw_root = Path(captures_dir)
    if raw_root.is_symlink():
        raise ValueError('Capture directory must not be a symlink')
    root = raw_root.resolve()
    local_root = Path(private_root).resolve() if private_root is not None else Path(__file__).resolve().parents[2] / '.local'
    if not root.is_relative_to(local_root) or any(part.casefold() in {'public', 'static', 'dist'} for part in root.parts):
        raise ValueError('Financial captures must remain under the private .local directory')
    root.mkdir(parents=True, exist_ok=True)
    index_path = root / 'index.json'
    if index_path.exists():
        if index_path.stat().st_size > MAX_INDEX_BYTES:
            raise ValueError('Saved capture index exceeds size bound')
        index = json.loads(index_path.read_text(encoding='utf-8'))
        if index.get('contract') != 'personal-saved-captures-v1' or not isinstance(index.get('captures'), dict):
            raise ValueError('Invalid saved capture index')
    else:
        index = {'contract': 'personal-saved-captures-v1', 'captures': {}}
    index.setdefault('capture_history', {})
    if not isinstance(index['capture_history'], dict):
        raise ValueError('Invalid capture revision history')

    results = []
    errors = {}
    for ticker in requested:
        prior_entry = index['captures'].get(ticker)
        if prior_entry and not refresh:
            try:
                prior, digest = saved_packet(root, ticker)
                results.append(dict(ticker=ticker, status='skipped_existing', sha256=digest,
                    coverage=_coverage(prior)))
            except Exception as exc:
                errors[ticker] = type(exc).__name__
                results.append(dict(ticker=ticker, status='invalid_existing_capture', error=type(exc).__name__))
            continue

        try:
            packet = fetch_packet(ticker)
            _validate_packet(packet, ticker)
            prior = None
            if prior_entry:
                prior, _ = saved_packet(root, ticker)
                previous_quarter_counts = [len([o for o in r.observations if o.frequency == 'quarterly'])
                    for r in prior.reports.values()]
                next_quarter_counts = [len([o for o in r.observations if o.frequency == 'quarterly'])
                    for r in packet.reports.values()]
                previous_annual_counts = [len([o for o in r.observations if o.frequency == 'annual'])
                    for r in prior.reports.values()]
                next_annual_counts = [len([o for o in r.observations if o.frequency == 'annual'])
                    for r in packet.reports.values()]
                if any(old > new for old, new in zip(previous_quarter_counts, next_quarter_counts)) or any(
                        old > new for old, new in zip(previous_annual_counts, next_annual_counts)):
                    results.append(dict(ticker=ticker, status='refresh_deferred_shorter_history',
                        previous_coverage=_coverage(prior), candidate_coverage=_coverage(packet)))
                    continue
                if _fingerprint(prior) == _fingerprint(packet):
                    results.append(dict(ticker=ticker, status='unchanged',
                        sha256=prior_entry['sha256'], coverage=_coverage(prior)))
                    continue

            body = (packet.model_dump_json(indent=2) + '\n').encode('utf-8')
            if len(body) > MAX_PACKET_BYTES:
                raise ValueError('Normalized financial packet exceeds size bound')
            digest = hashlib.sha256(body).hexdigest()
            name = f'{ticker}-vci-{digest}.json'
            _write_immutable(root / name, body)
            entry = dict(file=name, sha256=digest, format='canonical-financial-packet-v1')
            if prior_entry:
                history = index['capture_history'].setdefault(ticker, [])
                if prior_entry not in history:
                    history.append(prior_entry)
            index['captures'][ticker] = entry
            _save_index(root, index)
            results.append(dict(ticker=ticker, status='refreshed' if prior_entry else 'added',
                sha256=digest, coverage=_coverage(packet)))
        except Exception as exc:
            errors[ticker] = type(exc).__name__
            results.append(dict(ticker=ticker, status='failed', error=type(exc).__name__))

    return dict(contract='financial-batch-acquisition-v1', provider='vnstock:VCI',
        requested_tickers=requested, results=results, errors=errors,
        added=sum(row['status'] == 'added' for row in results),
        refreshed=sum(row['status'] == 'refreshed' for row in results),
        unchanged=sum(row['status'] == 'unchanged' for row in results),
        skipped_existing=sum(row['status'] == 'skipped_existing' for row in results))

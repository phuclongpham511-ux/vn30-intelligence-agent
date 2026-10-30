"""Prepare an immutable private saved-data bundle; never acquires or serves data."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from src.services.personal_financials import saved_packet, validated_canonical_packet


def prepare(captures, destination, packet_paths=()):
    source = Path(captures).resolve(strict=True)
    target = Path(destination).resolve()
    if source == target or any(part.casefold() in ('public', 'static') for part in target.parts):
        raise ValueError('Use a separate private capture folder')
    index = json.loads((source / 'index.json').read_text(encoding='utf-8'))
    if index.get('contract') != 'personal-saved-captures-v1' or len(index.get('captures', {})) > 2000:
        raise ValueError('Invalid saved source index')
    pending = {}
    for ticker, entry in sorted(index['captures'].items()):
        saved_packet(source, ticker)  # Validate original hash, identity and bounds.
        data = (source / entry['file']).read_bytes()
        if hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError('Source changed during bundle preparation')
        pending[ticker] = (data, entry.get('format'))
    for path in packet_paths:
        path = Path(path)
        if path.stat().st_size > 32_000_000:
            raise ValueError('Canonical packet exceeds bound')
        data = path.read_bytes()
        packet = validated_canonical_packet(data)
        if packet.ticker in pending:
            raise ValueError('Duplicate issuer; prepare a separate revision bundle')
        pending[packet.ticker] = (data, 'canonical-financial-packet-v1')
    manifest = dict(contract='personal-saved-captures-v1', captures={})
    for ticker, (data, format_name) in pending.items():
        digest = hashlib.sha256(data).hexdigest()
        manifest['captures'][ticker] = dict(file=f'{ticker}-{digest}.json', sha256=digest)
        if format_name:
            manifest['captures'][ticker]['format'] = format_name
    if (target / 'index.json').exists():
        before = json.loads((target / 'index.json').read_text(encoding='utf-8'))
        if before != manifest:
            raise ValueError('Existing bundle differs; use a new revision folder')
    target.mkdir(parents=True, exist_ok=True)
    for ticker, (data, _) in pending.items():
        path = target / manifest['captures'][ticker]['file']
        if path.exists() and path.read_bytes() != data:
            raise ValueError('Existing immutable capture differs')
        if not path.exists():
            path.write_bytes(data)
    (target / 'index.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return dict(contract='financial-activation-bundle-v1', prepared_at=datetime.now(timezone.utc).isoformat(),
        tickers=sorted(pending), provider_requests=0, public_activation=False,
        captures={t: {'sha256': v['sha256'], 'format': v.get('format', 'vci-raw-capture-v1')}
            for t, v in manifest['captures'].items()})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captures', required=True, type=Path)
    parser.add_argument('--destination', required=True, type=Path)
    parser.add_argument('--packet', action='append', default=[], type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.captures, args.destination, args.packet)))

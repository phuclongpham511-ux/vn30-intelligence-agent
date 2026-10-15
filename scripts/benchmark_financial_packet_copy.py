"""Paired isolated replay benchmark; never invokes a provider or opens a database.

Usage: python -m scripts.benchmark_financial_packet_copy --packet saved-packet.json
Captured packets must be labelled by the caller; this is not a live API benchmark.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import time
from src.providers.vnstock import VnstockFundamentalDataProvider
from src.schemas.financials import FinancialPacket


def benchmark(path, samples=11):
    packet=FinancialPacket.model_validate_json(path.read_bytes())
    provider=VnstockFundamentalDataProvider()
    # Seed only the temporary in-process fixture cache, not a running service.
    provider._report_cache[(packet.ticker,int(time.time()//3600))]=packet
    def no_acquisition(*_):raise AssertionError('Replay must not acquire')
    provider._reports=no_acquisition
    times={'baseline_deepcopy':[],'candidate_get_reports':[]}
    for iteration in range(samples):
        order=list(times) if iteration%2==0 else list(reversed(times))
        for name in order:
            start=time.perf_counter()
            clone=packet.model_copy(deep=True) if name=='baseline_deepcopy' else provider.get_reports(packet.ticker)
            times[name].append((time.perf_counter()-start)*1000)
            assert clone==packet and clone is not packet
    medians={name:round(statistics.median(values),3) for name,values in times.items()}
    return {'ticker':packet.ticker,'samples':samples,'observations':sum(len(r.observations) for r in packet.reports.values()),
            'evidence':'REPLAY captured packet; no provider/DB; same facts/provenance; not page-load latency',
            'median_ms':medians,'reduction_percent':round(100*(1-medians['candidate_get_reports']/medians['baseline_deepcopy']),2)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet',type=Path,action='append',required=True)
    parser.add_argument('--samples',type=int,default=11)
    args=parser.parse_args()
    if not 3<=args.samples<=31:parser.error('samples must be between 3 and 31')
    print(json.dumps({'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'results':[benchmark(path,args.samples) for path in args.packet]},indent=2))

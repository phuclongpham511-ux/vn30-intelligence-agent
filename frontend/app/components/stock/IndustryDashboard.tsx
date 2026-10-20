'use client';
import {useState} from 'react';
import {formatFinancialAmount} from '@/lib/financial-format';
import {useLocale} from '@/lib/i18n';
import {industryData,industryLabels,type IndustrySnapshot} from '@/lib/industry-financials';
import {unitDivisor,unitLabels,type AmountUnit} from '@/lib/fundamental-research';

export default function IndustryDashboard({data,allowDemo=false,initialUnit='billions'}:{data:IndustrySnapshot;allowDemo?:boolean;initialUnit?:AmountUnit}){
 const {ui,t,number,percent,language}=useLocale();
 const [metric,setMetric]=useState(data.industry.model==='bank'?'operating_income':'revenue');
 const [unit,setUnit]=useState<AmountUnit>(initialUnit);
 const safe=industryData(data,data.industry.id,data.period,allowDemo);
 const selected=safe.metrics[metric]||Object.values(safe.metrics)[0];
 const format=(value:number|null,metricUnit:string)=>value===null?'—':metricUnit==='fraction'?percent(value):metricUnit==='multiple'?number(value)+'×':formatFinancialAmount(value,unitDivisor[unit],2,number)+' '+ui(unitLabels[unit]);
 return <section className="min-w-0 space-y-5" aria-label={ui('Industry comparison')}>
  {safe.is_fixture&&<p className="stock-note" role="note">{ui('DEMO · Synthetic companies and financial observations. Not market data.')}</p>}
  <header><p className="eyebrow">{ui('Industry comparison')}</p><h2 className="text-xl font-semibold">{language==='vi'?safe.industry.name_vi:safe.industry.name_en}</h2><p className="mt-1 text-xs text-muted-foreground">{safe.period} · {ui(safe.frequency==='annual'?'Annual':safe.frequency==='quarterly'?'Quarterly':'TTM')} · {ui(safe.report_scope==='consolidated'?'Consolidated statements':'Separate statements')}</p></header>
  <p className="stock-note">{ui('Totals cover observed companies only. Each ratio uses a matched company cohort; missing companies are not zero.')}</p>
  <label className="flex items-center gap-2 text-xs">{ui('Amount units')}<select value={unit} onChange={e=>setUnit(e.target.value as AmountUnit)} className="rounded border bg-background p-2">{Object.entries(unitLabels).map(([key,label])=><option key={key} value={key}>{ui(label)}</option>)}</select></label>
  <div className="fundamental-table-scroll" tabIndex={0} role="region" aria-label={ui('Industry metric coverage')}><table className="fundamental-table text-xs"><caption className="sr-only">{ui('Industry metric coverage')}</caption><thead><tr><th>{t('Metric')}</th><th>{ui('Observed aggregate')}</th><th>{ui('Companies covered')}</th><th>{ui('Coverage')}</th></tr></thead><tbody>{Object.entries(safe.metrics).map(([key,m])=><tr key={key}><th scope="row"><button type="button" aria-pressed={metric===key} onClick={()=>setMetric(key)} className="text-left underline underline-offset-4">{ui(industryLabels[key]||key)}</button></th><td>{format(m.value,m.unit)}</td><td>{m.included_companies} / {m.expected_companies}</td><td>{percent(m.coverage)} · {ui(m.status)}</td></tr>)}</tbody></table></div>
  {selected&&<section aria-label={ui('Peer comparison')} className="border-t pt-4"><label className="flex flex-wrap items-center gap-3 text-sm font-medium">{ui('Peer comparison')}<select value={metric} onChange={e=>setMetric(e.target.value)} className="rounded border bg-background px-2 py-2 text-xs">{Object.keys(safe.metrics).map(key=><option key={key} value={key}>{ui(industryLabels[key]||key)}</option>)}</select></label><p className="mt-2 text-xs text-muted-foreground">{ui('Rank orders numerical values, not investment merit. Percentiles use the covered sample.')}</p>
   {!selected.peers.length?<p className="stock-note">{ui('No compatible qualified peers are available for this metric.')}</p>:<div className="fundamental-table-scroll mt-3" tabIndex={0} role="region" aria-label={ui('Peer comparison')}><table className="fundamental-table text-xs"><thead><tr><th>{ui('Company')}</th><th>{ui('Value')}</th><th>{ui('Rank')}</th><th>{ui('Percentile')}</th><th>{ui('Contribution')}</th></tr></thead><tbody>{selected.peers.map(peer=><tr key={peer.ticker}><th scope="row">{safe.is_fixture?peer.ticker:<a href={`/stocks/${encodeURIComponent(peer.ticker)}#stock-fundamentals`} className="text-primary underline">{peer.ticker}</a>}</th><td>{format(peer.value,selected.unit)}</td><td>{peer.rank}</td><td>{percent(peer.percentile)}</td><td>{percent(peer.contribution)}</td></tr>)}</tbody></table></div>}
   <details className="mt-3 text-xs text-muted-foreground"><summary className="cursor-pointer">{ui('Method, sources and exclusions')}</summary><p className="mt-2">{selected.method}</p>{Object.entries(selected.excluded).map(([ticker,reason])=><p key={ticker}>{ticker} · {ui(reason)}</p>)}{selected.peers.map(peer=><details key={peer.ticker} className="mt-2"><summary>{peer.ticker} · {peer.sources.join(', ')}</summary><p className="break-all">{peer.revisions.join(' · ')}</p></details>)}</details>
  </section>}
  <footer className="border-t pt-3 text-xs text-muted-foreground"><p>{safe.taxonomy.name} · {safe.taxonomy.version} · {ui('Membership date')}: {safe.membership_on}</p><p className="mt-1 break-words">{safe.taxonomy.source_reference}</p><details className="mt-2"><summary className="cursor-pointer">{ui('Limitations')}</summary><ul className="mt-2 space-y-1">{safe.limitations.map(l=><li key={l}>{ui(l)}</li>)}</ul></details></footer>
 </section>;
}

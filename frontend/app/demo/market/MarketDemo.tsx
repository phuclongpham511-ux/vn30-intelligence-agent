"use client";
import {useState} from 'react';
import {QuoteMapView} from '../../components/stock/QuoteMap';
import type {LiveBatch,LiveSnapshot} from '@/lib/live-market';
import type {IndustryPreview} from '@/lib/industryPreview';
import {priceStateClass,priceStateLabel,resolvePriceState} from '@/lib/priceState';
import {useLocale} from '@/lib/i18n';

// Fixed clock + invented tickers and categories. No issuer classification or SSI event.
const now=new Date('2026-10-16T07:00:00Z');
const changes=[700,200,0,-200,-700,100,100,100,100];
const stocks=Array.from({length:30},(_,i)=>({symbol:`DEMO${String(i+1).padStart(2,'0')}`,company_name:'DEMO synthetic instrument',exchange:'DEMO'}));
const snapshot=(i:number):LiveSnapshot=>{
  const symbol=stocks[i].symbol,change=changes[i%changes.length];
  return {ticker:symbol,price_unit:'VND',last_price:10000+change,reference_price:10000,change:i===7?null:change,change_percent:i===7?null:change/100,
    source:'DEMO synthetic quote — NOT SSI',trading_date:'2026-10-16',updated_at:now.toISOString(),session:'active',open:null,high:null,low:null,total_volume:null,total_value:null,
    price_limits:{symbol,trading_date:'2026-10-16',effectiveness:'trading_day',reference_price:10000,observed_at:null,source:'DEMO synthetic day-effective limits',unit:'VND',qualification:'qualified',ceiling:10700,floor:9300,ceiling_field:'demo_ceiling',floor_field:'demo_floor'},
    trading_activity:{symbol,trading_date:'2026-10-16',observed_at:now.toISOString(),session:'trading_day',source:'DEMO synthetic matched pair — NOT SSI',scope:'regular_matched',cumulative:true,includes_negotiated_trades:false,
      volume:{value:i===2?0:(i+1)*125000,raw_value:String(i===2?0:(i+1)*125000),field:'demo_matched_volume',unit:'shares',qualification:'qualified'},
      value:{value:i===2?0:(31-i)*1200000000,raw_value:String(i===2?0:(31-i)*1200000000),field:'demo_independent_matched_value',unit:'VND',qualification:'qualified'}}};
};
const industry:IndustryPreview={kind:'synthetic',label:'DEMO',categories:Object.fromEntries(stocks.filter((_,i)=>i%5!==4).map((s,i)=>[s.symbol,{code:i%2?'demo-services':'demo-products',name:i%2?'DEMO Services':'DEMO Products'}]))};

export default function MarketDemo() {
  const {t,ui}=useLocale();
  const [mode,setMode]=useState<'board'|'heatmap'>('board'),[unsupported,setUnsupported]=useState(false);
  const data:LiveBatch={session:'active',as_of:now.toISOString(),items:Object.fromEntries(stocks.map((s,i)=>{
    const row=snapshot(i);
    if(unsupported&&row.trading_activity)for(const metric of [row.trading_activity.volume,row.trading_activity.value]){metric.unit=null;metric.qualification='unverified_units';}
    return [s.symbol,{status:i===5?'stale':i===6?'unavailable':'fresh',snapshot:i===6?null:row}];
  }))};
  const stateCases=Array.from({length:9},(_,i)=>{const row=snapshot(i);const status=i===5?'stale':i===6?'unavailable':'fresh';return resolvePriceState(row.ticker,i===6?null:row,status,now,i===8);});
  return <div className="price-demo"><div className="market-validation">DEMO — SYNTHETIC FIXTURES — NOT LIVE SSI</div>
    <h1>{t('Market Workspace V2.2 · DEMO')}</h1><p className="price-demo-note">{t('Synthetic tickers, independent matched totals and invented categories. Fixed clock: 16 Oct 2026, 14:00 ICT. No real issuer classifications or live events.')}</p>
    <div className="price-state-samples" aria-label="DEMO price states">{stateCases.map(state=><div key={state} data-demo-state={state} className={priceStateClass(state)}><b>{ui(priceStateLabel[state])}</b><span>{state}</span></div>)}</div>
    <div className="price-demo-controls"><button aria-pressed={mode==='board'} onClick={()=>setMode('board')}>{t('Board')}</button><button aria-pressed={mode==='heatmap'} onClick={()=>setMode('heatmap')}>{t('Heatmap')}</button><button aria-pressed={unsupported} onClick={()=>setUnsupported(v=>!v)}>{t(unsupported?'Unqualified units · unavailable':'DEMO qualified-contract values')}</button></div>
    <p className="price-demo-note">{t('Industry DEMO is optional in Board Organization. Production industry grouping remains disabled.')}</p>
    <QuoteMapView stocks={stocks} data={data} scope="page" scopeLabel="DEMO · 30 synthetic instruments" now={now} mode={mode} industryPreview={industry}/>
  </div>;
}

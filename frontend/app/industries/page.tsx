'use client';
import {useEffect,useState} from 'react';
import {useLocale} from '@/lib/i18n';
import {industryData,observedIndustryData,type IndustryDirectory,type IndustrySnapshot,type ObservedIndustryDirectory,type ObservedIndustryPeers} from '@/lib/industry-financials';
import IndustryDashboard,{ObservedIndustryDashboard} from '../components/stock/IndustryDashboard';

export default function IndustryPage(){
 const {ui,language}=useLocale();
 const [directory,setDirectory]=useState<IndustryDirectory|ObservedIndustryDirectory|null>(null),[data,setData]=useState<IndustrySnapshot|ObservedIndustryPeers|null>(null);
 const [id,setId]=useState(''),[period,setPeriod]=useState(String(new Date().getFullYear()-1)),[frequency,setFrequency]=useState<'annual'|'quarterly'|'ttm'>('annual');
 const [membership,setMembership]=useState(`${new Date().getFullYear()-1}-12-31`),[status,setStatus]=useState('loading'),[attempt,setAttempt]=useState(0);
 const observed=directory?.contract==='observed-industry-directory-v1';
 useEffect(()=>{const controller=new AbortController();fetch('/api/financial-intelligence/industries',{signal:controller.signal}).then(async r=>{
  if(!r.ok)throw Error();const d=await r.json();
  if(!['industry-directory-v1','observed-industry-directory-v1'].includes(d.contract)||!Array.isArray(d.industries)||d.industries.length>200)throw Error();
  if(d.contract==='observed-industry-directory-v1'&&(d.display_scope!=='personal_research'||d.public_display_eligible!==false||d.historical_aggregation_enabled!==false||d.taxonomy_version!==null||d.industries.some((i:ObservedIndustryDirectory['industries'][number])=>!/^\d{1,16}$/.test(i.id)||!i.label||!Number.isInteger(i.members)||!Number.isInteger(i.saved_companies)||i.saved_companies<0||i.saved_companies>i.members)))throw Error();
  setDirectory(d);setId(d.industries[0]?.id||'');setStatus('ready');
  const context=new URLSearchParams(window.location.search),company=context.get('ticker'),selectedPeriod=context.get('period'),selectedFrequency=context.get('frequency');
  if(selectedFrequency&&['annual','quarterly','ttm'].includes(selectedFrequency)&&selectedPeriod&&/^\d{4}(?:-Q[1-4])?$/.test(selectedPeriod)){setFrequency(selectedFrequency as typeof frequency);setPeriod(selectedPeriod);}
  if(d.contract==='observed-industry-directory-v1'&&company&&/^[A-Z0-9]{1,20}$/.test(company)){
   const q=new URLSearchParams({period:selectedPeriod||period,frequency:selectedFrequency||frequency});
   const response=await fetch(`/api/personal-research/peers/${company}?${q}`,{signal:controller.signal});
   if(response.ok){const value=await response.json();if(value.contract==='observed-industry-peers-v1'&&d.industries.some((i:ObservedIndustryDirectory['industries'][number])=>i.id===value.industry?.id)){setId(value.industry.id);}}
  }
 }).catch(()=>{if(!controller.signal.aborted)setStatus('error');});return()=>controller.abort();},[attempt]);
 useEffect(()=>{
  if(!id)return;
  if(!(frequency==='annual'?/^\d{4}$/:/^\d{4}-Q[1-4]$/).test(period)||!observed&&!/^\d{4}-\d{2}-\d{2}$/.test(membership)){setData(null);setStatus('input');return;}
  const controller=new AbortController();setStatus('loading');setData(null);const query=new URLSearchParams({period,frequency,...(observed?{}:{membership_on:membership})});
  fetch(`/api/financial-intelligence/industries/${encodeURIComponent(id)}?${query}`,{signal:controller.signal}).then(async r=>{if(!r.ok)throw Error();const value=await r.json();setData(observed?observedIndustryData(value,id,period,true):industryData(value,id,period));setStatus('ready');}).catch(()=>{if(!controller.signal.aborted)setStatus('error');});return()=>controller.abort();
 },[id,period,frequency,membership,attempt,observed]);
 return <main className="mx-auto min-w-0 max-w-6xl space-y-5 p-4 md:p-6"><h1 className="text-2xl font-semibold">{ui('Industry comparison')}</h1><a href="/" className="text-xs text-primary underline">{ui('Market')}</a>
  {directory?.industries.length?<div className="flex flex-wrap gap-3 text-xs"><label>{ui('Industry')}<select className="ml-2 rounded border bg-background p-2" value={id} onChange={e=>setId(e.target.value)}>{directory.industries.map(i=><option key={i.id} value={i.id}>{'label'in i?`${i.label} · ${i.saved_companies}/${i.members}`:language==='vi'?i.name_vi:i.name_en}</option>)}</select></label><label>{ui('Reporting frequency')}<select className="ml-2 rounded border bg-background p-2" value={frequency} onChange={e=>{const next=e.target.value as typeof frequency;setFrequency(next);setPeriod(p=>next==='annual'?p.slice(0,4):p.includes('-Q')?p:p+'-Q4');}}>{(['annual','quarterly','ttm'] as const).map(f=><option key={f} value={f}>{ui(f==='annual'?'Annual':f==='quarterly'?'Quarterly':'TTM')}</option>)}</select></label><label>{ui('Reporting period')}<input className="ml-2 w-28 rounded border bg-background p-2" value={period} maxLength={7} onChange={e=>setPeriod(e.target.value)}/></label>{!observed&&<label>{ui('Membership date')}<input className="ml-2 rounded border bg-background p-2" type="date" value={membership} onChange={e=>setMembership(e.target.value)}/></label>}</div>:null}
  {status==='input'?<p role="status">{ui('Enter a valid reporting period.')}</p>:status==='loading'?<p role="status">{ui('Loading industry observations…')}</p>:status==='error'?<div role="alert"><p>{ui('Industry observations are unavailable. Please retry.')}</p><button className="mt-2 underline" onClick={()=>setAttempt(n=>n+1)}>{ui('Retry')}</button></div>:!directory?.industries.length?<p className="stock-note">{ui('Verified industry classification is not available. Company financial research remains available from each stock.')}</p>:data?.contract==='observed-industry-peers-v1'?<ObservedIndustryDashboard key={`${id}:${period}:${frequency}`} data={data}/>:data?<IndustryDashboard key={id} data={data}/>:null}
 </main>;
}

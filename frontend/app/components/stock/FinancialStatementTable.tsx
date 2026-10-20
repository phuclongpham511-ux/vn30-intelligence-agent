"use client";
import {useState} from 'react';
import {useLocale} from '@/lib/i18n';
import type {FinancialStatementPeriod} from '@/lib/types';
import {unitDivisor,unitLabels,consolidationLabel,type AmountUnit} from '@/lib/fundamental-research';
import {statementHierarchy} from '@/lib/financial-statement-rows';

export default function FinancialStatementTable({periods,unit,label}:{periods:FinancialStatementPeriod[];unit:AmountUnit;label:string}){
  const {language,t,ui,number}=useLocale();
  const [collapsed,setCollapsed]=useState<Set<string>>(()=>new Set());
  const hierarchy=statementHierarchy(periods,collapsed),lines=hierarchy.filter(r=>!r.hidden);
  return <><p className="mb-3 text-xs text-muted-foreground">{t('Reported source statements. Conflicting labels are withheld, not corrected by inference.')}{' '}{t('Unqualified reporting bases remain unavailable; raw source amounts are evidence only.')}</p>
    <div className="financial-statement-toolbar"><p>{ui(label)} · {ui(unitLabels[unit])}</p>{hierarchy.some(row=>row.expandable)&&<div role="group" aria-label={t('Statement hierarchy')}><button type="button" onClick={()=>setCollapsed(new Set())}>{t('Expand all')}</button><button type="button" onClick={()=>setCollapsed(new Set(hierarchy.filter(row=>row.expandable).map(row=>row.line.code)))}>{t('Collapse groups')}</button></div>}</div>
    <div className="fundamental-table-scroll" role="region" tabIndex={0} aria-label={ui(label)}><table className="fundamental-table text-xs"><caption className="sr-only">{ui(label)} · {ui(unitLabels[unit])}</caption>
      <thead><tr><th scope="col">{t('Metric')}</th>{periods.map(period=><th scope="col" key={period.period}>{period.period}<span className="mt-1 block text-[10px] font-normal text-muted-foreground">{ui(period.basis==='point_in_time'?'Period-end balance':period.basis==='annual'?'Annual':period.basis==='standalone'?'Standalone quarter':period.basis==='ytd'?'YTD':'Unknown basis')} · {ui(consolidationLabel(period.consolidation))}</span></th>)}</tr></thead>
      <tbody>{lines.map(({line,depth,expandable})=><tr key={line.code} className={expandable?'financial-statement-group':undefined}><th scope="row"><span style={{paddingInlineStart:depth*12}} className="block">{expandable?<button type="button" aria-expanded={!collapsed.has(line.code)} onClick={()=>setCollapsed(before=>{const next=new Set(before);if(next.has(line.code))next.delete(line.code);else next.add(line.code);return next;})} className="rounded text-left focus-visible:outline-2 focus-visible:outline-ring"><span aria-hidden="true">{collapsed.has(line.code)?'▸':'▾'} </span>{language==='vi'?line.name_vi:line.name_en}</button>:language==='vi'?line.name_vi:line.name_en}</span><span className="mt-1 block text-[10px] font-normal text-muted-foreground">{line.code}{line.unit==='VND/share'?' · '+t('VND/share'):''}</span></th>{periods.map(period=>{const item=period.items.find(value=>value.code===line.code);return <td key={period.period}>{item?.value==null?'—':number(item.value/(item.unit==='VND'?unitDivisor[unit]:1),item.unit==='VND'&&unit==='vnd'?0:2)}{item&&item.semantic_status!=='reported'&&<details className="mt-1 text-[10px] text-muted-foreground"><summary className="cursor-pointer">{t(item.semantic_status==='conflicted'?'Source conflict':'UNQUALIFIED')}</summary><p className="mt-2">{t('Unqualified raw amount')}: {number(item.raw_value)} {item.unit}</p>{item.source_labels?.map((label,index)=><p key={index}>{label.en_name} · {label.name} · {label.parent}</p>)}</details>}</td>;})}</tr>)}</tbody>
    </table></div></>;
}

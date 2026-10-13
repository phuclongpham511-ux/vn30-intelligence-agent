"use client";
import {useLocale} from '@/lib/i18n';
import type {FinancialStatementPeriod} from '@/lib/types';
import {unitDivisor,unitLabels,type AmountUnit} from '@/lib/fundamental-research';

export default function FinancialStatementTable({periods,unit,label}:{periods:FinancialStatementPeriod[];unit:AmountUnit;label:string}){
  const {language,t,ui,number}=useLocale();
  const lines=[...new Map(periods.flatMap(period=>period.items.map(line=>[line.code,line] as const))).values()];
  return <><p className="mb-3 text-xs text-muted-foreground">{t('Reported source statements. Conflicting labels are withheld, not corrected by inference.')}</p>
    <div className="fundamental-table-scroll" role="region" tabIndex={0} aria-label={ui(label)}><table className="fundamental-table text-xs"><caption className="sr-only">{ui(label)} · {ui(unitLabels[unit])}</caption>
      <thead><tr><th scope="col">{t('Metric')}</th>{periods.map(period=><th scope="col" key={period.period}>{period.period}<span className="mt-1 block text-[10px] font-normal text-muted-foreground">{ui(period.basis==='point_in_time'?'Period-end balance':period.basis==='annual'?'Annual':period.basis==='standalone'?'Standalone quarter':period.basis==='ytd'?'YTD':'Unknown basis')}</span></th>)}</tr></thead>
      <tbody>{lines.map(line=><tr key={line.code}><th scope="row"><span>{language==='vi'?line.name_vi:line.name_en}</span><span className="mt-1 block text-[10px] font-normal text-muted-foreground">{line.code}{line.unit==='VND/share'?' · '+t('VND/share'):''}</span></th>{periods.map(period=>{const item=period.items.find(value=>value.code===line.code);return <td key={period.period}>{item?.value==null?'—':number(item.value/(item.unit==='VND'?unitDivisor[unit]:1),item.unit==='VND'&&unit==='vnd'?0:2)}{item?.semantic_status==='conflicted'&&<details className="mt-1 text-[10px] text-muted-foreground"><summary className="cursor-pointer">{t('Source conflict')}</summary><p className="mt-2">{t('Unqualified raw amount')}: {number(item.raw_value)} VND</p>{item.source_labels?.map((label,index)=><p key={index}>{label.en_name} · {label.name} · {label.parent}</p>)}</details>}</td>;})}</tr>)}</tbody>
    </table></div></>;
}

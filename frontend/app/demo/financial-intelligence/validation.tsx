'use client';
import {useState} from 'react';
import fixtures from '../../../tests/fixtures/financial-intelligence-demo.json';
import type {FinancialPanel,FundamentalResearch} from '@/lib/types';
import type {IndustrySnapshot} from '@/lib/industry-financials';
import {financialEngineData} from '@/lib/financial-engine-data';
import {useLocale} from '@/lib/i18n';
import FinancialAnalysisPanel from '../../components/stock/FinancialAnalysisPanel';
import IndustryDashboard from '../../components/stock/IndustryDashboard';
export default function FinancialValidation(){
 const {ui}=useLocale();
 const [model,setModel]=useState<'nonfinancial'|'bank'>('nonfinancial'),[frequency,setFrequency]=useState<'annual'|'quarterly'>('annual');
 const view=financialEngineData(fixtures[model][frequency] as unknown as FundamentalResearch,'ABC',frequency,true);
 const keys:FinancialPanel['key'][]=['cashflow','profitability',model==='bank'?'bank_funding':'liquidity'];
 return <main className="mx-auto max-w-6xl space-y-6 p-4 md:p-6"><h1 className="text-xl font-semibold">{ui('DEMO · Synthetic companies and financial observations. Not market data.')}</h1><div className="flex flex-wrap gap-3"><select aria-label={ui('Company')} className="rounded border bg-background p-2" value={model} onChange={e=>setModel(e.target.value as typeof model)}><option value="nonfinancial">{ui('Non-financial company')}</option><option value="bank">{ui('Bank')}</option></select><select aria-label={ui('Reporting frequency')} className="rounded border bg-background p-2" value={frequency} onChange={e=>setFrequency(e.target.value as typeof frequency)}><option value="annual">{ui('Annual')}</option><option value="quarterly">{ui('Quarterly')}</option></select></div><div className="grid min-w-0 gap-5 lg:grid-cols-2">{keys.map(key=><FinancialAnalysisPanel key={`${model}:${frequency}:${key}`} kind={key} panel={view.research_panels?.find(p=>p.key===key)} unit="vnd" isFixture/>)}</div><IndustryDashboard data={fixtures.industry as IndustrySnapshot} allowDemo initialUnit="vnd"/></main>;
}

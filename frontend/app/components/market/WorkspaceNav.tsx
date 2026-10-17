"use client";
import Link from 'next/link';
import {useLocale} from '@/lib/i18n';
export type WorkspaceView='overview'|'board'|'heatmap';
export function workspaceView(hash:string):WorkspaceView{return hash==='#market-board'?'board':hash==='#market-heatmap'?'heatmap':'overview';}
export default function WorkspaceNav({view,research=false}:{view?:WorkspaceView;research?:boolean}){
  const {t}=useLocale();
  return <nav className="market-nav" aria-label={t('Market workspace')}>
    {(['overview','board','heatmap'] as const).map(v=><a key={v} href={'/#market-'+v} aria-current={!research&&view===v?'page':undefined}>{t(v==='overview'?'Overview':v==='board'?'Market board':'Heatmap')}</a>)}
    {research?<span aria-current="page">{t('Stock research')}</span>:<Link href="#market-search" onClick={event=>{event.preventDefault();document.querySelector<HTMLInputElement>('[aria-label="Search ticker"], [data-market-search] input')?.focus();}}>{t('Stock research')}</Link>}
  </nav>;
}

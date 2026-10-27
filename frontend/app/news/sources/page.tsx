"use client";
import {useState} from 'react';
import {useLocale} from '@/lib/i18n';
import SourceCoverage from '../../components/news/SourceCoverage';
import {Button} from '../../components/ui/button';
export default function NewsSources(){
  const {t}=useLocale();const [attempt,setAttempt]=useState(0);
  return <div className="page-stack"><h1>{t('Source health')}</h1><SourceCoverage attempt={attempt}/><Button variant="outline" onClick={()=>setAttempt(value=>value+1)}>{t('Refresh')}</Button></div>;
}

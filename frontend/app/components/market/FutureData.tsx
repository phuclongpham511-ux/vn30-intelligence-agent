"use client";
import {useLocale} from '@/lib/i18n';
export default function FutureData(){const {t}=useLocale();return <details className="market-future"><summary>{t('Future data · not active')}<span>{t('Inspect requirements')} ↗</span></summary><div><p>{t('Sector classification and sector performance need qualified membership and methodology.')}</p><p>{t('Whole-market breadth, cumulative session volume and capitalization sizing are unavailable in this view.')}</p><p>{t('No strength, sentiment or institutional money-flow indicator is inferred.')}</p></div></details>;}

"use client";
import {useEffect,useState} from 'react';
import {useParams} from 'next/navigation';
import Link from 'next/link';
import {useLocale} from '@/lib/i18n';
import type {NewsArticle} from '@/lib/news';
import ArticleRow from '@/app/components/news/ArticleRow';

export default function StoryEvidence(){
  const {id}=useParams<{id:string}>();const {t}=useLocale();
  const [articles,setArticles]=useState<NewsArticle[]|null>(null);const [error,setError]=useState(false);
  useEffect(()=>{const controller=new AbortController();setArticles(null);setError(false);
    fetch('/api/news/stories/'+encodeURIComponent(id),{signal:controller.signal,cache:'no-store'}).then(async r=>{if(!r.ok)throw Error();const data=await r.json();if(!controller.signal.aborted)setArticles(data.articles);}).catch(()=>{if(!controller.signal.aborted)setError(true);});return()=>controller.abort();
  },[id]);
  return <div className="page-stack"><Link href="/news" className="text-sm text-primary">← {t('News')}</Link><div><h1>{t('Story evidence')}</h1><p className="mt-2 text-sm text-muted-foreground">{t('Headline association; price movement does not establish news impact.')}</p></div>
    {error?<p role="alert">{t('News is temporarily unavailable.')}</p>:!articles?<p role="status">{t('Loading news…')}</p>:<section className="panel px-4"><p className="py-3 text-xs text-muted-foreground">{t('Original publisher evidence')}</p>{articles.map(a=><ArticleRow key={a.id} article={a} requireImage={false}/>)}</section>}
  </div>;
}

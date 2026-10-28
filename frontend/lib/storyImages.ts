import {safeExternalUrl} from './presentation.ts';
import type {NewsArticle} from './news.ts';
export function storyImages(item:{representative_article:NewsArticle;articles:NewsArticle[];thumbnail_url?:string|null}) {
  const representative=item.representative_article;
  const members=[representative,...item.articles.filter(row=>row.id!==representative.id).sort((a,b)=>a.id.localeCompare(b.id))];
  const images=members.map(row=>safeExternalUrl(row.thumbnail_url||null)).filter((url):url is string=>!!url);
  const preferred=safeExternalUrl(item.thumbnail_url||null);
  return [...new Set([safeExternalUrl(representative.thumbnail_url||null),preferred&&images.includes(preferred)?preferred:null,...images].filter((url):url is string=>!!url))];
}

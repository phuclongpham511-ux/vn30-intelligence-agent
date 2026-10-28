"use client";
import {useLocale} from "@/lib/i18n";
import { ExternalLink, Newspaper } from "lucide-react";
import type { News } from "@/lib/types";
import { safeExternalUrl } from "@/lib/presentation";
import { Badge } from "../ui/badge";
import NewsThumbnail from "../news/NewsThumbnail";
export default function NewsFeed({ items }: { items: News[] }) {
  const {t,ui,date:localDate}=useLocale();
  const sample = items.some(item => item.is_fixture);
  return <section className="panel overflow-hidden">
    <div className="flex items-center justify-between border-b px-5 py-4"><div><h2>{ui(sample ? "Sample News Feed" : "News")}</h2><p className="mt-1 text-xs text-muted-foreground">{ui(sample ? "Live news ingestion is not connected yet." : "Headlines from the current source.")}</p></div><Newspaper size={18} className="text-muted-foreground"/></div>
    {!items.length ? <div className="p-8 text-center text-sm text-muted-foreground">{t("No news is available from the current source.")}</div> : items.map(item => {
      const url = safeExternalUrl(item.url);
      return <NewsThumbnail key={item.id} images={[(item as News & {thumbnail_url?:string|null}).thumbnail_url]}>{image=><article className="px-5 py-5 [&+article]:border-t">
        <div className="flex items-start gap-4">{image}<div className="min-w-0 flex-1">
        <div className="mb-2 flex flex-wrap items-center gap-2.5 text-[10px] text-muted-foreground"><span className="font-medium uppercase tracking-wide">{item.source}</span><span>·</span><time dateTime={item.published_at}>{localDate(item.published_at)}</time>{item.is_fixture && <Badge variant="outline" className="rounded px-1.5 py-0 text-[9px] font-normal text-muted-foreground">{t("FIXTURE")}</Badge>}</div>
        <h3 className="text-sm font-medium">{url ? <a href={url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 hover:text-primary">{item.title}<ExternalLink size={13}/><span className="sr-only"> {t("Opens in a new tab")}</span></a> : item.title}</h3>
        {item.summary_or_content && <p className="mt-2 max-w-3xl text-xs leading-6 text-muted-foreground">{item.summary_or_content}</p>}
        {item.is_fixture && <p className="mt-3 text-[10px] text-muted-foreground">{t("Demonstration content · Not an actual company announcement")}</p>}
        </div></div>
      </article>}</NewsThumbnail>;
    })}
  </section>;
}

"use client";
import { useCallback, useEffect, useState } from "react";
import { Button } from "../components/ui/button";

type Article = {
  id: string; title: string; url: string; source_name: string; published_at: string | null;
  first_seen_at: string; topics: string[]; tickers: string[]; sectors: string[];
};
type Story = { story: { id: string; representative_title: string; source_count: number }; articles: Article[] };
type Topic = { topic: string; story_count: number; source_count: number; mention_velocity: number };
type Data = { top: Story[]; topics: Topic[]; latest: Article[]; global: Article[] };

function Time({ article }: { article: Article }) {
  const date = article.published_at || article.first_seen_at;
  return <span>{!article.published_at && "First seen "}<time dateTime={date}>{new Date(date).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" })}</time></span>;
}
function ArticleRow({ article }: { article: Article }) {
  return <article className="border-b py-4 last:border-0">
    <div className="mb-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground"><span>{article.source_name}</span><Time article={article}/></div>
    <h3 className="text-sm font-medium leading-6">{article.title}</h3>
    <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">{[...article.topics, ...article.tickers, ...article.sectors].filter((v, i, arr) => arr.indexOf(v) === i).map(tag => <span key={tag} className="rounded border px-2 py-0.5">{tag}</span>)}</div>
    <a className="mt-3 inline-block text-xs text-primary underline-offset-4 hover:underline focus-visible:outline" href={article.url} target="_blank" rel="noopener noreferrer">Read original ↗</a>
  </article>;
}
export default function NewsPage() {
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selectedTopic, setSelectedTopic] = useState("");
  const load = useCallback(async (signal?: AbortSignal) => {
    setLoading(true); setError(false);
    try {
      const paths = ["top?limit=6", "topics/trending?limit=10", `latest?limit=30${selectedTopic ? `&topic=${encodeURIComponent(selectedTopic)}` : ""}`, "latest?category=GLOBAL&limit=12"];
      const results = await Promise.all(paths.map(async path => {
        const response = await fetch(`/api/news/${path}`, { signal, cache: "no-store" });
        if (!response.ok) throw new Error("News unavailable");
        return response.json();
      }));
      if (!signal?.aborted) setData({ top: results[0], topics: results[1], latest: results[2], global: results[3] });
    } catch {
      if (!signal?.aborted) setError(true);
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, [selectedTopic]);
  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    const timer = setInterval(() => void load(controller.signal), 15 * 60 * 1000);
    return () => { controller.abort(); clearInterval(timer); };
  }, [load]);
  return <div className="page-stack">
    <div className="flex items-start justify-between gap-4"><div><div className="eyebrow mb-3">News</div><h1>Market Today</h1><p className="mt-2 text-sm text-muted-foreground">Market-wide reporting from Vietnam and global markets.</p></div><Button variant="outline" disabled={loading} onClick={() => void load()}>Refresh</Button></div>
    {error && <div role="alert" className="rounded border p-4 text-sm">News is temporarily unavailable. {data && "Previously loaded headlines are shown below."} <button className="ml-2 text-primary underline" onClick={() => void load()}>Retry</button></div>}
    {loading && !data && <p role="status" className="py-8 text-sm text-muted-foreground">Loading news…</p>}
    {data && <>
      <section aria-labelledby="top-stories"><h2 id="top-stories">Top Stories</h2><p className="mt-1 text-xs text-muted-foreground">Ranked by independent sources, story activity and recency.</p>
        {!data.top.length && <p className="py-6 text-sm text-muted-foreground">No recent stories available.</p>}
        <div className="mt-3 grid gap-x-8 md:grid-cols-2">{data.top.map(({ story, articles }) => <article key={story.id} className="border-b py-4"><h3 className="font-medium leading-6">{story.representative_title}</h3><div className="mt-2 text-xs text-muted-foreground">{story.source_count} independent {story.source_count === 1 ? "source" : "sources"}</div><details className="mt-3 text-xs"><summary className="cursor-pointer text-primary">View reporting</summary>{articles.map(article => <ArticleRow key={article.id} article={article}/>)}</details></article>)}</div>
      </section>
      <section aria-labelledby="trending"><h2 id="trending">Trending Topics</h2><p className="mt-1 text-xs text-muted-foreground">Increasing coverage over the last six hours compared with the preceding six hours.</p><div className="mt-4 flex flex-wrap gap-2">{data.topics.map(topic => <button key={topic.topic} aria-pressed={selectedTopic === topic.topic} onClick={() => setSelectedTopic(selectedTopic === topic.topic ? "" : topic.topic)} className={`rounded border px-3 py-2 text-left text-sm focus-visible:outline ${selectedTopic === topic.topic ? "border-primary text-primary" : "hover:bg-muted"}`}><span className="font-medium">{topic.topic}</span><span className="mt-1 block text-xs text-muted-foreground">{topic.story_count} stories · {topic.source_count} sources</span></button>)}</div>{!data.topics.length && <p className="py-4 text-sm text-muted-foreground">No topics with increasing coverage yet.</p>}</section>
      <div className="grid gap-8 xl:grid-cols-[2fr_1fr]">
        <section aria-labelledby="latest"><div className="flex items-center justify-between"><h2 id="latest">Latest News</h2>{selectedTopic && <button className="text-xs text-primary" onClick={() => setSelectedTopic("")}>Clear {selectedTopic} filter</button>}</div>{data.latest.map(article => <ArticleRow key={article.id} article={article}/>)}{!data.latest.length && <p className="py-6 text-sm text-muted-foreground">No recent news matches this view.</p>}</section>
        <section aria-labelledby="global"><h2 id="global">Global Markets</h2><p className="mt-1 text-xs text-muted-foreground">Rates, currencies, commodities, trade and global business.</p>{data.global.map(article => <ArticleRow key={article.id} article={article}/>)}{!data.global.length && <p className="py-6 text-sm text-muted-foreground">No recent global market news available.</p>}</section>
      </div>
    </>}
  </div>;
}

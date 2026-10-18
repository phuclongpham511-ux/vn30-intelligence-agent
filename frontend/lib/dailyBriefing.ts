import {isUnread, reviewUpdates, uniqueUpdates, type AttentionUpdate, type Intelligence, type WatchlistState} from './watchlist.ts';
import {safeExternalUrl} from './presentation.ts';
import type {NewsArticle} from './news.ts';
import type {CommunityItem} from './community.ts';

export type BriefingItem = {
  id: string; item: AttentionUpdate; symbols: string[];
  source: string; time: string; published: boolean; url: string;
  sourceStatus: 'healthy'|'stale'|'error'|'not_attempted'|'disabled'|'unknown';
  sourceCheckedAt: string|null; corrected: boolean; fixture: boolean;
  references: {symbol:string; item:AttentionUpdate}[];
};

// Presentation only: preserve source time, read-layer associations and receipt
// semantics. No new event detector, numerical score or acquisition is involved.
export function dailyBriefing(data: Intelligence, state: WatchlistState) {
  const groups = new Map<string, BriefingItem>();
  const conflicts = new Set<string>();
  let incomplete = data.stocks.length !== state.symbols.length;
  const sources = [...data.news_sources, ...data.community_sources];
  if (['news', 'community'].some(kind => !(kind === 'news' ? data.news_sources : data.community_sources).some(s => s.enabled)) ||
      sources.some(s => s.enabled && s.status !== 'healthy')) incomplete = true;

  for (const row of data.stocks) {
    if (!state.symbols.includes(row.symbol)) continue;
    if (row.status !== 'ready') { incomplete = true; continue; }
    for (const kind of ['news', 'community'] as const) {
      const page = row[kind];
      if (!page) { incomplete = true; continue; }
      if (page.has_more || page.truncated) incomplete = true;
      for (const item of uniqueUpdates(page.items)) {
        if (!isUnread(state, row.symbol, item)) continue;
        const article = kind === 'news' && Array.isArray(item.evidence) ? (item.evidence as NewsArticle[])[0] : null;
        const discussion = kind === 'community' ? item.evidence as CommunityItem : null;
        const source = article ? data.news_sources.find(s => s.name === article.source_name) :
          discussion ? data.community_sources.find(s => s.source_id === discussion.source_id) : null;
        const url = safeExternalUrl(item.url);
        const published = article?.published_at || discussion?.published_at || null;
        const time = published || item.occurred_at;
        // Unknown or contradictory attribution must not become trusted briefing.
        if (!source || !source.enabled || !url || !Number.isFinite(Date.parse(time)) ||
            Date.parse(time) > Date.parse(data.as_of) ||
            (article && (article.title !== item.title || safeExternalUrl(article.url) !== url)) ||
            (!article && !discussion)) { incomplete = true; continue; }
        const previous = groups.get(item.id);
        if (previous && (previous.item.revision !== item.revision || previous.item.title !== item.title ||
            previous.time !== time || previous.url !== url)) { conflicts.add(item.id); incomplete = true; continue; }
        const reference = {symbol: row.symbol, item};
        const corrected = !!state.receipts?.[row.symbol]?.[item.id];
        if (previous) {
          previous.symbols.push(row.symbol); previous.references.push(reference);
          previous.corrected ||= corrected;
        } else groups.set(item.id, {id:item.id, item, symbols:[row.symbol], references:[reference],
          source:source.name, time, published:!!published, url, sourceStatus:source.status,
          sourceCheckedAt:source.last_success_at, corrected, fixture:!!discussion?.is_fixture});
      }
    }
  }
  const all = [...groups.values()].filter(item => !conflicts.has(item.id))
    .sort((a,b) => Date.parse(b.time)-Date.parse(a.time) || a.id.localeCompare(b.id));
  return {items:all.slice(0,3), total:all.length, incomplete};
}

// Acknowledge exactly the displayed revisions, never hidden items or a removed
// stock. A concurrent explicit review in another tab takes precedence.
export function reviewBriefingItem(current:WatchlistState, rendered:WatchlistState, entry:Pick<BriefingItem,'references'>, at?:string) {
  let next = current;
  for (const {symbol,item} of entry.references) {
    if (!current.symbols.includes(symbol) ||
        JSON.stringify(current.receipts?.[symbol]?.[item.id]) !== JSON.stringify(rendered.receipts?.[symbol]?.[item.id])) continue;
    next = reviewUpdates(next,symbol,[item],at);
  }
  return next;
}

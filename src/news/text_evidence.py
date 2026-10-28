"""Append-only feed text receipts; corrections never reuse a previous title's text."""
from sqlmodel import select
from src.news.models import NewsTextReceipt
from src.news.normalization import digest, canonical_url, clean_title


def retain_text(session, article, item, now):
    # A same-title dedup can retain another URL's article row. Such metadata is
    # not evidence from the displayed article. Native corrections are normalized
    # by the writer before this check; cross-publisher matches never supply text.
    if canonical_url(item.url) != article.canonical_url or clean_title(item.title) != article.title:
        return False
    text = (getattr(item, 'text', None) or '').strip()[:12000]
    origin = getattr(item, 'text_provenance', None)
    if not text or origin not in ('rss:content', 'rss:description', 'atom:content', 'atom:summary'):
        return False
    text_hash = digest(text)
    previous = session.exec(select(NewsTextReceipt).where(NewsTextReceipt.article_id == article.id)
        .order_by(NewsTextReceipt.sequence.desc(), NewsTextReceipt.observed_at.desc(), NewsTextReceipt.id.desc()).limit(1)).first()
    if previous and (previous.article_title, previous.canonical_url, previous.provenance, previous.text_hash) == (article.title, article.canonical_url, origin, text_hash):
        return False
    sequence = previous.sequence + 1 if previous else 1
    identity = digest('|'.join((article.id, str(sequence), article.title, article.canonical_url, origin, text_hash)))
    session.add(NewsTextReceipt(id=identity, article_id=article.id, article_title=article.title,
        canonical_url=article.canonical_url, text=text, text_hash=text_hash,
        provenance=origin, observed_at=now, sequence=sequence))
    return True


def receipt_map(session, articles, *, now=None):
    if not articles:
        return {}
    result = {}
    # Bounded chunks avoid SQLite's parameter ceiling on a large cache rebuild.
    identities = {a.id: a for a in articles}
    ids = list(identities)
    for offset in range(0, len(ids), 500):
        query = select(NewsTextReceipt).where(NewsTextReceipt.article_id.in_(ids[offset:offset+500]))
        if now is not None:
            query = query.where(NewsTextReceipt.observed_at <= now)
        receipts = session.exec(query.order_by(NewsTextReceipt.sequence.desc(), NewsTextReceipt.observed_at.desc(), NewsTextReceipt.id.desc())).all()
        for receipt in receipts:
            article = identities[receipt.article_id]
            if receipt.article_title == article.title and receipt.canonical_url == article.canonical_url:
                result.setdefault(article.id, receipt)
    return result

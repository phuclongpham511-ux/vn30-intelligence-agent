"""Bounded lexical search of the existing publisher projection; no acquisition."""
from src.news.normalization import normalized
from src.news.tagging import contains, AMBIGUOUS_LANGUAGE


def prepare_query(query, stocks, aliases):
    phrase = normalized((query or '').strip()[:120])
    symbols = {stock.symbol for stock in stocks}
    owners = {}
    for stock in stocks:
        for name in [stock.company_name, getattr(stock, 'display_name_en', None), *aliases.get(stock.symbol, [])]:
            if name:
                owners.setdefault(normalized(name), set()).add(stock.symbol)
    exact = phrase.upper() if phrase.upper() in symbols else None
    resolved = {exact} if exact else owners.get(phrase, set())
    if len(resolved) > 1:  # Shared names cannot manufacture an issuer identity.
        resolved = set()
    return phrase, resolved, bool(exact and phrase in AMBIGUOUS_LANGUAGE)


def match_score(prepared, article, qualified, supplied_text=''):
    phrase, resolved, ambiguous = prepared
    if not phrase:
        return 1
    if resolved & qualified:
        return 100
    if ambiguous:
        return 0
    title, body = normalized(article.title), normalized(supplied_text)
    if contains(title, phrase):
        return 40
    tokens = phrase.split()
    if all(contains(title, word) for word in tokens):
        return 30
    if phrase in {normalized(value) for value in [*article.topics, *article.sectors]}:
        return 25
    if contains(body, phrase):
        return 20
    # AND matching, not an OR over broad terms that swamps a specific request.
    return 10 if all(contains(title+' '+body, word) for word in tokens) else 0

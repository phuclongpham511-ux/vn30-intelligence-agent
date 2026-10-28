"""Deterministic, configurable dictionaries; stock universe comes from the stock table."""
from dataclasses import dataclass
import re
from src.news.normalization import normalized

TOPICS = {
    'Equities': ['chung khoan', 'vn index', 'vnindex', 'co phieu', 'stock market', 'stocks', 'equities', 'wall street', 's&p 500', 'nasdaq'],
    'Rates': ['lai suat', 'fed', 'federal reserve', 'interest rate', 'interest rates', 'central bank', 'ecb', 'monetary policy', 'governing council'],
    'Currencies': ['ty gia', 'ngoai te', 'usd', 'dollar', 'forex', 'currency', 'yuan'],
    'China': ['trung quoc', 'china', 'chinese', 'beijing'],
    'Oil': ['dau tho', 'gia dau', 'oil', 'opec', 'crude', 'diesel'],
    'Gold': ['gia vang', 'vang mieng', 'gold', 'bullion'],
    'Trade': ['xuat khau', 'nhap khau', 'thue quan', 'tariff', 'trade', 'exports', 'imports'],
    'Economy': ['kinh te', 'lam phat', 'gdp', 'cpi', 'inflation', 'economy', 'economic', 'employment', 'recession'],
    'Semiconductors': ['ban dan', 'semiconductor', 'computer chip', 'computer chips', 'chipmaker', 'microchip', 'nvidia', 'tsmc'],
    'AI': ['tri tue nhan tao', 'artificial intelligence', 'ai', 'openai'],
    'Earnings': ['loi nhuan', 'doanh thu', 'ket qua kinh doanh', 'earnings', 'revenue', 'profit'],
    'Real Estate': ['bat dong san', 'dia oc', 'real estate', 'property market'],
    'Banking': ['ngan hang', 'tin dung', 'banking', 'central bank', 'commercial bank', 'investment bank', 'banks', 'credit'],
}
SECTORS = {
    'Financials': ['ngan hang', 'bao hiem', 'central bank', 'commercial bank', 'investment bank', 'banks', 'banking', 'insurance'],
    'Real Estate': ['bat dong san', 'dia oc', 'real estate', 'property'],
    'Technology': ['cong nghe', 'ban dan', 'technology', 'semiconductor', 'artificial intelligence'],
    'Energy': ['dau khi', 'dau tho', 'oil', 'gas', 'energy'],
    'Consumer': ['ban le', 'tieu dung', 'retail', 'consumer'],
    'Industrials': ['san xuat', 'logistics', 'manufacturing', 'steel', 'thep'],
}


def contains(text: str, term: str) -> bool:
    return f' {normalized(term)} ' in f' {text} '


@dataclass(frozen=True)
class Tags:
    topics: list[str]
    tickers: list[str]
    sectors: list[str]
    scope: str


ENTITY_POLICY = 'issuer-context-v2'
# Language meanings, independent of the equity universe. These terms can still
# identify a security through explicit stock notation or its unique legal name.
AMBIGUOUS_LANGUAGE = frozenset(('it all are can for has his how new now one our out the who why you '
    'ceo cfo coo cto cio cpo cmo tp hcm vtv ai gas oil '
    'usd vnd eur gbp jpy cny aud cad chf hkd sgd krw ndt').split())
# Positive issuer evidence, not a list of allowed/forbidden securities. Generic
# price rises, currency amounts, job titles and acronym tokens are insufficient.
ISSUER_ACTIVITY = re.compile(r'^(?:(?:da|se|vua|dang)\s+)?(?:'
    r'huy dong|phat hanh|bo nhiem|mien nhiem|tra co tuc|chia co tuc|'
    r'tang doanh thu|giam doanh thu|tang loi nhuan|giam loi nhuan|'
    r'cong bo (?:ket qua kinh doanh|bao cao tai chinh)|dat muc tieu (?:doanh thu|loi nhuan)|'
    r'(?:gom|mua|ban)\s+(?:\w+\s+){0,10}co phieu|'
    r'loi nhuan|doanh thu|bao cao tai chinh|len tieng ve tin don|'
    r'(?:reports?|posts?|announces?)\s+(?:(?:higher|lower|quarterly|annual|new|revised)\s+)*(?:earnings|revenue|profit|dividend)|'
    r'appoints?\s+(?:a\s+)?(?:new\s+)?(?:director|chief|ceo)|'
    r'earnings|revenue|profit|bank\s+profit)\b')


class Tagger:
    def __init__(self, stocks=(), topics=None, sectors=None, company_aliases=None):
        self.topics = topics if topics is not None else TOPICS
        self.sectors = sectors if sectors is not None else SECTORS
        self.stocks = list(stocks)
        self.company_aliases = company_aliases or {}
        self.identities = {stock.symbol: [normalized(name) for name in
            [stock.company_name, getattr(stock, 'display_name_en', None), *self.company_aliases.get(stock.symbol, [])] if name]
            for stock in self.stocks}
        # Metadata/explicitly configured aliases must identify exactly one issuer.
        owners = {}
        for symbol, names in self.identities.items():
            for name in names:
                if name and name != normalized(symbol) and name not in AMBIGUOUS_LANGUAGE:
                    owners.setdefault(name, set()).add(symbol)
        self.identity_owners = owners
        symbols = '|'.join(re.escape(normalized(s.symbol)) for s in self.stocks)
        self.stock_context = re.compile(r'\b(?:co phieu|ma co phieu|ma chung khoan|ticker|stock|hose|hnx|upcom)\s*'
            r'(?:(?:' + symbols + r')\b\s*(?:(?:va|and)\s*)?)*$')
        self.symbol_pattern = re.compile(r'(?<!\w)(' + '|'.join(re.escape(stock.symbol) for stock in self.stocks) + r')(?!\w)') if self.stocks else None

    def resolve(self, title: str, *, body: str | None = None) -> list[dict]:
        """Headline proofs plus sentence-scoped evidence in supplied publisher text."""
        text = normalized(title)
        matches = {}
        for name, owners in self.identity_owners.items():
            if len(owners) == 1 and f' {name} ' in f' {text} ':
                symbol = next(iter(owners))
                matches[symbol] = dict(symbol=symbol, kind='issuer_identity', matched_text=name, policy=ENTITY_POLICY)
        for match in self.symbol_pattern.finditer(title) if self.symbol_pattern else ():
            prefix = title[max(0, match.start()-40):match.start()]
            folded_prefix = normalized(prefix)
            # A shared explicit stock list ("cổ phiếu ABC và XYZ") remains evidence
            # for each member; prose after the list cannot inherit that context.
            explicit = bool(self.stock_context.search(normalized(title[:match.start()])))
            currency_amount = bool(re.search(r'(?:\d[\d.,]*|ty phu|trieu phu|billionaire|millionaire|trieu|ty|ti|nghin|million|billion)\s*$', folded_prefix))
            location = bool(re.search(r'(?:TP|T\.P)\.\s*$', prefix, re.I))
            broadcaster = bool(re.search(r'(?:roi|dai|kenh)\s*$', folded_prefix))
            following = re.match(r'\s+(?:(?:of|at|của)\s+)?([A-Z0-9]{1,20})\b', title[match.end():])
            role = match[0] in {'CEO','CFO','COO','CTO','CIO','CPO','CMO'} and following and following[1] in self.identities
            tail = normalized(title[match.end():])
            activity = ISSUER_ACTIVITY.search(tail)
            # Market/industry prose can enumerate actual ticker tokens without
            # repeating "cổ phiếu". Currency, role and ordinary-language tokens
            # still need explicit security notation. A brand extension is not
            # evidence that its listed parent was the company being discussed.
            market_context = re.search(r'\b(?:vn index|vnindex|hnx index|upcom index|thi truong chung khoan|stock market|nganh|industry|sector)\b', text)
            brand_extension = re.match(r'\s+[A-Z][a-z]+\b', title[match.end():])
            contextual = (market_context and len(match[0]) >= 3
                and normalized(match[0]) not in AMBIGUOUS_LANGUAGE
                and not (currency_amount or location or broadcaster or role or brand_extension))
            explicit = explicit or bool(contextual)
            if brand_extension and not activity:
                explicit = False
            # Bare mã can describe a currency or product; accent folding also
            # conflates it with the conjunction mà. Require corroborating equity
            # activity, or qualified stock wording above. Cashtags are explicit
            # only for tokens without a competing common language meaning.
            explicit = explicit or bool(re.fullmatch(r'\s*Mã\s+', prefix, re.I)
                and re.match(r'^(?:phat hanh co phieu|tra co tuc|chia co tuc)\b', tail))
            explicit = explicit or bool(re.search(r'(?:^|\s)[$#]$', prefix)
                and normalized(match[0]) not in AMBIGUOUS_LANGUAGE)
            # Require the candidate to occupy an issuer-subject position. A macro
            # phrase such as "giá USD" never acquires issuer status from a suffix.
            subject = re.fullmatch(r'(?:(?:loi nhuan|doanh thu|co tuc|ngan hang|cong ty|'
                r'company|bank|ceo|cfo|chu tich|cua|of|at)\s*)*', folded_prefix)
            if explicit or (activity and subject and normalized(match[0]) not in AMBIGUOUS_LANGUAGE
                            and not (currency_amount or location or broadcaster or role)):
                matches.setdefault(match[0], dict(symbol=match[0], kind='explicit_stock' if explicit else 'issuer_activity',
                    matched_text=normalized(match[0]) + (' ' + activity[0] if activity and not explicit else ''), policy=ENTITY_POLICY))
        for proof in matches.values():
            proof['evidence_origin'] = 'headline'
        if body:
            # Headlines retain precedence. A bare ecosystem name never grants a
            # body association; explicit stock wording or unique legal identity
            # must occur in the same sentence as the candidate.
            for sentence in re.split(r'(?<=[.!?;])\s+|\n+', body[:12000]):
                for proof in self.resolve(sentence):
                    if proof['kind'] not in ('issuer_identity', 'explicit_stock'):
                        continue
                    # Keep an inspectable supporting span, even in long prose.
                    # Revalidate each bounded excerpt rather than cutting away
                    # the stock wording/name that qualified the association.
                    excerpt = None
                    for start in range(0, len(sentence), 300):
                        candidate = sentence[start:start+600]
                        if any(p['symbol'] == proof['symbol'] and p['kind'] == proof['kind']
                               and p['matched_text'] == proof['matched_text'] for p in self.resolve(candidate)):
                            excerpt = candidate
                            break
                    if excerpt is None:
                        continue
                    proof = {**proof, 'evidence_origin': 'publisher_text',
                             'evidence_excerpt': excerpt}
                    matches.setdefault(proof['symbol'], proof)
        return [matches[symbol] for symbol in sorted(matches)]

    def tag(self, title: str, category: str) -> Tags:
        text = normalized(title)
        topics = sorted(k for k, terms in self.topics.items() if any(contains(text, x) for x in terms))
        sectors = {k for k, terms in self.sectors.items() if any(contains(text, x) for x in terms)}
        tickers = {row['symbol'] for row in self.resolve(title)}
        for stock in self.stocks:
            symbol = stock.symbol
            if symbol in tickers:
                if getattr(stock, 'sector', None):
                    sectors.add(stock.sector)
        scope = 'GLOBAL' if category == 'GLOBAL' else 'COMPANY' if tickers else 'SECTOR' if sectors else 'MARKET'
        return Tags(topics, sorted(tickers), sorted(sectors), scope)

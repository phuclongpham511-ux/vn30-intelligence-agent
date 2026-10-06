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


class Tagger:
    def __init__(self, stocks=(), topics=None, sectors=None, company_aliases=None):
        self.topics = topics if topics is not None else TOPICS
        self.sectors = sectors if sectors is not None else SECTORS
        self.stocks = list(stocks)
        self.company_aliases = company_aliases or {}
        self.identities = {stock.symbol: [normalized(name) for name in
            [stock.company_name, getattr(stock, 'display_name_en', None), *self.company_aliases.get(stock.symbol, [])] if name]
            for stock in self.stocks}
        self.symbol_pattern = re.compile(r'(?<!\w)(' + '|'.join(re.escape(stock.symbol) for stock in self.stocks) + r')(?!\w)') if self.stocks else None

    def tag(self, title: str, category: str) -> Tags:
        text = normalized(title)
        topics = sorted(k for k, terms in self.topics.items() if any(contains(text, x) for x in terms))
        sectors = {k for k, terms in self.sectors.items() if any(contains(text, x) for x in terms)}
        tickers = set()
        for match in self.symbol_pattern.finditer(title) if self.symbol_pattern else ():
            prefix = title[max(0, match.start()-40):match.start()]
            folded_prefix = normalized(prefix)
            # These are language contexts, not security exceptions. Explicit stock
            # notation still works for an issuer whose symbol overlaps an acronym.
            explicit = bool(re.search(r'(?:co phieu|ticker|stock|ma|hose|hnx|upcom)\s*$', folded_prefix) or
                re.search(r'[#$]\s*$', prefix))
            currency_amount = bool(re.search(r'(?:\d[\d.,]*|ty phu|trieu phu|billionaire|millionaire|trieu|ty|ti|nghin|million|billion)\s*$', folded_prefix))
            location = bool(re.search(r'(?:TP|T\.P)\.\s*$', prefix, re.I))
            broadcaster = bool(re.search(r'(?:roi|dai|kenh)\s*$', folded_prefix))
            following = re.match(r'\s+(?:(?:of|at|của)\s+)?([A-Z0-9]{1,20})\b', title[match.end():])
            role = match[0] in {'CEO','CFO','COO','CTO','CIO','CPO','CMO'} and following and following[1] in self.identities
            if explicit or not (currency_amount or location or broadcaster or role):
                tickers.add(match[0])
        for stock in self.stocks:
            symbol = stock.symbol
            if symbol in tickers or any(f' {a} ' in f' {text} ' for a in self.identities[symbol]):
                tickers.add(symbol)
                if getattr(stock, 'sector', None):
                    sectors.add(stock.sector)
        scope = 'GLOBAL' if category == 'GLOBAL' else 'COMPANY' if tickers else 'SECTOR' if sectors else 'MARKET'
        return Tags(topics, sorted(tickers), sorted(sectors), scope)

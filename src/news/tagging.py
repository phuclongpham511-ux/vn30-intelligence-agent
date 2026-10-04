"""Deterministic, configurable dictionaries; stock universe comes from the stock table."""
from dataclasses import dataclass
import re
from src.news.normalization import normalized

TOPICS = {
    'Equities': ['chung khoan', 'vn index', 'vnindex', 'co phieu', 'stock market', 'stocks', 'equities', 'wall street', 's&p 500', 'nasdaq'],
    'Rates': ['lai suat', 'fed', 'federal reserve', 'interest rate', 'central bank', 'ecb', 'monetary policy', 'governing council'],
    'Currencies': ['ty gia', 'ngoai te', 'usd', 'dollar', 'forex', 'currency', 'yuan'],
    'China': ['trung quoc', 'china', 'chinese', 'beijing'],
    'Oil': ['dau tho', 'gia dau', 'oil', 'opec', 'crude', 'diesel'],
    'Gold': ['gia vang', 'vang mieng', 'gold', 'bullion'],
    'Trade': ['xuat khau', 'nhap khau', 'thue quan', 'tariff', 'trade', 'exports', 'imports'],
    'Economy': ['kinh te', 'lam phat', 'gdp', 'cpi', 'inflation', 'economy', 'economic', 'employment', 'recession'],
    'Semiconductors': ['ban dan', 'semiconductor', 'chip', 'chips', 'nvidia', 'tsmc'],
    'AI': ['tri tue nhan tao', 'artificial intelligence', 'ai', 'openai'],
    'Earnings': ['loi nhuan', 'doanh thu', 'ket qua kinh doanh', 'earnings', 'revenue', 'profit'],
    'Real Estate': ['bat dong san', 'dia oc', 'real estate', 'property market'],
    'Banking': ['ngan hang', 'tin dung', 'banking', 'bank', 'banks', 'credit'],
}
SECTORS = {
    'Financials': ['ngan hang', 'bao hiem', 'bank', 'banks', 'banking', 'insurance'],
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

    def tag(self, title: str, category: str) -> Tags:
        text = normalized(title)
        topics = sorted(k for k, terms in self.topics.items() if any(contains(text, x) for x in terms))
        sectors = {k for k, terms in self.sectors.items() if any(contains(text, x) for x in terms)}
        tickers = set()
        for stock in self.stocks:
            symbol = stock.symbol
            aliases = [stock.company_name, *self.company_aliases.get(symbol, [])]
            matched = bool(re.search(r'(?<![\w])' + re.escape(symbol) + r'(?![\w])', title))
            if matched or any(a and contains(text, a) for a in aliases):
                tickers.add(symbol)
                if stock.sector:
                    sectors.add(stock.sector)
        scope = 'GLOBAL' if category == 'GLOBAL' else 'COMPANY' if tickers else 'SECTOR' if sectors else 'MARKET'
        return Tags(topics, sorted(tickers), sorted(sectors), scope)

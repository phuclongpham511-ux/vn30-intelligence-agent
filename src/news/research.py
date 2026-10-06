"""Read-layer semantic classification; original Article/Story tags are preserved."""
from src.news.normalization import normalized
from src.news.tagging import contains
import re

MARKET_TERMS = ('vn index', 'vnindex', 'hnx index', 'upcom index', 'thi truong chung khoan',
    'luat chung khoan', 'co cau chi so', 'tai co cau chi so', 'nang hang thi truong',
    'chinh sach tien te', 'lai suat', 'lam phat', 'ty gia', 'gdp', 'cpi', 'khoi ngoai',
    'thanh khoan thi truong', 'tin dung toan', 'fed', 'central bank', 'monetary policy',
    'interest rate', 'inflation', 'stock market', 'securities regulation', 'index rebalance',
    'foreign flows', 'market liquidity', 'thue quan', 'tariff')
INDUSTRY_TERMS = ('nganh', 'he thong ngan hang', 'banking system', 'steel industry', 'retail sector',
    'aviation', 'hang khong', 'moi gioi', 'brokerage', 'bat dong san', 'thep', 'ban le',
    'dau khi', 'cong nghe', 'technology', 'semiconductor', 'coffee exports', 'ca phe')
PRIMARY_MARKET = r'^(?:vn index|vnindex|hnx index|upcom index|thi truong chung khoan|stock market|central bank|fed|ngan hang nha nuoc|luat chung khoan)\b'
PRIMARY_INDUSTRY = r'^(?:nganh|he thong ngan hang|banking system|steel industry|retail sector|aviation industry|securities brokers)\b'
NAMED_ISSUER = r'^[\w .&]{2,60}\s(?:[-–:]|trở thành|becomes)\s*(?:ngân hàng|công ty|bank|company)\b'


def research_category(article):
    text = normalized(article.title)
    if re.search(PRIMARY_MARKET, text):
        return 'MARKET_BRIEF'
    if re.search(PRIMARY_INDUSTRY, text):
        return 'INDUSTRY'
    # Explicit named bank/company subject; classification does not invent its ticker.
    if re.search(NAMED_ISSUER, article.title, re.I):
        return 'COMPANY'
    if article.tickers:
        return 'COMPANY'
    if any(contains(text, term) for term in MARKET_TERMS):
        return 'MARKET_BRIEF'
    if any(contains(text, term) for term in INDUSTRY_TERMS) or article.sectors:
        return 'INDUSTRY'
    return None


def attention_order(item):
    """Publisher breadth is primary, capped activity secondary, latest activity tertiary."""
    from src.news.normalization import utc
    return (-item.story.source_count, -min(item.story.article_count, 20),
        -utc(item.story.last_updated_at).timestamp(), item.story.id)

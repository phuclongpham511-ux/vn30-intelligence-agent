"""Read-layer semantic classification; original Article/Story tags are preserved."""
from src.news.normalization import normalized
from src.news.tagging import contains
import re

MARKET_TERMS = ('vn index', 'vnindex', 'hnx index', 'upcom index', 'thi truong chung khoan',
    'luat chung khoan', 'co cau chi so', 'tai co cau chi so', 'nang hang thi truong',
    'chinh sach tien te', 'lai suat', 'lam phat', 'ty gia', 'gdp', 'cpi', 'khoi ngoai',
    'thanh khoan thi truong', 'tin dung toan', 'fed', 'central bank', 'monetary policy',
    'interest rate', 'interest rates', 'inflation', 'stock market', 'securities regulation', 'index rebalance',
    'foreign flows', 'market liquidity', 'thue quan', 'tariff')
INDUSTRY_TERMS = ('nganh', 'he thong ngan hang', 'banking system', 'steel industry', 'retail sector',
    'aviation', 'hang khong', 'moi gioi', 'brokerage', 'bat dong san', 'thep', 'ban le',
    'dau khi', 'cong nghe', 'technology', 'semiconductor', 'coffee exports', 'ca phe')
PRIMARY_MARKET = r'^(?:vn index|vnindex|hnx index|upcom index|thi truong chung khoan|stock market|central bank|fed|ngan hang nha nuoc|luat chung khoan)\b'
PRIMARY_INDUSTRY = r'^(?:nganh|he thong ngan hang|cac ngan hang|nhom ngan hang|banking system|banking sector|steel industry|retail sector|aviation industry|securities industry|securities brokers|real estate sector|oil and gas industry|technology sector)\b'
NAMED_ISSUER = r'^[\w .&]{2,60}\s(?:[-–:]|trở thành|becomes)\s*(?:the\s+)?(?:first\s+)?(?:ngân hàng|công ty|bank|company|insurer|financial institution|corporation)\b'


def research_category(article):
    text = normalized(article.title)
    if re.search(PRIMARY_MARKET, text):
        return 'MARKET_BRIEF'
    if re.search(PRIMARY_INDUSTRY, text):
        return 'INDUSTRY'
    # Explicit named bank/company subject; classification does not invent its ticker.
    if re.search(NAMED_ISSUER, article.title, re.I):
        return 'COMPANY'
    # A named organization after an explicit organization noun is issuer framing.
    # Generic sector/system and central-bank subjects were handled above.
    subject = re.match(r'^(?i:ngân hàng|công ty|tập đoàn|chứng khoán|bảo hiểm|bank|company|corporation|insurer|financial institution|securities company)\s+(.+)', article.title)
    if subject:
        name = subject[1].split()[0].strip('"“')
        if name and name[0].isupper() and not any(text.startswith(prefix) for prefix in (
            'ngan hang viet nam', 'ngan hang trung uong', 'bank sector', 'company sector')):
            return 'COMPANY'
    if re.match(r'^[A-Za-z0-9][\w&.-]+(?:Bank|Corp|Insurance)\b', article.title):
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

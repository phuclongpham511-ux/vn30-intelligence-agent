"""Read-layer semantic classification; original Article/Story tags are preserved."""
from src.news.normalization import normalized
from src.news.tagging import contains
import re

MARKET_TERMS = ('vn index', 'vnindex', 'hnx index', 'upcom index', 'thi truong chung khoan',
    'luat chung khoan', 'co cau chi so', 'tai co cau chi so', 'nang hang thi truong',
    'chinh sach tien te', 'lai suat', 'lam phat', 'ty gia', 'gdp', 'cpi', 'khoi ngoai',
    'thanh khoan thi truong', 'tin dung toan', 'fed', 'central bank', 'monetary policy',
    'interest rate', 'interest rates', 'inflation', 'stock market', 'securities regulation', 'index rebalance',
    'foreign flows', 'nha dau tu ngoai', 'von ngoai', 'nha dau tu nuoc ngoai', 'market liquidity', 'thue quan', 'tariff')
INDUSTRY_TERMS = ('he thong ngan hang', 'banking system', 'steel industry', 'retail sector',
    'aviation', 'hang khong', 'moi gioi', 'brokerage', 'bat dong san', 'thep', 'ban le',
    'dau khi', 'cong nghe', 'technology', 'semiconductor', 'coffee exports', 'ca phe', 'co khi', 'go noi that', 'nong nghiep', 'thuc uong', 'thuc pham', 'du lich', 'logistics', 'det may', 'thuy san')
PRIMARY_MARKET = r'^(?:vn index|vnindex|hnx index|upcom index|thi truong chung khoan|stock market|central bank|fed|ngan hang nha nuoc|luat chung khoan)\b'
PRIMARY_INDUSTRY = r'^(?:nganh (?:ngan hang|chung khoan|thep|ban le|bat dong san|cong nghe|hang khong|dau khi|co khi|go|nong nghiep|thuc pham|thuc uong|du lich|logistics|det may|thuy san)|he thong ngan hang|cac ngan hang|nhom ngan hang|banking system|banking sector|steel industry|retail sector|aviation industry|securities industry|securities brokers|real estate sector|oil and gas industry|technology sector)\b'
FOREIGN_SUBJECT = r'\b(?:nvidia|openai|spacex|elon musk|wall street|nasdaq|s p 500|goldman sachs|fed|ecb|trung quoc|china|nuoc my|tai my|kinh te my|thi truong my|hoa ky|middle east|trung dong|toan cau|global|overseas)\b'
FOREIGN_GEOGRAPHY = r'\b(?:nhat ban|japan|japanese|han quoc|korea|korean|dai loan|taiwan|an do|india|indian|thai lan|thailand|singapore|indonesia|malaysia|chau au|europe|european|britain|british|london|germany|german|france|french|italy|italian|australia|australian|canada|canadian|russia|russian|ukraine|israel|iran|brazil|brazilian)\b'
FOREIGN_SECTOR_COUNTRY = r'\b(?:nganh|cong nghe|kinh te|thi truong|co phieu|thep|ngan hang|bat dong san|ban le|san xuat|cong nghiep)\s+(?:(?:tai|o|cua)\s+)?(?:my|anh|duc|phap|nga)\b'
ISSUER_ACTIONS = {'announces','reports','expands','appoints','earnings','revenue','profit','declares','raises','increases','invests','signs','launches','acquires','records','plans','shares','stock','capital','operations'}
ISSUER_VIETNAMESE_ACTION = r'^(?:loi nhuan|doanh thu|bo nhiem|mien nhiem|huy dong|tang|giam|cong bo|bao cao|dau tu|ky ket|hop tac|mua|ban|hoan|phat hanh|chuyen|tra|chia|du kien|len ke hoach|dang|da|se|vua|duoc|khong|lai|lan|nhan|co|tiep|tien|len|ve|voi)\b'
VIETNAM_CONTEXT = ('viet nam', 'vietnam', 'vn index', 'vnindex', 'vnd', 'dong viet', 'trong nuoc', 'noi dia', 'ngan hang nha nuoc')
ISSUER_PREFIX = r'^(?:(?:co phieu|ma|ticker|stock|ngan hang|bank|cong ty|company|tap doan|corporation|chung khoan|bao hiem|chu tich|ceo|cfo|director|chairman|lanh dao|tong giam doc|loi nhuan(?: sau thue)?|doanh thu|ket qua kinh doanh|earnings|profit|revenue|income|co tuc|nhan su|du an|cua|of|at)\s+)*$'


def primary_issuers(title, equities):
    """Conservative headline-subject identity, never a name-shaped organization guess."""
    text = normalized(title)
    result = set()
    for equity in equities:
        names = [equity.symbol, equity.company_name, getattr(equity, 'display_name_en', None)]
        for name in filter(None, names):
            match = re.search(r'(?<!\w)' + re.escape(normalized(name)) + r'(?!\w)', text)
            if not match or not re.fullmatch(ISSUER_PREFIX, text[:match.start()]):
                continue
            # An unknown extension of a bare brand may name another legal entity, in any casing.
            if name == equity.symbol:
                tail = text[match.end():].strip()
                extension = re.match(r'([a-z][a-z&.-]+)\b', tail)
                if extension and extension[1].casefold() not in ISSUER_ACTIONS and not re.search(ISSUER_VIETNAMESE_ACTION, normalized(tail)):
                    pair = normalized(name + ' ' + extension[1])
                    identities = [normalized(value) for value in (equity.company_name, getattr(equity, 'display_name_en', None)) if value]
                    descriptor = extension[1].casefold() in {'bank','company','corporation'} and any(contains(identity, extension[1]) for identity in identities)
                    if not descriptor and not any(contains(identity, pair) for identity in identities):
                        continue
            result.add(equity.symbol)
    return result


def vietnam_relevance(title, primary=()):
    text = normalized(title)
    foreign = any(re.search(pattern, text) for pattern in (FOREIGN_SUBJECT, FOREIGN_GEOGRAPHY, FOREIGN_SECTOR_COUNTRY))
    return not foreign or bool(primary) or any(contains(text, term) for term in VIETNAM_CONTEXT)


def research_category(article, equities=()):
    text = normalized(article.title)
    primary = primary_issuers(article.title, equities)
    if not vietnam_relevance(article.title, primary):
        return None
    # A named analyst before a colon is attribution, not the market subject.
    subject = normalized(article.title.split(':', 1)[-1])
    if re.search(PRIMARY_MARKET, text) or re.search(PRIMARY_MARKET, subject) or re.search(r'\busd\s+vnd\b', text):
        return 'MARKET_BRIEF'
    if re.search(PRIMARY_INDUSTRY, text):
        return 'INDUSTRY'
    if primary:
        return 'COMPANY'
    if (re.match(r'^[A-Za-z0-9][\w&.-]+(?:Bank|Corp|Insurance)\b', article.title) or
        re.match(r'^(?i:ngân hàng|công ty|tập đoàn|bank|company|corporation)\s+[A-Z][\w.-]+', article.title)):
        return None
    if any(contains(text, term) for term in MARKET_TERMS):
        return 'MARKET_BRIEF'
    # Sector tags alone describe mentions, not the primary subject.
    sector_framing = (contains(text, 'nganh') or contains(text, 'sector') or contains(text, 'industry') or
        re.search(r'^(?:(?:kim ngach )?(?:xuat khau|coffee exports)|gia|nhu cau|nguon cung|thi truong|san luong|tieu thu|cac doanh nghiep|nhom doanh nghiep)\b', text))
    if sector_framing and any(contains(text, term) for term in INDUSTRY_TERMS):
        return 'INDUSTRY'
    return None


def attention_order(item):
    """Publisher breadth is primary, capped activity secondary, latest activity tertiary."""
    from src.news.normalization import utc
    return (-item.story.source_count, -min(item.story.article_count, 20),
        -utc(item.story.last_updated_at).timestamp(), item.story.id)

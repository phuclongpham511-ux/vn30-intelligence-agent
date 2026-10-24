"""Finite Vietnamese question grammar, not a general-language classifier."""
import re
import unicodedata

from src.schemas.financial_assistant import QuestionIntent

METRIC_LABELS = {
    'revenue': ('doanh thu', 'Doanh thu'),
    'net_profit': ('loi nhuan', 'Lợi nhuận sau thuế'),
    'net_margin': ('bien loi nhuan rong', 'Biên lợi nhuận ròng'),
    'gross_margin': ('bien loi nhuan gop', 'Biên lợi nhuận gộp'),
    'roe': ('roe', 'ROE'),
    'roa': ('roa', 'ROA'),
    'cash_operating': ('dong tien hoat dong', 'Dòng tiền hoạt động'),
    'total_assets': ('tong tai san', 'Tổng tài sản'),
    'total_liabilities': ('tong no phai tra', 'Tổng nợ phải trả'),
    'equity': ('von chu so huu', 'Vốn chủ sở hữu'),
    'operating_income': ('thu nhap hoat dong', 'Thu nhập hoạt động'),
    'customer_loans': ('du no cho vay', 'Dư nợ cho vay khách hàng'),
    'customer_deposits': ('tien gui khach hang', 'Tiền gửi khách hàng'),
}
ACRONYMS = {'ROE', 'ROA', 'NIM', 'CASA', 'CAR', 'NPL', 'LDR', 'EPS', 'EBITDA',
    'FCF', 'TTM', 'YOY', 'QOQ', 'SQL', 'PDF', 'API', 'LLM', 'Q1', 'Q2', 'Q3', 'Q4'}


class UnsupportedQuestion(ValueError):
    """Stable reason code, without echoing the user's potentially private text."""


def folded(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.replace('đ', 'd').replace('Đ', 'D'))
        if not unicodedata.combining(c)).casefold()


def select_intent(question: str) -> QuestionIntent:
    if not isinstance(question, str) or not question.strip() or len(question.encode('utf-8')) > 2048:
        raise UnsupportedQuestion('question_size_or_empty')
    text = re.sub(r'\b(quy|nam)(?=\d)', r'\1 ', folded(question))
    if re.search(r'ignore|bo qua|system|developer|thuc thi|execute|python|select\s+.+\s+from|'
            r'https?://|file:|[a-z]:[\\/]|\.\.[\\/]|/etc/|credentials|password|api.key|mat khau|'
            r'tiet lo|doc (?:tep|file)|gui email|gui du lieu|upload|`', text):
        raise UnsupportedQuestion('unsafe_or_out_of_scope_instruction')
    if re.search(r'\b(?:buy|sell|hold)\b|nen mua|nen ban|nen giu|khuyen nghi dau tu|gia muc tieu', text):
        raise UnsupportedQuestion('investment_advice_unsupported')
    if re.search(r'\b(?:nim|casa|car|npl|ldr|cir|fcf|ebitda|ttm|eps)\b|gia tri hop ly|du bao|'
            r'nguyen nhan|tai sao|vi sao|luy ke|loi nhuan truoc thue|(?<!bien )loi nhuan gop|'
            r'loi nhuan.*cong ty me|bien loi nhuan(?! rong| gop)|dong tien tu do', text):
        raise UnsupportedQuestion('unsupported_definition_or_causality')
    tickers = set(re.findall(r'\b[A-Z][A-Z0-9]{1,19}\b', question)) - ACRONYMS
    tickers.update(s.upper() for s in re.findall(r'\b(?:ma|co phieu)\s+([a-z][a-z0-9]{1,19})\b', text))
    if len(tickers) != 1:
        raise UnsupportedQuestion('one_explicit_ticker_required')
    ticker = tickers.pop()
    quarterly = bool(re.search(r'\bquy\b|\b\d+-q\d+\b', text))
    annual = bool(re.search(r'hang nam|theo nam|bao cao nam|ca nam', text))
    if quarterly and annual:
        raise UnsupportedQuestion('incompatible_frequency')
    frequency = 'quarterly' if quarterly else 'annual'
    quarter_dates = re.findall(r'\bquy\s*(\d+)\s*(?:[/\-]|nam|\s)\s*(\d+)\b', text)
    iso_dates = re.findall(r'\b(\d+)-q(\d+)\b', text)
    explicit_years = (re.findall(r'\bnam\s*(\d+)\b', text) + re.findall(r'\b\d{4}\b', text)
        + [year for _, year in quarter_dates] + [year for year, _ in iso_dates])
    if any(len(year) != 4 or not 1900 <= int(year) <= 2199 for year in explicit_years):
        raise UnsupportedQuestion('unsupported_year')
    if (any(quarter not in ('1', '2', '3', '4') for quarter, _ in quarter_dates)
            or any(quarter not in ('1', '2', '3', '4') for _, quarter in iso_dates)):
        raise UnsupportedQuestion('explicit_quarter_required')
    comparison = 'qoq' if re.search(r'qoq|quy truoc|lien quy', text) else 'yoy'
    if frequency == 'annual' and comparison == 'qoq':
        raise UnsupportedQuestion('incompatible_comparison')
    quarter_matches = re.findall(r'\bquy\s*([1-4])\s*(?:[/\-]|nam)?\s*((?:19|20|21)\d{2})\b', text)
    periods = [f'{year}-Q{quarter}' for quarter, year in quarter_matches]
    periods += [f'{year}-Q{quarter}' for year, quarter in re.findall(r'\b((?:19|20|21)\d{2})-q([1-4])\b', text)]
    years = re.findall(r'\b(?:19|20|21)\d{2}\b', text)
    if re.search(r'quy\s*[05-9]|\d{4}-q[05-9]', text) or quarterly and years and not periods:
        raise UnsupportedQuestion('explicit_quarter_required')
    quarter_text = re.sub(r'\bquy\s*([1-4])\s*(?:[/\-]|nam)?\s*((?:19|20|21)\d{2})\b', '', text)
    quarter_text = re.sub(r'\b(?:19|20|21)\d{2}-q[1-4]\b', '', quarter_text)
    if re.search(r'\bquy\s*\d|\b\d+-q|\bq\d+\b|\b\d+q\d+\b', quarter_text):
        raise UnsupportedQuestion('explicit_quarter_required')
    if quarterly and re.search(r'\b(?:19|20|21)\d{2}\b', quarter_text):
        raise UnsupportedQuestion('incompatible_frequency')
    if not quarterly:
        periods = years
    periods = list(dict.fromkeys(periods))
    if len(periods) > 2:
        raise UnsupportedQuestion('period_limit')
    metrics = []
    # Match longer labels first so "biên lợi nhuận ròng" is not also PAT.
    remaining = text
    for metric, (alias, _) in sorted(METRIC_LABELS.items(), key=lambda item: -len(item[1][0])):
        pattern = r'\bloi nhuan(?: sau thue)?\b' if metric == 'net_profit' else r'\b' + alias + r'\b'
        matches = list(re.finditer(pattern, remaining))
        if metric == 'net_profit':
            for match in matches:
                # A bare/PAT alias cannot stand for operating profit, a yield,
                # parent profit or another unrecognized qualified definition.
                tail = remaining[match.end():].lstrip()
                supported_tail = (r'^(?:$|[?,.;]|(?:cua\s+)?' + re.escape(ticker.casefold())
                    + r'\b|(?:nam|quy|hang nam|theo nam|la|va)\b|(?:19|20|21)\d{2}\b)')
                if re.search(r'(?:ty suat|ty le|bien)\s*$', remaining[:match.start()]) or not re.search(supported_tail, tail):
                    raise UnsupportedQuestion('unsupported_definition_or_causality')
        if matches:
            metrics.append(metric)
            remaining = re.sub(pattern, '', remaining)
    if len(metrics) > 4:
        raise UnsupportedQuestion('metric_limit')
    if 'ngan hang' in text and re.search(r'chi (?:tieu|so)|san co', text):
        kind = 'comparison' if re.search(r'tang truong|so sanh|thay doi|bien dong', text) else 'metrics'
        metrics = ['operating_income', 'net_profit', 'customer_loans', 'customer_deposits']
    elif re.search(r'dong tien|luu chuyen tien te', text) and re.search(r'thieu|san co|co du lieu|moi nhat', text):
        kind = 'statement'
    elif re.search(r'tang truong|so sanh|thay doi|bien dong', text):
        kind, metrics = 'comparison', metrics or ['revenue', 'net_profit']
    elif re.search(r'ket qua tai chinh|hieu qua tai chinh|tinh hinh tai chinh|phan tich tai chinh', text):
        kind, metrics = 'performance', ['revenue', 'net_profit']
    elif metrics:
        kind = 'metrics'
    else:
        raise UnsupportedQuestion('unsupported_question_type')
    # The existing Insight Engine supports a smaller set than metric retrieval.
    if kind == 'comparison' and set(metrics) & {'roe', 'roa'}:
        raise UnsupportedQuestion('unsupported_comparison_metric')
    return QuestionIntent(kind=kind, ticker=ticker, frequency=frequency, periods=periods,
        metrics=metrics, statement='cash' if kind == 'statement' else None, comparison=comparison)

"""Extractive Vietnamese discussion grouping; breadth is never corroboration."""
from collections import Counter
from difflib import SequenceMatcher
import re
from src.news.normalization import normalized

TOPICS = (
    ('foreign_flows', 'Foreign investor flows', ('khoi ngoai', 'tay ban', 'tay mua', 'nn ban rong', 'nn mua rong', 'ngoai ban rong', 'ngoai mua rong')),
    ('technical_levels', 'Technical levels and support', ('ma50', 'ma20', 'ma200', 'ho tro', 'thung ma', 'test ma', 'khang cu')),
    ('earnings_capacity', 'Earnings and operating capacity', ('loi nhuan', 'cong suat', 'san luong', 'doanh thu', 'ket qua kinh doanh')),
    ('distributions', 'Dividends and distributions', ('co tuc', 'chia thuong', 'chia co phieu', 'tra co tuc')),
    ('price_action', 'Price action discussion', ('keo tru', 'dap', 'tim', 'break', 'fomo', 'tang tran', 'giam san')),
    ('brokerage_share', 'Brokerage market-share competition', ('thi phan moi gioi', 'brokerage market share')),
)
STOP = set('va la cua cho voi nhung nay thi mot cac co phieu ma ngay hom nay nha dau tu cong ty tap doan ve trong duoc khong den tu tren tai se da dang nguoi khi cung rat nhu hon sau lai roi nao minh anh em chung ta toi ban mua stock ticker'.split())


def text(row):
    body = ' '.join(filter(None, [row.get('title'), row['excerpt']]))
    return normalized(re.sub(r'https?://\S+|www\.\S+', ' ', body))


def deduplicate(items):
    groups, native = [], set()
    for row in items:
        if row['id'] in native:
            continue
        native.add(row['id'])
        fingerprint = text(row)
        match = None
        # Long exact or very close copy only; generic short comments remain independent.
        if len(fingerprint) >= 100:
            for group in groups:
                other = text(group[0])
                if len(other) >= 100 and (fingerprint == other or
                    (len(fingerprint.split()) >= 30 and len(other.split()) >= 30 and SequenceMatcher(None, fingerprint, other, autojunk=False).ratio() >= .95)):
                    match = group
                    break
        if match is None:
            groups.append([row])
        else:
            match.append(row)
    return groups


def representative_excerpt(row, keywords):
    for body in (row['excerpt'], row.get('title') or ''):
        # Mask links without shifting offsets into the original evidence text.
        searchable = re.sub(r'https?://\S+|www\.\S+', lambda match: ' '*len(match[0]), body)
        words = list(re.finditer(r'\S+', searchable))
        for index, word in enumerate(words):
            phrase = normalized(searchable[word.start():words[min(index+3, len(words)-1)].end()])
            if any(re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', phrase) for term in keywords):
                start = max(0, word.start()-50)
                end = min(len(body), start+300)
                return ('…' if start else '') + body[start:end] + ('…' if end<len(body) else '')
    return row['excerpt'][:300]


def evidence_title(row):
    """Quote an actual source clause; never translate or invent a sparse theme."""
    body = row.get('title') or row['excerpt']
    body = re.sub(r'https?://\S+|www\.\S+', '', body)
    clause = re.split(r'[\n.!?]', ' '.join(body.split()), maxsplit=1)[0].strip()
    return clause[:100] + ('…' if len(clause) > 100 else '')


def concise_excerpt(row, keywords):
    body = representative_excerpt(row, keywords)
    sentences = re.split(r'(?<=[.!?])\s+', body)
    sentence = next((part for part in sentences if any(re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', normalized(part)) for term in keywords)), sentences[0])
    return sentence[:179] + '…' if len(sentence) > 180 else sentence


def extract_themes(groups, excluded=()):
    excluded_words = set(' '.join(normalized(value) for value in excluded).split())
    candidates = {}
    unmatched = []
    for index, group in enumerate(groups):
        value = text(group[0])
        matched = False
        for identity, label, synonyms in TOPICS:
            terms = [term for term in synonyms if re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', value)
                and (term != 'tim' or re.search(r'\btím\b', group[0]['excerpt'], re.I))]
            if terms:
                candidate = candidates.setdefault(identity, dict(label=label, indices=set(), keywords=set()))
                candidate['indices'].add(index); candidate['keywords'].update(terms)
                matched = True
        if not matched:
            unmatched.append(index)
    phrases = Counter()
    item_phrases = {}
    for index in unmatched:
        tokens = re.findall(r'[a-z0-9]+', text(groups[index][0]))
        item_phrases[index] = set(' '.join(tokens[n:n+size]) for size in (2,3) for n in range(len(tokens)-size+1)
            if all(t not in STOP | excluded_words and len(t)>1 for t in tokens[n:n+size]))
        phrases.update(item_phrases[index])
    for phrase, frequency in sorted(phrases.items(), key=lambda pair:(-pair[1], -len(pair[0].split()), pair[0])):
        if frequency < 2:
            continue
        indices = {index for index in unmatched if phrase in item_phrases[index]}
        if indices:
            candidates['phrase:' + phrase] = dict(label=None, indices=indices, keywords={phrase})
            unmatched = [i for i in unmatched if i not in indices]
    # Honest sparse coverage: quote a real discussion instead of inventing a topic.
    for index in unmatched:
        candidates['item:' + groups[index][0]['id']] = dict(label=evidence_title(groups[index][0]), indices={index}, keywords=set())
    output = []
    for identity, candidate in candidates.items():
        evidence = [row for index in sorted(candidate['indices']) for row in groups[index]]
        evidence.sort(key=lambda row:(-row['published_at'].timestamp(),row['id']))
        sources = sorted(set(row['source_id'] for row in evidence))
        representative = evidence[0]
        output.append(dict(id=identity, label=candidate['label'] or evidence_title(representative), keywords=sorted(candidate['keywords'])[:5],
            summary=concise_excerpt(representative, candidate['keywords']), summary_kind='representative_excerpt',
            representative_id=representative['id'], item_count=len(candidate['indices']), source_ids=sources,
            source_count=len(sources), latest_at=evidence[0]['published_at'], evidence_ids=[row['id'] for row in evidence],
            evidence_revisions=[dict(id=row['id'], revision_id=row['revision_id']) for row in evidence]))
    output.sort(key=lambda theme:(-theme['item_count'], -theme['source_count'], -theme['latest_at'].timestamp(), theme['id']))
    return output[:3]

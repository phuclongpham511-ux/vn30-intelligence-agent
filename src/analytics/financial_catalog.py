"""Additional original-note fields; no guessed VCI mappings or provider ratios."""
NOTE_FIELDS = {
    'balance': {
        'customer_demand_deposits': 'Customer demand deposits',
        'classified_loans': 'Classified customer loans (excluding securities margin lending)',
        'loan_grade_1': 'Standard loans',
        'loan_grade_2': 'Special mention loans',
        'loan_grade_3': 'Substandard loans',
        'loan_grade_4': 'Doubtful loans',
        'loan_grade_5': 'Loss loans',
        'loan_allowance_general': 'General allowance for classified customer loans',
        'loan_allowance_specific': 'Specific allowance for classified customer loans',
    }
}
LOAN_QUALITY_FIELDS = {'classified_loans', *(f'loan_grade_{i}' for i in range(1,6))}
NOTE_AMOUNTS = set(NOTE_FIELDS['balance'])
BANK_NOTE_AMOUNTS = NOTE_AMOUNTS.copy()
NOTE_FIELDS['balance'].update(ordinary_equity='Ordinary shareholders capital and reserves',
    ordinary_shares='Ordinary shares in circulation')
NOTE_AMOUNTS.add('ordinary_equity')
NOTE_RATIOS = {'demand_deposit_share', 'npl_classified_ratio', 'classified_loan_coverage'}


def specialist_consistency(ref):
    """Only the relevant note equation can disqualify an individual field."""
    meta = (ref.get('source_context') or {}).get('original_metadata') or {}
    if ref.get('field')=='ordinary_shares':
        value=ref.get('value')
        return type(value) in (int,float) and value>0 and value==int(value)
    return not (ref.get('field') in LOAN_QUALITY_FIELDS and meta.get('loan_quality_identity') == 'FAIL')

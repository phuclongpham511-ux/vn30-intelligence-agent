"""Transport-only projection; the Python financial engine remains unchanged."""
from src.schemas.financials import FinancialEngineResponse


def display_financial_response(result: FinancialEngineResponse) -> FinancialEngineResponse:
    """Keep facts/tables/receipts and the latest inspected calculation evidence.

    The default full API still supplies every historical calculation. Chart rows
    repeat facts, never need a second copy of the calculation input graph.
    """
    latest = len(result.rows) - 1
    return result.model_copy(update={
        'rows': [row if index == latest else {k:v for k,v in row.items() if k != 'calculations'}
                 for index, row in enumerate(result.rows)],
        'chart_rows': [{k:v for k,v in row.items() if k != 'calculations'} for row in result.chart_rows],
    })

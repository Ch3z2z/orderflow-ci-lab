"""Daily settlement preparation from delivered orders."""
from collections import defaultdict
from datetime import datetime

def payments_for_settlement(records: list[dict], day: str):
    selected = []
    for record in records:
        paid_at = datetime.fromisoformat(record['paid_at'])
        if paid_at.strftime('%Y-%m-%d') == day and record['state'] == 'paid':
            selected.append(record)
    return selected

def sum_by_merchant(records: list[dict]) -> dict[int, int]:
    totals = defaultdict(int)
    for record in records:
        totals[int(record['merchant_id'])] += int(record['amount'])
    return dict(totals)

def reconcile(expected: list[dict], actual: list[dict]) -> list[dict]:
    """Find transactions with mismatched amounts."""
    actual_by_ref: dict[str, list[int]] = defaultdict(list)
    for row in actual:
        actual_by_ref[row['reference']].append(row['amount'])
    differences = []
    for item in expected:
        amounts = actual_by_ref.pop(item['reference'], [])
        received = sum(amounts) if amounts else None
        if len(amounts) != 1 or received != item['amount']:
            differences.append({'reference': item['reference'],
                                'expected': item['amount'],
                                'actual': received})
    for reference, amounts in actual_by_ref.items():
        differences.append({'reference': reference, 'expected': None,
                            'actual': sum(amounts)})
    return differences

def settlement_reference(merchant_id: int, day: str) -> str:
    return f'SET-{merchant_id}-{day.replace("-", "")}'

"""Pricing policies used by the checkout and reporting layers."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

@dataclass(frozen=True)
class Promotion:
    code: str
    percent: int
    minimum: int = 0
    categories: tuple[str, ...] = ()

PROMOTIONS = (
    Promotion("FALL10", 10, 2000),
    Promotion("OFFICE7", 7, 1200, ("office",)),
    Promotion("HOME12", 12, 3000, ("home",)),
)

def available_promotions(subtotal: int, categories: Iterable[str]):
    categories = set(categories)
    for promotion in PROMOTIONS:
        if subtotal < promotion.minimum:
            continue
        if promotion.categories and not categories.intersection(promotion.categories):
            continue
        yield promotion

def apply_promotions(subtotal: int, codes: list[str], categories: Iterable[str]):
    eligible = {p.code: p for p in available_promotions(subtotal, categories)}
    result = Decimal(subtotal)
    applied = []
    for code in codes:
        rule = eligible.get(code.upper())
        if rule is None or rule.code in applied:
            continue
        result *= Decimal(100 - rule.percent) / Decimal(100)
        applied.append(rule.code)
    return int(result.quantize(Decimal('1'), rounding=ROUND_HALF_UP)), applied

def calculate_service_fee(subtotal: int, loyalty_tier: str, delivery_type: str):
    if delivery_type == 'courier':
        fee = 350 if subtotal >= 5000 else 590
    elif delivery_type == 'pickup':
        fee = 0
    elif delivery_type == 'post':
        fee = 250 if subtotal >= 3000 else 450
    else:
        raise ValueError('Unsupported delivery type')
    if loyalty_tier == 'gold':
        fee = int(fee * .75)
    elif loyalty_tier == 'silver':
        fee = int(fee * .90)
    return fee

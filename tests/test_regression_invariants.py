"""Regression scenarios for business invariants that the original suite did not cover."""
from datetime import datetime, timezone

from orderflow.billing import distribute_refund
from orderflow.fulfillment import Basket, Line, reserve_items
from orderflow.inventory import Warehouse, allocate_order
from orderflow.promotions import apply_promotions
from orderflow.settlement import reconcile


# --- Резервирование товара: остаток не становится отрицательным, операция атомарна ---

def test_reserve_items_is_atomic_when_second_line_is_short():
    """Граничный случай: первая позиция есть, второй не хватает -> склад не меняется."""
    stock = {"SKU-1": 10, "SKU-2": 1}
    basket = Basket(1, [Line("SKU-1", 3, 100, "office"), Line("SKU-2", 2, 100, "office")])
    assert reserve_items(basket, stock) is False
    assert stock == {"SKU-1": 10, "SKU-2": 1}


def test_reserve_items_with_repeated_sku_lines():
    """Несколько строк одного SKU в сумме превышают остаток."""
    stock = {"SKU-1": 5}
    basket = Basket(1, [Line("SKU-1", 3, 100, "office"), Line("SKU-1", 3, 100, "office")])
    assert reserve_items(basket, stock) is False
    assert stock == {"SKU-1": 5}


def test_allocate_order_with_repeated_sku_never_goes_negative():
    warehouse = Warehouse({"A": 5})
    items = [{"sku": "A", "quantity": 3}, {"sku": "A", "quantity": 3}]
    assert allocate_order(warehouse, "ORD-1", items) is False
    assert warehouse.available["A"] == 5
    assert "ORD-1" not in warehouse.reserved


def test_allocate_order_twice_with_same_reference_keeps_stock_consistent():
    """Повторная операция: повторное резервирование того же заказа не должно терять остатки."""
    warehouse = Warehouse({"A": 10})
    assert allocate_order(warehouse, "ORD-1", [{"sku": "A", "quantity": 2}])
    assert allocate_order(warehouse, "ORD-1", [{"sku": "A", "quantity": 2}]) is False
    assert warehouse.available["A"] + sum(warehouse.reserved["ORD-1"].values()) == 10


# --- Применение скидки: один и тот же код не применяется дважды ---

def test_same_coupon_is_applied_once():
    amount, applied = apply_promotions(4000, ["OFFICE7", "office7"], ["office"])
    assert (amount, applied) == (3720, ["OFFICE7"])


# --- Возврат: сумма распределения равна возвращаемой сумме ---

def test_refund_distribution_preserves_total():
    lines = [{"sku": "A", "amount": 100}, {"sku": "B", "amount": 100}, {"sku": "C", "amount": 100}]
    parts = distribute_refund(100, lines)
    assert sum(parts.values()) == 100
    assert max(parts.values()) - min(parts.values()) <= 1


# --- Сопоставление платежей: лишние и задвоенные платежи видны ---

def test_reconcile_reports_duplicate_and_unexpected_payments():
    expected = [{"reference": "r1", "amount": 10}]
    actual = [{"reference": "r1", "amount": 10}, {"reference": "r1", "amount": 10},
              {"reference": "r2", "amount": 5}]
    refs = sorted(diff["reference"] for diff in reconcile(expected, actual))
    assert refs == ["r1", "r2"]


def test_session_with_naive_timestamp_is_handled():
    from orderflow.access import session_valid
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    assert session_valid("2026-01-01T13:00:00", now) is True
    assert session_valid("2026-01-01T11:00:00", now) is False

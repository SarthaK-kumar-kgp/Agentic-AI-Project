import pytest

from taskflow.invoices import InvoiceLine, subtotal_cents, total_after_discount_cents


def test_subtotal_cents_multiplies_quantity_by_unit_price():
    lines = [
        InvoiceLine("Notebook", quantity=2, unit_price_cents=500),
        InvoiceLine("Pen", quantity=3, unit_price_cents=125),
    ]

    assert subtotal_cents(lines) == 1375


def test_total_after_discount_cents_applies_percentage_discount():
    lines = [InvoiceLine("Desk", quantity=1, unit_price_cents=20_000)]

    assert total_after_discount_cents(lines, discount_percent=15) == 17_000


def test_total_after_discount_cents_rejects_zero_discount():
    with pytest.raises(ValueError, match="discount_percent must be positive"):
        total_after_discount_cents([], discount_percent=0)

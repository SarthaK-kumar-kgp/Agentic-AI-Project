from dataclasses import dataclass

from taskflow.validation import require_positive_int


@dataclass(frozen=True)
class InvoiceLine:
    description: str
    quantity: int
    unit_price_cents: int


def subtotal_cents(lines: list[InvoiceLine]) -> int:
    total = 0
    for line in lines:
        require_positive_int(line.quantity, "quantity")
        require_positive_int(line.unit_price_cents, "unit_price_cents")
        total += line.quantity * line.unit_price_cents
    return total


def total_after_discount_cents(lines: list[InvoiceLine], discount_percent: int) -> int:
    require_positive_int(discount_percent, "discount_percent")
    subtotal = subtotal_cents(lines)
    return subtotal - discount_percent

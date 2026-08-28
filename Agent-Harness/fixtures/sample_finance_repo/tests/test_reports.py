from ledgerlite.reports import monthly_totals, top_transactions


def test_monthly_totals_groups_by_iso_month():
    transactions = [
        {"id": "a", "date": "2026-01-15", "amount_cents": 1200},
        {"id": "b", "date": "2026-01-20", "amount_cents": 800},
        {"id": "c", "date": "2026-02-01", "amount_cents": 500},
    ]

    assert monthly_totals(transactions) == {
        "2026-01": 2000,
        "2026-02": 500,
    }


def test_top_transactions_returns_largest_without_mutating_input_order():
    transactions = [
        {"id": "small", "amount_cents": 100},
        {"id": "large", "amount_cents": 900},
        {"id": "medium", "amount_cents": 500},
    ]

    result = top_transactions(transactions, 2)

    assert [item["id"] for item in result] == ["large", "medium"]
    assert [item["id"] for item in transactions] == ["small", "large", "medium"]

from ledgerlite.importer import load_transactions, normalize_date, parse_amount_cents


def test_parse_amount_cents_handles_commas_and_currency_symbol():
    assert parse_amount_cents("$1,234.50") == 123450


def test_parse_amount_cents_handles_plain_amount():
    assert parse_amount_cents("19.99") == 1999


def test_normalize_date_converts_us_date_to_iso_date():
    assert normalize_date("01/15/2026") == "2026-01-15"


def test_load_transactions_normalizes_fields():
    rows = [
        {
            "id": " tx-001 ",
            "date": "01/15/2026",
            "category": " Groceries ",
            "amount": "$12.30",
        }
    ]

    assert load_transactions(rows) == [
        {
            "id": "tx-001",
            "date": "2026-01-15",
            "category": "groceries",
            "amount_cents": 1230,
        }
    ]

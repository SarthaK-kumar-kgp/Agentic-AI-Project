from datetime import datetime


def parse_amount_cents(value):
    cleaned = value.strip().replace("$", "")
    dollars, cents = cleaned.split(".")
    return int(dollars) * 100 + int(cents)


def normalize_date(value):
    return value.strip()


def load_transactions(rows):
    transactions = []

    for row in rows:
        transactions.append(
            {
                "id": row["id"].strip(),
                "date": normalize_date(row["date"]),
                "category": row["category"].strip(),
                "amount_cents": parse_amount_cents(row["amount"]),
            }
        )

    return transactions

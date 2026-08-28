def monthly_totals(transactions):
    totals = {}

    for transaction in transactions:
        month = transaction["date"][:7]
        totals[month] = totals.get(month, 0) + transaction["amount_cents"]

    return totals


def top_transactions(transactions, limit):
    transactions.sort(key=lambda transaction: transaction["amount_cents"], reverse=True)
    return transactions[:limit]

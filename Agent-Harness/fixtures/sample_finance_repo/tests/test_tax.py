from pathlib import Path

from ledgerlite.tax import load_tax_rules, tax_cents, tax_rate_for_state


RULES_PATH = Path(__file__).resolve().parents[1] / "data" / "tax_rules.json"


def test_load_tax_rules_reads_state_rates():
    rules = load_tax_rules(RULES_PATH)

    assert rules["states"]["CA"] == 0.0825


def test_tax_rate_for_state_normalizes_state_code():
    rules = load_tax_rules(RULES_PATH)

    assert tax_rate_for_state(" ca ", rules) == 0.0825


def test_tax_rate_for_state_uses_default_for_unknown_state():
    rules = load_tax_rules(RULES_PATH)

    assert tax_rate_for_state("WA", rules) == 0.0


def test_tax_cents_rounds_to_nearest_cent():
    assert tax_cents(1999, 0.0825) == 165

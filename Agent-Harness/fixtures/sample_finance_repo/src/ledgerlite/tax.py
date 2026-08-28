import json


def load_tax_rules(path):
    with open(path) as file:
        return json.load(file)


def tax_rate_for_state(state, rules):
    return rules.get(state, rules["default_rate"])


def tax_cents(subtotal_cents, rate):
    return int(subtotal_cents * rate)

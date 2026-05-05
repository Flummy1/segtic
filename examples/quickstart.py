"""Quickstart — the five most common segtic patterns in one file.

Run:
    python examples/quickstart.py
"""

from datetime import date
from decimal import Decimal
from typing import Literal

from segtic import Field, Form, SegticParseError


# 1. Basic form — typed fields, comma-separated by default
class Order(Form):
    item: str
    quantity: int
    price: Decimal = Field(suffix='₽')

result = Order.parse('Wireless mouse, 2, 1490,00 ₽')
print(result)
# Order(item='Wireless mouse', quantity=2, price=Decimal('1490.00'))


# 2. Anchors — suffix, prefix, Literal pin a field to a recognisable token
class Topup(Form):
    service: str
    amount: int = Field(suffix='руб.')
    promo: str | None = None

print(Topup.parse('Steam, 500 руб.'))           # promo=None
print(Topup.parse('Steam, 500 руб., SALE'))     # promo='SALE'


# 3. Greedy field — swallows multiple comma-separated chunks
class Boost(Form):
    description: str = Field(greedy=True)
    currency: Literal['USD', 'RUB', 'EUR']
    price: int = Field(prefix='$')
    days: int = Field(suffix='дн.')

print(Boost.parse('arena, 2200 rating, all roles, USD, $150, 5 дн.'))
# description='arena, 2200 rating, all roles'


# 4. parse_any — try several forms, pick the most specific match
class Short(Form):
    qty: int = Field(suffix='шт.')

class Long(Form):
    qty: int = Field(suffix='шт.')
    note: str = Field(greedy=True)

print(Form.parse_any('5 шт.', [Long, Short]))           # → Short
print(Form.parse_any('5 шт., срочно', [Long, Short]))   # → Long


# 5. parse_strict — raises with diagnostics instead of returning None
class Receipt(Form):
    when: date = Field(date_format='%d.%m.%Y')
    total: Decimal = Field(suffix='₽')

try:
    Receipt.parse_strict('not-a-date, 500 ₽')
except SegticParseError as e:
    print(f'failed at {e.failed_at!r}: {e.reason}')

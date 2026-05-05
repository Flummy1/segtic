"""Marketplace batch parser — realistic multi-form scenario.

Simulates a feed of order titles from a digital-goods marketplace.
Each title may belong to one of several product categories.
parse_any picks the best-matching form per title.

Run:
    python examples/marketplace.py
"""

from typing import Literal

from segtic import Field, Form, parse_many

# --- Form definitions --------------------------------------------------------


class TelegramStars(Form):
    qty: int = Field(suffix=('звёзд', 'stars'))
    auth: str = Field(clean=True)
    username: str = Field(greedy=True)


class Topup(Form):
    service: str
    amount: int = Field(suffix='руб.')
    promo: str | None = None


class Boost(Form):
    description: str = Field(greedy=True)
    currency: Literal['USD', 'RUB', 'EUR']
    price: int = Field(prefix='$')
    days: int = Field(suffix='дн.')


class FxRate(Form):
    pair: str
    rate: float = Field(suffix='₽')


class WowChar(Form):
    class Meta:
        separator = ' | '

    realm: str
    faction: Literal['Alliance', 'Horde']
    level: int


FORMS = [TelegramStars, Topup, Boost, FxRate, WowChar]

# --- Feed --------------------------------------------------------------------

TITLES = [
    '50 звёзд, по логину, @nick',
    '100 stars, login, @shop, gift',
    'Steam, 500 руб.',
    'Xbox, 750 руб., SALE2026',
    'boost, mythic+, all roles, USD, $250, 3 дн.',
    'arena, 2200 rating, EUR, $800, 14 дн.',
    'USD/RUB, 95,42 ₽',
    'EUR/RUB, 105,30 ₽',
    'Stormrage | Alliance | 70',
    'Silvermoon | Horde | 60',
    'completely unrecognised title',
]

# --- Parse and report --------------------------------------------------------

results = parse_many(TITLES, FORMS)

width = max(len(t) for t in TITLES)
print(f'{"Title":<{width}}   Result')
print('-' * (width + 40))
for title, result in zip(TITLES, results, strict=True):
    label = '—  (no match)' if result is None else f'{type(result).__name__}  {result}'
    print(f'{title:<{width}}   {label}')

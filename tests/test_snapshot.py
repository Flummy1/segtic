"""Snapshot test on a small fixture of real-world style titles.

Pins the percentage of successful matches across releases — drops should be
investigated, not silently shipped.
"""

from pathlib import Path
from typing import Literal

from segtic import Field, Form

FIXTURE = Path(__file__).parent / 'fixtures' / 'marketplace_titles.txt'


class TelegramStars(Form):
    qty: int = Field(suffix=('звёзд', 'stars'))
    auth: str = Field(clean=True)
    user: str = Field(greedy=True)


class Topup(Form):
    service: str
    amount: int = Field(suffix='руб.')
    promo: str | None = None


class TopupReverse(Form):
    amount: int = Field(suffix='руб.')
    service: str


class Boost(Form):
    description: str = Field(greedy=True)
    cur: Literal['USD', 'RUB', 'EUR']
    price: int = Field(prefix='$')
    delivery: int = Field(suffix='дн.')


class FxRate(Form):
    pair: str
    rate: float = Field(suffix='₽')


class Region(Form):
    flag: Literal['RU', 'USA'] = Field(clean=True)
    qty: int


class WowChar(Form):
    class Meta:
        separator = ' | '

    realm: str
    faction: Literal['Alliance', 'Horde']
    level: int


class Triple(Form):
    a: str
    b: str
    c: int


VARIANTS = [TelegramStars, Topup, TopupReverse, Boost, FxRate, Region, WowChar, Triple]


def test_snapshot_match_rate() -> None:
    titles = [
        line.strip()
        for line in FIXTURE.read_text().splitlines()
        if line.strip() and not line.startswith('#')
    ]
    matched = sum(1 for t in titles if Form.parse_any(t, VARIANTS) is not None)
    rate = matched / len(titles)
    # Floor ratchet: tighten as parsing improves; drops below this fail CI.
    assert rate >= 0.9, f'match rate dropped to {rate:.0%} ({matched}/{len(titles)})'

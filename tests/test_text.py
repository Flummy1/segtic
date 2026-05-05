from __future__ import annotations

import pytest

from segtic import clean_decorations
from segtic._text import has_affix


@pytest.mark.parametrize(
    'raw, expected',
    [
        ('🇺🇸 USA ⭐', 'USA'),
        ('💎 Premium 💎', 'Premium'),
        ('🚀 Boost 🔥', 'Boost'),
        ('✅ done ✨', 'done'),
        ('🀄 mahjong', 'mahjong'),
        ('♠ ace ♣', 'ace'),
        ('  spaced   out  ', 'spaced out'),
        ('—dash—', 'dash'),
        ('plain', 'plain'),
    ],
)
def test_clean_decorations(raw: str, expected: str) -> None:
    assert clean_decorations(raw) == expected


def test_has_affix_empty_is_true() -> None:
    assert has_affix('anything', (), side='prefix') is True
    assert has_affix('anything', '', side='suffix') is True


def test_has_affix_str() -> None:
    assert has_affix('100 stars', 'stars', side='suffix')
    assert not has_affix('100 stars', 'rubles', side='suffix')


def test_has_affix_tuple_casefold() -> None:
    assert has_affix('100 STARS', ('stars', 'звёзд'), side='suffix')
    assert has_affix('$250', '$', side='prefix')

from __future__ import annotations

from typing import Literal

from segtic import Field, Form


def test_silent_numeric_none_rejected() -> None:
    """suffix matches but no digits → must NOT yield qty=None silently."""

    class S(Form):
        qty: int = Field(suffix='шт.')

    # With suffix-anchor int field requires digits in segment, so this fails
    # at matches() — but ensure even a digitless suffix-bearing string fails.
    assert S.parse('many шт.') is None


def test_multi_greedy_with_anchor() -> None:
    class S(Form):
        head: str = Field(greedy=True)
        cur: Literal['USD', 'RUB']
        tail: str = Field(greedy=True)

    res = S.parse('a, b, c, USD, x, y')
    assert res == S(head='a, b, c', cur='USD', tail='x, y')


def test_segment_count_mismatch() -> None:
    class S(Form):
        a: str
        b: str

    assert S.parse('only-one') is None
    assert S.parse('a, b, c') is None


def test_empty_title() -> None:
    class S(Form):
        a: str

    assert S.parse('') is None

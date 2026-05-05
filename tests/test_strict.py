from __future__ import annotations

from typing import Literal

import pytest

from segtic import (
    Field,
    Form,
    SegticAmbiguousError,
    SegticParseError,
    parse_strict,
)


def test_parse_strict_segment_count() -> None:
    class S(Form):
        a: str
        b: str

    with pytest.raises(SegticParseError) as ei:
        S.parse_strict('only-one')
    assert 'expected 2 segments' in ei.value.reason
    assert ei.value.failed_at is None
    assert ei.value.form_name == 'S'


def test_parse_strict_anchor_mismatch() -> None:
    class S(Form):
        qty: int = Field(suffix='звёзд')

    with pytest.raises(SegticParseError) as ei:
        S.parse_strict('100 stars')
    assert ei.value.failed_at == 'qty'


def test_parse_strict_literal_mismatch() -> None:
    class S(Form):
        cur: Literal['USD', 'RUB']
        amt: int

    with pytest.raises(SegticParseError) as ei:
        S.parse_strict('JPY, 50')
    assert ei.value.failed_at == 'cur'


def test_parse_strict_top_level_function_with_dataclass() -> None:
    from dataclasses import dataclass

    @dataclass
    class D:
        a: str
        b: int

    with pytest.raises(SegticParseError):
        parse_strict('only-one', D)


def test_parse_any_strict_raises_on_ambiguity() -> None:
    class A(Form):
        x: str
        y: int

    class B(Form):
        x: str
        y: int

    with pytest.raises(SegticAmbiguousError) as ei:
        Form.parse_any('foo, 5', [A, B], strict=True)
    assert 'A' in ei.value.candidates and 'B' in ei.value.candidates


def test_parse_any_strict_no_ambiguity_passes() -> None:
    class A(Form):
        qty: int = Field(suffix='шт.')

    class B(Form):
        qty: int = Field(suffix='шт.')
        note: str = Field(greedy=True)

    # Different specificity — no ambiguity, even with strict=True.
    assert Form.parse_any('5 шт., note', [A, B], strict=True) == B(qty=5, note='note')

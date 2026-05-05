from __future__ import annotations

from typing import Literal

from segtic import Field, Form, parse_many


def test_minimal() -> None:
    class S(Form):
        a: str
        b: str
        c: int

    assert S.parse('foo, bar, 42') == S(a='foo', b='bar', c=42)


def test_suffix_anchor() -> None:
    class S(Form):
        qty: int = Field(suffix=('звёзд', 'stars'))
        user: str = Field(greedy=True)

    assert S.parse('100 stars, @nick, more') == S(qty=100, user='@nick, more')


def test_prefix_anchor() -> None:
    class S(Form):
        title: str = Field(greedy=True)
        price: int = Field(prefix='$')

    assert S.parse('item, with, commas, $250') == S(title='item, with, commas', price=250)


def test_optional_via_pipe_none() -> None:
    class S(Form):
        qty: int = Field(suffix='шт.')
        region: str | None = None

    assert S.parse('5 шт.') == S(qty=5, region=None)
    assert S.parse('5 шт., RU') == S(qty=5, region='RU')


def test_literal() -> None:
    class S(Form):
        desc: str = Field(greedy=True)
        cur: Literal['USD', 'RUB']
        amt: int

    assert S.parse('a, b, c, USD, 50') == S(desc='a, b, c', cur='USD', amt=50)


def test_parse_any_picks_fattest_regardless_of_order() -> None:
    class A(Form):
        qty: int = Field(suffix='звёзд')

    class B(Form):
        qty: int = Field(suffix='звёзд')
        user: str = Field(greedy=True)

    for variants in ([A, B], [B, A]):
        assert Form.parse_any('100 звёзд', variants) == A(qty=100)
        assert Form.parse_any('100 звёзд, @nick', variants) == B(qty=100, user='@nick')


def test_clean_strips_emoji() -> None:
    class S(Form):
        flag: Literal['Russia', 'USA'] = Field(clean=True)
        qty: int

    assert S.parse('🇺🇸 USA ⭐, 5') == S(flag='USA', qty=5)


def test_float() -> None:
    class S(Form):
        pair: str
        rate: float = Field(suffix='₽')

    assert S.parse('USD/RUB, 95,42 ₽') == S(pair='USD/RUB', rate=95.42)


def test_custom_separator() -> None:
    class S(Form):
        separator = ' | '
        a: str
        b: str
        c: int

    assert S.parse('x | y | 1') == S(a='x', b='y', c=1)


def test_failure_returns_none() -> None:
    class S(Form):
        qty: int = Field(suffix='звёзд')

    assert S.parse('totally unrelated string') is None


def test_pattern_regex_anchor() -> None:
    class S(Form):
        phone: str = Field(pattern=r'\+\d{11}')
        name: str

    assert S.parse('+71234567890, alice') == S(phone='+71234567890', name='alice')
    assert S.parse('not-a-phone, alice') is None


def test_pattern_combined_with_prefix() -> None:
    class S(Form):
        code: str = Field(prefix='ID-', pattern=r'ID-\d{4}')

    assert S.parse('ID-1234') == S(code='ID-1234')
    assert S.parse('ID-12') is None
    assert S.parse('XX-1234') is None


def test_meta_separator() -> None:
    class S(Form):
        class Meta:
            separator = ' | '

        a: str
        b: int

    assert S.parse('foo | 7') == S(a='foo', b=7)


def test_legacy_class_attr_separator_still_works() -> None:
    class S(Form):
        separator = ' / '
        a: str
        b: str

    assert S.parse('x / y') == S(a='x', b='y')


def test_parse_many_single_form() -> None:
    class S(Form):
        a: str
        b: int

    assert parse_many(['x, 1', 'y, 2', 'bad'], S) == [
        S(a='x', b=1),
        S(a='y', b=2),
        None,
    ]


def test_parse_many_variants() -> None:
    class A(Form):
        qty: int = Field(suffix='шт.')

    class B(Form):
        qty: int = Field(suffix='шт.')
        note: str = Field(greedy=True)

    out = parse_many(['5 шт.', '5 шт., note', 'bogus'], [A, B])
    assert out == [A(qty=5), B(qty=5, note='note'), None]

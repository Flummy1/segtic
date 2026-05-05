from datetime import date, datetime
from decimal import Decimal
from enum import Enum

import pytest

from segtic import Field, Form, register_kind, register_type


def test_bool_default_tokens() -> None:
    class S(Form):
        active: bool
        n: int

    assert S.parse('yes, 5') == S(active=True, n=5)
    assert S.parse('NO, 5') == S(active=False, n=5)
    assert S.parse('да, 5') == S(active=True, n=5)
    assert S.parse('нет, 5') == S(active=False, n=5)


def test_bool_custom_tokens() -> None:
    class S(Form):
        flag: bool = Field(bool_true=('включено',), bool_false=('выключено',))

    assert S.parse('включено') == S(flag=True)
    assert S.parse('выключено') == S(flag=False)
    assert S.parse('yes') is None  # not in custom tokens


def test_enum_str_value() -> None:
    class Currency(str, Enum):
        USD = 'USD'
        RUB = 'RUB'

    class S(Form):
        cur: Currency
        amt: int

    assert S.parse('USD, 50') == S(cur=Currency.USD, amt=50)
    assert S.parse('rub, 30') == S(cur=Currency.RUB, amt=30)
    assert S.parse('JPY, 50') is None


def test_enum_int_value() -> None:
    class Tier(Enum):
        FREE = 0
        PRO = 1

    class S(Form):
        tier: Tier

    assert S.parse('1') == S(tier=Tier.PRO)


def test_decimal() -> None:
    class S(Form):
        price: Decimal = Field(suffix='₽')

    res = S.parse('1234,56 ₽')
    assert res is not None and res.price == Decimal('1234.56')


def test_date_iso() -> None:
    class S(Form):
        when: date

    assert S.parse('2026-05-05') == S(when=date(2026, 5, 5))


def test_date_custom_format() -> None:
    class S(Form):
        when: date = Field(date_format='%d.%m.%Y')

    assert S.parse('05.05.2026') == S(when=date(2026, 5, 5))


def test_datetime_iso() -> None:
    class S(Form):
        ts: datetime

    res = S.parse('2026-05-05T12:30:00')
    assert res == S(ts=datetime(2026, 5, 5, 12, 30, 0))


def test_register_type_custom() -> None:
    class IPv4:
        def __init__(self, value: str) -> None:
            parts = value.split('.')
            if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) < 256 for p in parts):
                raise ValueError(value)
            self.value = value

        def __eq__(self, other: object) -> bool:
            return isinstance(other, IPv4) and other.value == self.value

    def _ip_match(s: str, spec) -> bool:  # type: ignore[no-untyped-def]
        try:
            IPv4(s.strip())
            return True
        except ValueError:
            return False

    def _ip_coerce(s: str, spec) -> IPv4:  # type: ignore[no-untyped-def]
        return IPv4(s.strip())

    register_kind('ipv4', matcher=_ip_match, coercer=_ip_coerce)
    register_type(lambda tp: ('ipv4', (), {}) if tp is IPv4 else None)

    class S(Form):
        host: IPv4
        port: int

    assert S.parse('10.0.0.1, 8080') == S(host=IPv4('10.0.0.1'), port=8080)
    assert S.parse('not-an-ip, 8080') is None


def test_bool_with_emoji_and_clean() -> None:
    class S(Form):
        flag: bool = Field(clean=True)

    res = S.parse('✅ yes')
    assert res == S(flag=True)


@pytest.mark.parametrize('text', ['maybe', 'kinda'])
def test_bool_invalid(text: str) -> None:
    class S(Form):
        flag: bool

    assert S.parse(text) is None


def test_list_of_str() -> None:
    class S(Form):
        tags: list[str] = Field(item_separator=';')
        n: int

    assert S.parse('alpha;beta;gamma, 5') == S(tags=['alpha', 'beta', 'gamma'], n=5)


def test_list_of_int() -> None:
    class S(Form):
        ids: list[int] = Field(item_separator=';')

    assert S.parse('1;2;3') == S(ids=[1, 2, 3])
    assert S.parse('1;abc;3') is None


def test_list_default_separator() -> None:
    class S(Form):
        tags: list[str]
        n: int

    assert S.parse('a;b, 1') == S(tags=['a', 'b'], n=1)

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal

import pytest

from segtic._types import (
    KIND_BOOL,
    KIND_DATE,
    KIND_DATETIME,
    KIND_DECIMAL,
    KIND_ENUM,
    KIND_FLOAT,
    KIND_INT,
    KIND_LITERAL,
    KIND_STRING,
    resolve_kind,
)


def test_resolve_str() -> None:
    kind, values, optional, extras = resolve_kind(str)
    assert kind == KIND_STRING and values == () and not optional and extras == {}


def test_resolve_int() -> None:
    assert resolve_kind(int)[0] == KIND_INT


def test_resolve_float() -> None:
    assert resolve_kind(float)[0] == KIND_FLOAT


def test_resolve_bool_before_int() -> None:
    assert resolve_kind(bool)[0] == KIND_BOOL


def test_resolve_decimal() -> None:
    assert resolve_kind(Decimal)[0] == KIND_DECIMAL


def test_resolve_date_and_datetime() -> None:
    assert resolve_kind(date)[0] == KIND_DATE
    assert resolve_kind(datetime)[0] == KIND_DATETIME


def test_resolve_enum() -> None:
    class Color(Enum):
        RED = 'red'
        BLUE = 'blue'

    kind, values, _, extras = resolve_kind(Color)
    assert kind == KIND_ENUM
    assert values == ('red', 'blue')
    assert extras['enum_class'] is Color


def test_resolve_literal() -> None:
    kind, values, optional, _ = resolve_kind(Literal['A', 'B'])
    assert kind == KIND_LITERAL
    assert values == ('A', 'B')
    assert optional is False


def test_resolve_optional() -> None:
    kind, _, optional, _ = resolve_kind(str | None)
    assert kind == KIND_STRING
    assert optional is True


def test_resolve_unsupported() -> None:
    with pytest.raises(TypeError):
        resolve_kind(list)

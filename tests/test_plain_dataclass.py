from __future__ import annotations

from dataclasses import dataclass

from segtic import parse


def test_plain_dataclass() -> None:
    @dataclass
    class D:
        a: str
        b: int

    assert parse('hello, 7', D) == D(a='hello', b=7)


def test_plain_dataclass_failure_returns_none() -> None:
    @dataclass
    class D:
        a: str
        b: int

    assert parse('not enough', D) is None

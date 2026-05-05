"""Registry of field kinds: matcher + coercer per kind name.

A *kind* is a string identifier (``'string'``, ``'int'``, ``'bool'``, …) attached
to every :class:`~segtic._spec.Spec`. The matcher decides whether a raw segment
*could* be this kind; the coercer turns the segment into the final Python value.
Custom kinds can be registered via :func:`register_kind`.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import TYPE_CHECKING, Any

from ._text import clean_decorations, has_affix

if TYPE_CHECKING:
    from ._spec import Spec


Matcher = Callable[[str, 'Spec'], bool]
Coercer = Callable[[str, 'Spec'], Any]


@dataclass(frozen=True)
class KindHandler:
    matcher: Matcher
    coercer: Coercer
    numeric: bool = False  # numeric kinds reject None coercion as a hard fail


_REGISTRY: dict[str, KindHandler] = {}


def register_kind(name: str, *, matcher: Matcher, coercer: Coercer, numeric: bool = False) -> None:
    """Register or override a kind handler."""
    _REGISTRY[name] = KindHandler(matcher=matcher, coercer=coercer, numeric=numeric)


def get_kind(name: str) -> KindHandler:
    return _REGISTRY[name]


def is_numeric(name: str) -> bool:
    handler = _REGISTRY.get(name)
    return bool(handler and handler.numeric)


# ---------- built-in kinds --------------------------------------------------


def _affix_ok(text: str, spec: Spec) -> bool:
    if not has_affix(text, spec.prefix, side='prefix'):
        return False
    if not has_affix(text, spec.suffix, side='suffix'):
        return False
    return not (spec.pattern is not None and not spec.pattern.fullmatch(text.strip()))


def _string_match(s: str, spec: Spec) -> bool:
    chk = clean_decorations(s) if spec.clean else s
    return _affix_ok(chk, spec)


def _string_coerce(s: str, spec: Spec) -> str:
    return clean_decorations(s) if spec.clean else s.strip()


def _int_match(s: str, spec: Spec) -> bool:
    return bool(re.search(r'\d', s)) and _affix_ok(s, spec)


def _int_coerce(s: str, spec: Spec) -> int | None:
    cleaned = re.sub(r'[\s\xa0]', '', s)
    m = re.search(r'-?\d+(?:[.,]\d{3})*(?!\d)|-?\d+', cleaned)
    return int(re.sub(r'[.,]', '', m.group())) if m else None


def _float_match(s: str, spec: Spec) -> bool:
    return bool(re.search(r'\d', s)) and _affix_ok(s, spec)


def _float_coerce(s: str, spec: Spec) -> float | None:
    m = re.search(r'-?\d+(?:[.,]\d+)?', s)
    return float(m.group().replace(',', '.')) if m else None


def _decimal_coerce(s: str, spec: Spec) -> Decimal | None:
    m = re.search(r'-?\d+(?:[.,]\d+)?', s)
    if not m:
        return None
    try:
        return Decimal(m.group().replace(',', '.'))
    except InvalidOperation:
        return None


def _literal_match(s: str, spec: Spec) -> bool:
    c = (clean_decorations(s) if spec.clean else s.strip()).casefold()
    return any(c == str(v).casefold() for v in spec.values)


def _literal_coerce(s: str, spec: Spec) -> str:
    return clean_decorations(s) if spec.clean else s.strip()


_DEFAULT_TRUE = ('true', 'yes', 'y', '1', '+', 'on', 'да')
_DEFAULT_FALSE = ('false', 'no', 'n', '0', '-', 'off', 'нет')


def _bool_tokens(spec: Spec) -> tuple[tuple[str, ...], tuple[str, ...]]:
    extras = spec.extras
    t = tuple(extras.get('bool_true', _DEFAULT_TRUE))
    f = tuple(extras.get('bool_false', _DEFAULT_FALSE))
    return t, f


def _bool_match(s: str, spec: Spec) -> bool:
    if not _affix_ok(s, spec):
        return False
    cleaned = (clean_decorations(s) if spec.clean else s.strip()).casefold()
    t, f = _bool_tokens(spec)
    return cleaned in t or cleaned in f


def _bool_coerce(s: str, spec: Spec) -> bool | None:
    cleaned = (clean_decorations(s) if spec.clean else s.strip()).casefold()
    t, f = _bool_tokens(spec)
    if cleaned in t:
        return True
    if cleaned in f:
        return False
    return None


def _enum_match(s: str, spec: Spec) -> bool:
    enum_cls: type[Enum] = spec.extras['enum_class']
    cleaned = (clean_decorations(s) if spec.clean else s.strip()).casefold()
    return any(cleaned == str(m.value).casefold() for m in enum_cls)


def _enum_coerce(s: str, spec: Spec) -> Enum | None:
    enum_cls: type[Enum] = spec.extras['enum_class']
    cleaned = (clean_decorations(s) if spec.clean else s.strip()).casefold()
    for m in enum_cls:
        if cleaned == str(m.value).casefold():
            return m
    return None


def _parse_date_value(s: str, spec: Spec) -> date | datetime | None:
    fmt = spec.extras.get('date_format')
    text = clean_decorations(s) if spec.clean else s.strip()
    if fmt:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        try:
            return date.fromisoformat(text)
        except ValueError:
            return None


def _date_match(s: str, spec: Spec) -> bool:
    if not _affix_ok(s, spec):
        return False
    return _parse_date_value(s, spec) is not None


def _date_coerce(s: str, spec: Spec) -> date | None:
    v = _parse_date_value(s, spec)
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    return v


def _datetime_match(s: str, spec: Spec) -> bool:
    if not _affix_ok(s, spec):
        return False
    return _parse_date_value(s, spec) is not None


def _datetime_coerce(s: str, spec: Spec) -> datetime | None:
    v = _parse_date_value(s, spec)
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    return None


# Registration -----------------------------------------------------------------

register_kind('string', matcher=_string_match, coercer=_string_coerce)
register_kind('int', matcher=_int_match, coercer=_int_coerce, numeric=True)
register_kind('float', matcher=_float_match, coercer=_float_coerce, numeric=True)
register_kind('decimal', matcher=_float_match, coercer=_decimal_coerce, numeric=True)
register_kind('literal', matcher=_literal_match, coercer=_literal_coerce)
register_kind('bool', matcher=_bool_match, coercer=_bool_coerce)
register_kind('enum', matcher=_enum_match, coercer=_enum_coerce)
register_kind('date', matcher=_date_match, coercer=_date_coerce)
register_kind('datetime', matcher=_datetime_match, coercer=_datetime_coerce)


def _make_item_spec(parent: Spec) -> Spec:
    """Build a transient :class:`Spec` for the inner items of a list field."""
    from ._spec import Spec as _Spec

    return _Spec(
        name=f'{parent.name}[]',
        kind=parent.extras['item_kind'],
        clean=parent.clean,
        values=parent.extras.get('item_values', ()),
        extras=parent.extras.get('item_extras', {}),
    )


def _list_items(s: str, spec: Spec) -> list[str]:
    item_sep = spec.extras.get('item_separator', ';')
    parts = [p.strip() for p in s.split(item_sep)]
    return [p for p in parts if p]


def _list_match(s: str, spec: Spec) -> bool:
    if not _affix_ok(s, spec):
        return False
    items = _list_items(s, spec)
    if not items:
        return False
    inner = _make_item_spec(spec)
    inner_handler = get_kind(inner.kind)
    return all(inner_handler.matcher(item, inner) for item in items)


def _list_coerce(s: str, spec: Spec) -> list[Any] | None:
    items = _list_items(s, spec)
    inner = _make_item_spec(spec)
    inner_handler = get_kind(inner.kind)
    out: list[Any] = []
    for item in items:
        v = inner_handler.coercer(item, inner)
        if v is None and inner_handler.numeric:
            return None
        out.append(v)
    return out


register_kind('list', matcher=_list_match, coercer=_list_coerce)

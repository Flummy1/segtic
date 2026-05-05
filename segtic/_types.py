"""Map Python type annotations to segtic kind names + extras."""

from __future__ import annotations

import types
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal, Union, get_args, get_origin

# Re-exported for backward compat with older imports.
KIND_STRING = 'string'
KIND_INT = 'int'
KIND_FLOAT = 'float'
KIND_LITERAL = 'literal'
KIND_BOOL = 'bool'
KIND_ENUM = 'enum'
KIND_DATE = 'date'
KIND_DATETIME = 'datetime'
KIND_DECIMAL = 'decimal'
KIND_LIST = 'list'


# Result: (kind_name, literal_values, extras_dict).
TypeResolver = Callable[[Any], 'tuple[str, tuple[Any, ...], dict[str, Any]] | None']


_RESOLVERS: list[TypeResolver] = []


def register_type(resolver: TypeResolver) -> None:
    """Register a custom type resolver.

    Resolvers are tried in registration order; the first non-None result wins.
    Built-ins are tried last, so a custom resolver can override them.
    """
    _RESOLVERS.append(resolver)


def _resolve_builtin(tp: Any) -> tuple[str, tuple[Any, ...], dict[str, Any]] | None:
    if tp is str:
        return KIND_STRING, (), {}
    if tp is bool:  # must be checked before int (bool is a subclass of int)
        return KIND_BOOL, (), {}
    if tp is int:
        return KIND_INT, (), {}
    if tp is float:
        return KIND_FLOAT, (), {}
    if tp is Decimal:
        return KIND_DECIMAL, (), {}
    if tp is datetime:
        return KIND_DATETIME, (), {}
    if tp is date:
        return KIND_DATE, (), {}
    if isinstance(tp, type) and issubclass(tp, Enum):
        return KIND_ENUM, tuple(m.value for m in tp), {'enum_class': tp}
    return None


def resolve_kind(tp: Any) -> tuple[str, tuple[Any, ...], bool, dict[str, Any]]:
    """Return ``(kind, literal_values, optional, extras)``."""
    optional = False
    origin = get_origin(tp)
    if origin is Union or origin is types.UnionType:
        args = get_args(tp)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) != len(args):
            optional = True
        if len(non_none) == 1:
            tp = non_none[0]
            origin = get_origin(tp)
    if origin is Literal:
        return KIND_LITERAL, tuple(get_args(tp)), optional, {}
    if origin is list:
        (item_type,) = get_args(tp)
        item_kind, item_values, _, item_extras = resolve_kind(item_type)
        return (
            KIND_LIST,
            (),
            optional,
            {
                'item_kind': item_kind,
                'item_values': item_values,
                'item_extras': item_extras,
            },
        )
    for resolver in _RESOLVERS:
        result = resolver(tp)
        if result is not None:
            kind, values, extras = result
            return kind, values, optional, extras
    builtin = _resolve_builtin(tp)
    if builtin is not None:
        kind, values, extras = builtin
        return kind, values, optional, extras
    raise TypeError(f'unsupported field type: {tp!r}')

"""Per-field configuration and the runtime spec used by the parser."""

from __future__ import annotations

import dataclasses
import re
from dataclasses import MISSING
from typing import Any, get_type_hints

from ._kinds import get_kind
from ._types import resolve_kind

FIELD_META_KEY = '_segtic_field_config'


class _FieldConfig:
    __slots__ = ('suffix', 'prefix', 'pattern', 'greedy', 'clean', 'extras')

    def __init__(
        self,
        *,
        suffix: str | tuple[str, ...] = (),
        prefix: str | tuple[str, ...] = (),
        pattern: str | None = None,
        greedy: bool = False,
        clean: bool = False,
        extras: dict[str, Any] | None = None,
    ) -> None:
        self.suffix = suffix
        self.prefix = prefix
        self.pattern = pattern
        self.greedy = greedy
        self.clean = clean
        self.extras: dict[str, Any] = dict(extras) if extras else {}


def Field(
    *,
    default: Any = MISSING,
    default_factory: Any = MISSING,
    suffix: str | tuple[str, ...] = (),
    prefix: str | tuple[str, ...] = (),
    pattern: str | None = None,
    greedy: bool = False,
    clean: bool = False,
    bool_true: tuple[str, ...] | None = None,
    bool_false: tuple[str, ...] | None = None,
    date_format: str | None = None,
    item_separator: str | None = None,
) -> Any:
    """Per-field configuration, used as default value (pydantic-style)::

    quantity: int = Field(suffix='звёзд')
    username: str = Field(greedy=True)
    when: date = Field(date_format='%d.%m.%Y')
    """
    extras: dict[str, Any] = {}
    if bool_true is not None:
        extras['bool_true'] = tuple(bool_true)
    if bool_false is not None:
        extras['bool_false'] = tuple(bool_false)
    if date_format is not None:
        extras['date_format'] = date_format
    if item_separator is not None:
        extras['item_separator'] = item_separator
    cfg = _FieldConfig(
        suffix=suffix,
        prefix=prefix,
        pattern=pattern,
        greedy=greedy,
        clean=clean,
        extras=extras,
    )
    meta = {FIELD_META_KEY: cfg}
    if default_factory is not MISSING:
        return dataclasses.field(default_factory=default_factory, metadata=meta)
    if default is not MISSING:
        return dataclasses.field(default=default, metadata=meta)
    return dataclasses.field(metadata=meta)


class Spec:
    """Runtime description of one field used by the parser."""

    __slots__ = (
        'name',
        'kind',
        'greedy',
        'optional',
        'clean',
        'suffix',
        'prefix',
        'pattern',
        'values',
        'extras',
    )

    def __init__(
        self,
        name: str,
        kind: str,
        *,
        greedy: bool = False,
        optional: bool = False,
        clean: bool = False,
        suffix: str | tuple[str, ...] = (),
        prefix: str | tuple[str, ...] = (),
        pattern: re.Pattern[str] | None = None,
        values: tuple[Any, ...] = (),
        extras: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.kind = kind
        self.greedy = greedy
        self.optional = optional
        self.clean = clean
        self.suffix = suffix
        self.prefix = prefix
        self.pattern = pattern
        self.values = values
        self.extras: dict[str, Any] = dict(extras) if extras else {}

    def matches(self, s: str) -> bool:
        return get_kind(self.kind).matcher(s, self)

    def coerce(self, s: str) -> Any:
        return get_kind(self.kind).coercer(s, self)


def build_specs(cls: type) -> list[Spec]:
    """Inspect a dataclass and produce a list of :class:`Spec` objects."""
    hints = get_type_hints(cls)
    specs: list[Spec] = []
    for f in dataclasses.fields(cls):
        tp = hints.get(f.name, f.type)
        kind, values, optional, type_extras = resolve_kind(tp)
        cfg: _FieldConfig | None = f.metadata.get(FIELD_META_KEY) if f.metadata else None
        if cfg is None:
            cfg = _FieldConfig()
        merged_extras = {**type_extras, **cfg.extras}
        compiled_pattern: re.Pattern[str] | None = (
            re.compile(cfg.pattern) if cfg.pattern is not None else None
        )
        specs.append(
            Spec(
                name=f.name,
                kind=kind,
                greedy=cfg.greedy,
                optional=optional,
                clean=cfg.clean,
                suffix=cfg.suffix,
                prefix=cfg.prefix,
                pattern=compiled_pattern,
                values=values,
                extras=merged_extras,
            )
        )
    return specs

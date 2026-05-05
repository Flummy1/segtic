"""High-level :class:`Form` base class and the public ``parse`` function."""

from __future__ import annotations

import contextlib
import dataclasses
from collections.abc import Iterable
from typing import Any, ClassVar, TypeVar

from ._errors import SegticAmbiguousError, SegticParseError
from ._parser import diagnose, parse_segments, specificity
from ._spec import Spec, build_specs

F = TypeVar('F', bound='Form')


def _raise_parse_error(title: str, sep: str, specs: list[Spec], form_name: str) -> None:
    fail = diagnose(title, specs, sep)
    raise SegticParseError(
        title=title,
        segments=title.split(sep) if title else [],
        form_name=form_name,
        reason=fail.reason,
        failed_at=fail.failed_at,
    )


class Form:
    """Base class for title forms. Subclass and declare typed fields::

    class MyForm(Form):
        currency: str
        amount: int = Field(suffix='руб.')
    """

    separator: ClassVar[str] = ', '
    __segtic_specs__: ClassVar[list[Spec]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Pull options from an inner ``Meta`` class if present.
        meta = cls.__dict__.get('Meta')
        if meta is not None:
            sep = getattr(meta, 'separator', None)
            if sep is not None:
                cls.separator = sep
        if not dataclasses.is_dataclass(cls):
            dataclasses.dataclass(cls)
        cls.__segtic_specs__ = build_specs(cls)

    @classmethod
    def parse(cls: type[F], title: str, *, separator: str | None = None) -> F | None:
        sep = separator if separator is not None else cls.separator
        data = parse_segments(title, cls.__segtic_specs__, sep)
        if data is None:
            return None
        return cls(**data)

    @classmethod
    def parse_strict(cls: type[F], title: str, *, separator: str | None = None) -> F:
        """Like :meth:`parse`, but raises :class:`SegticParseError` on failure."""
        sep = separator if separator is not None else cls.separator
        data = parse_segments(title, cls.__segtic_specs__, sep)
        if data is None:
            _raise_parse_error(title, sep, cls.__segtic_specs__, cls.__name__)
        assert data is not None  # for type-checker
        return cls(**data)

    @classmethod
    def parse_any(
        cls,
        title: str,
        forms: Iterable[type[Form]],
        *,
        separator: str | None = None,
        strict: bool = False,
    ) -> Form | None:
        """Iterate `forms`, return the result of the most specific successful match.

        Specificity = sum over fields: anchored (suffix/prefix/Literal) +3,
        non-greedy +2, greedy +1, optional −1. Tie-break by declaration order.

        If ``strict=True``, raise :class:`SegticAmbiguousError` when two or more
        forms match the title with the same specificity score.
        """
        best: Form | None = None
        best_score: int | None = None
        best_idx: int | None = None
        tied: list[str] = []
        for idx, form in enumerate(forms):
            res = form.parse(title) if separator is None else form.parse(title, separator=separator)
            if res is None:
                continue
            score = specificity(form)
            if best is None or (best_score is not None and score > best_score):
                best, best_score, best_idx = res, score, idx
                tied = [form.__name__]
            elif best_score is not None and score == best_score:
                tied.append(form.__name__)
                if best_idx is not None and idx < best_idx:
                    best, best_idx = res, idx
        if strict and len(tied) > 1:
            raise SegticAmbiguousError(title=title, candidates=tied)
        return best


def parse_many(
    titles: Iterable[str],
    forms: type[Form] | Iterable[type[Form]],
    *,
    separator: str | None = None,
) -> list[Form | None]:
    """Parse a batch of titles. Pass a single Form class or a list of variants.

    For variants, :meth:`Form.parse_any` is used per title with default scoring.
    """
    if isinstance(forms, type) and issubclass(forms, Form):
        single: type[Form] = forms
        return [
            single.parse(t) if separator is None else single.parse(t, separator=separator)
            for t in titles
        ]
    variants = list(forms)
    return [Form.parse_any(t, variants, separator=separator) for t in titles]


def parse(title: str, obj_to_create: type, *, separator: str = ', ') -> Any:
    """Parse ``title`` into an instance of a :class:`Form` or a plain dataclass."""
    if isinstance(obj_to_create, type) and issubclass(obj_to_create, Form):
        return obj_to_create.parse(title, separator=separator)
    if dataclasses.is_dataclass(obj_to_create):
        specs = _cached_specs(obj_to_create)
        data = parse_segments(title, specs, separator)
        if data is None:
            return None
        return obj_to_create(**data)
    raise TypeError(f'obj_to_create must be a Form subclass or dataclass; got {obj_to_create!r}')


def _cached_specs(cls: type) -> list[Spec]:
    cached = cls.__dict__.get('__segtic_specs__')
    if cached is None:
        cached = build_specs(cls)
        # frozen / __slots__ class → fall back to recomputing each call.
        with contextlib.suppress(AttributeError, TypeError):
            cls.__segtic_specs__ = cached  # type: ignore[attr-defined]
    return cached


def parse_strict(title: str, obj_to_create: type, *, separator: str = ', ') -> Any:
    """Strict variant of :func:`parse` — raises :class:`SegticParseError` on failure."""
    if isinstance(obj_to_create, type) and issubclass(obj_to_create, Form):
        return obj_to_create.parse_strict(title, separator=separator)
    if dataclasses.is_dataclass(obj_to_create):
        specs = _cached_specs(obj_to_create)
        data = parse_segments(title, specs, separator)
        if data is None:
            _raise_parse_error(title, separator, specs, obj_to_create.__name__)
        assert data is not None
        return obj_to_create(**data)
    raise TypeError(f'obj_to_create must be a Form subclass or dataclass; got {obj_to_create!r}')

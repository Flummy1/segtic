"""Public exception types raised by strict parsing entry-points."""

from __future__ import annotations


class SegticError(Exception):
    """Base class for all segtic errors."""


class SegticParseError(SegticError):
    """Strict parse failed for a single form.

    Attributes:
        title: the input string that was being parsed.
        segments: the title split by the active separator.
        form_name: name of the :class:`Form` (or dataclass) being attempted.
        reason: short, human-readable description of *what* went wrong.
        failed_at: name of the field that failed, or ``None`` for structural
            failures (e.g. wrong segment count).
    """

    def __init__(
        self,
        *,
        title: str,
        segments: list[str],
        form_name: str,
        reason: str,
        failed_at: str | None = None,
    ) -> None:
        self.title = title
        self.segments = segments
        self.form_name = form_name
        self.reason = reason
        self.failed_at = failed_at
        loc = f' at field {failed_at!r}' if failed_at else ''
        super().__init__(f'{form_name}: {reason}{loc} (title={title!r})')


class SegticAmbiguousError(SegticError):
    """``parse_any(strict=True)`` saw two forms tied for highest specificity."""

    def __init__(self, *, title: str, candidates: list[str]) -> None:
        self.title = title
        self.candidates = candidates
        super().__init__(f'ambiguous parse for {title!r}: tied candidates {candidates}')

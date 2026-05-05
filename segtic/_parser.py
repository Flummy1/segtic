"""Core parser: turning a list of segments + specs into a dict of field values."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any

from ._kinds import is_numeric
from ._spec import Spec


@dataclass
class Failure:
    """Why a parse attempt failed. ``failed_at`` is None for structural issues."""

    reason: str
    failed_at: str | None = None


def parse_segments(title: str, specs: list[Spec], sep: str) -> dict[str, Any] | None:
    if not title:
        return None
    segs = title.split(sep)
    res, _ = _parse_one(segs, specs, sep)
    return res


def diagnose(title: str, specs: list[Spec], sep: str) -> Failure:
    """Re-run with the full (no-optional-pruning) pattern to surface a reason."""
    if not title:
        return Failure(reason='empty input')
    segs = title.split(sep)
    _, fail = _parse_one(segs, specs, sep)
    return fail or Failure(reason='no matching variant')


def _parse_one(
    segs: list[str], specs: list[Spec], sep: str
) -> tuple[dict[str, Any] | None, Failure | None]:
    opt_indices = [i for i, f in enumerate(specs) if f.optional]
    if not opt_indices:
        return _parse_fixed(segs, specs, sep)

    n_opt = len(opt_indices)
    n_required = len(specs) - n_opt
    has_greedy = any(f.greedy for f in specs)
    n_segs = len(segs)

    # Determine which active-optional counts (k) are plausible given segment count.
    # Without greedy: total fields must equal segments → k is fixed.
    # With greedy: total fields ≤ segments → k ranges from 0..max_k.
    if not has_greedy:
        target = n_segs - n_required
        if target < 0 or target > n_opt:
            return None, Failure(
                reason=f'expected {n_required}..{len(specs)} segments, got {n_segs}',
            )
        k_values = [target]
    else:
        max_k = min(n_opt, max(0, n_segs - n_required))
        # Most specific (highest k) first.
        k_values = list(range(max_k, -1, -1))

    last_fail: Failure | None = None
    for k in k_values:
        for active_combo in combinations(opt_indices, k):
            active = set(active_combo)
            sub = [f for i, f in enumerate(specs) if not f.optional or i in active]
            res, fail = _parse_fixed(segs, sub, sep)
            if res is not None:
                for f in specs:
                    if f.optional:
                        res.setdefault(f.name, None)
                return res, None
            if fail is not None:
                last_fail = fail
    return None, last_fail


def _parse_fixed(
    segs: list[str], pattern: list[Spec], sep: str
) -> tuple[dict[str, Any] | None, Failure | None]:
    n = len(pattern)
    greedy_idx = [i for i, f in enumerate(pattern) if f.greedy]

    chunks: list[str]
    if not greedy_idx:
        if len(segs) != n:
            return None, Failure(
                reason=f'expected {n} segments, got {len(segs)}',
            )
        chunks = list(segs)
    elif len(greedy_idx) == 1:
        g = greedy_idx[0]
        n_left, n_right = g, n - g - 1
        if len(segs) < n_left + n_right + 1:
            return None, Failure(
                reason=f'expected at least {n_left + n_right + 1} segments, got {len(segs)}',
            )
        left = segs[:n_left]
        right = segs[len(segs) - n_right :] if n_right else []
        middle = segs[n_left : len(segs) - n_right] if n_right else segs[n_left:]
        chunks = [*left, sep.join(middle), *right]
    else:
        resolved, fail = _resolve_multi_greedy(segs, pattern, greedy_idx, sep)
        if resolved is None:
            return None, fail
        chunks = resolved

    for f, c in zip(pattern, chunks, strict=True):
        if not f.matches(c):
            return None, Failure(
                reason=f'segment {c!r} does not match field constraints',
                failed_at=f.name,
            )
    out: dict[str, Any] = {}
    for f, c in zip(pattern, chunks, strict=True):
        v = f.coerce(c)
        if v is None and is_numeric(f.kind):
            return None, Failure(
                reason=f'could not coerce {c!r} to {f.kind}',
                failed_at=f.name,
            )
        out[f.name] = v
    return out, None


def _resolve_multi_greedy(
    segs: list[str],
    pattern: list[Spec],
    greedy_idx: list[int],
    sep: str,
) -> tuple[list[str] | None, Failure | None]:
    n = len(pattern)
    first_g, last_g = greedy_idx[0], greedy_idx[-1]
    n_left = first_g
    n_right = n - last_g - 1
    n_g = len(greedy_idx)
    n_anchors_in_middle = (last_g - first_g + 1) - n_g

    if len(segs) < n_left + n_right + n_g + n_anchors_in_middle:
        return None, Failure(
            reason=f'too few segments for greedy pattern: got {len(segs)}',
        )

    left_segs = segs[:n_left]
    right_segs = segs[len(segs) - n_right :] if n_right else []
    middle_segs = segs[n_left : len(segs) - n_right] if n_right else segs[n_left:]
    middle_pattern = pattern[first_g : last_g + 1]

    anchors = [(i, f) for i, f in enumerate(middle_pattern) if not f.greedy]

    anchor_positions: list[int] = []
    cursor = 1
    for k, (_, anchor) in enumerate(anchors):
        remaining = len(anchors) - k - 1
        max_pos = len(middle_segs) - 1 - (remaining * 2 + 1)
        found: int | None = None
        for j in range(cursor, max_pos + 1):
            if anchor.matches(middle_segs[j]):
                found = j
                break
        if found is None:
            return None, Failure(
                reason='could not locate anchor in greedy middle',
                failed_at=anchor.name,
            )
        anchor_positions.append(found)
        cursor = found + 2

    middle_chunks: list[str] = []
    prev = -1
    for ap in anchor_positions:
        middle_chunks.append(sep.join(middle_segs[prev + 1 : ap]))
        middle_chunks.append(middle_segs[ap])
        prev = ap
    middle_chunks.append(sep.join(middle_segs[prev + 1 :]))

    return [*left_segs, *middle_chunks, *right_segs], None


def specificity(form: type) -> int:
    score = 0
    specs: list[Spec] = form.__segtic_specs__  # type: ignore[attr-defined]
    for s in specs:
        if s.suffix or s.prefix or s.values or s.pattern is not None:
            score += 3
        if not s.greedy:
            score += 2
        else:
            score += 1
        if s.optional:
            score -= 1
    return score

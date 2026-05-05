"""Text-cleanup utilities: emoji/decoration stripping and affix checks."""

from __future__ import annotations

import re
from collections.abc import Iterable

_DECORATION_RE = re.compile(
    '['
    '⌀-⏿'  # misc technical
    '☀-➿'  # misc symbols + dingbats
    '⬀-⯿'  # arrows / misc symbols and arrows
    '︀-️'  # variation selectors
    '‍'  # zero-width joiner
    '\U0001f000-\U0001f02f'  # mahjong
    '\U0001f0a0-\U0001f0ff'  # playing cards
    '\U0001f100-\U0001f1ff'  # enclosed alphanumerics + regional indicators
    '\U0001f200-\U0001f2ff'  # enclosed ideographic
    '\U0001f300-\U0001f5ff'  # misc symbols and pictographs
    '\U0001f600-\U0001f64f'  # emoticons
    '\U0001f680-\U0001f6ff'  # transport
    '\U0001f700-\U0001f77f'  # alchemical
    '\U0001f780-\U0001f7ff'  # geometric extended
    '\U0001f800-\U0001f8ff'  # supplemental arrows-c
    '\U0001f900-\U0001f9ff'  # supplemental symbols
    '\U0001fa00-\U0001faff'  # symbols extended-a
    ']'
)
_OUTER_PUNCT = '.,;:!?-—_*~|/\\()[]{}«»"\'`'


def clean_decorations(s: str) -> str:
    """Strip emoji/decorations, collapse whitespace, strip outer punctuation."""
    s = _DECORATION_RE.sub('', s)
    s = re.sub(r'\s+', ' ', s).strip()
    s = s.strip(_OUTER_PUNCT)
    return s.strip()


def has_affix(s: str, affix: str | tuple[str, ...] | Iterable[str], *, side: str) -> bool:
    """Return True if `s` starts/ends with `affix` (str or tuple). Empty affix → True."""
    if not affix:
        return True
    items: tuple[str, ...] = (affix,) if isinstance(affix, str) else tuple(affix)
    cf = s.strip().casefold()
    check = cf.startswith if side == 'prefix' else cf.endswith
    return any(check(x.strip().casefold()) for x in items)

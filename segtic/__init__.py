"""segtic — segment-based typed parsing of structured-but-loose strings.

Define forms as classes, then call ``.parse()``::

    from typing import Literal
    from segtic import Form, Field

    class TelegramStars(Form):
        quantity: int = Field(suffix=('звёзд', 'звезда', 'звезды', 'stars'))
        auth_method: str = Field(clean=True)
        username: str = Field(greedy=True)
        note: str | None = None

    TelegramStars.parse('50 звёзд, по логину, @user')
    # → TelegramStars(quantity=50, auth_method='по логину', username='@user', note=None)

Try-each across variants (order-independent — picks the most specific match)::

    Form.parse_any(title, [VariantA, VariantB])

Plain dataclasses also work::

    parse(title, MyDataClass)  # → MyDataClass instance | None
"""

from __future__ import annotations

from ._errors import SegticAmbiguousError, SegticError, SegticParseError
from ._form import Form, parse, parse_many, parse_strict
from ._kinds import register_kind
from ._spec import Field
from ._text import clean_decorations
from ._types import register_type

__version__ = '0.1.0'
__all__ = [
    'Field',
    'Form',
    'SegticAmbiguousError',
    'SegticError',
    'SegticParseError',
    'clean_decorations',
    'parse',
    'parse_many',
    'parse_strict',
    'register_kind',
    'register_type',
]

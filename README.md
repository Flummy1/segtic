# segtic

[![CI](https://github.com/Flummy1/segtic/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Flummy1/segtic/actions/workflows/ci.yml)

> Segment-based typed parsing of structured-but-loose strings.
> pydantic-style schema, dissect-style splitting.

`segtic` parses strings that are *almost* structured — comma-separated marketplace titles, `|`-delimited records, slash-separated paths, anything where you'd otherwise reach for fragile `str.split()` + manual indexing — into typed dataclass instances.

```python
from typing import Literal
from segtic import Form, Field

class TelegramStars(Form):
    quantity: int = Field(suffix=('звёзд', 'звезда', 'звезды', 'stars'))
    auth_method: str
    username: str = Field(greedy=True)
    note: str | None = None

TelegramStars.parse('50 звёзд, по логину, @nick, extra info')
# TelegramStars(quantity=50, auth_method='по логину',
#               username='@nick, extra info', note=None)
```

## Why

Real-world "structured" strings are sloppy:

- Different titles for the same product use different field counts (`X, Y` vs `X, Y, Z`).
- Numbers come with units (`50 звёзд`, `$250`, `3 шт.`).
- Some fields are decorated with emojis or punctuation noise.
- Some fields are free-form and must "swallow" multiple comma-separated chunks.

`segtic` lets you describe these patterns declaratively as classes, with anchors (`suffix`, `prefix`, `Literal[...]`, `pattern`), greedy fields, and optional fields. The engine resolves the layout for you and returns a typed instance.

## Install

```bash
pip install segtic
```

## Quick tour

### Anchors: `suffix`, `prefix`, `Literal`, `pattern`

```python
class Order(Form):
    description: str = Field(greedy=True)
    currency: Literal['USD', 'RUB', 'EUR']    # Literal-anchor
    price: int = Field(prefix='$')            # prefix-anchor
    delivery: int = Field(suffix='дн.')       # suffix-anchor
    phone: str = Field(pattern=r'\+\d{11}')   # regex-anchor

Order.parse('boost, 70 lvl, mythic+, USD, $250, 3 дн., +71234567890')
```

### Optional fields via `| None`

```python
class Topup(Form):
    service: str
    amount: int = Field(suffix='руб.')
    promo: str | None = None

Topup.parse('Steam, 1000 руб.')              # promo=None
Topup.parse('Steam, 1000 руб., NEWYEAR')     # promo='NEWYEAR'
```

### Try-each variants — order doesn't matter

```python
class Short(Form):
    qty: int = Field(suffix='шт.')

class Long(Form):
    qty: int = Field(suffix='шт.')
    note: str = Field(greedy=True)

Form.parse_any('5 шт.', [Long, Short])               # → Short(qty=5)
Form.parse_any('5 шт., срочно', [Long, Short])       # → Long(qty=5, note='срочно')
```

`parse_any` scores each successful match by specificity (anchored fields > non-greedy > greedy; optionals penalised) and returns the most specific one. With `strict=True` it raises `SegticAmbiguousError` when two forms tie on score.

### Strict mode — diagnostics on failure

```python
from segtic import SegticParseError

try:
    Topup.parse_strict('garbage')
except SegticParseError as e:
    print(e.failed_at, '—', e.reason)
```

`parse()` returns `None` on failure; `parse_strict()` raises with `form_name`, `failed_at` (field name or `None` for structural failures), `reason`, and the original `title`/`segments`.

### Custom separator (class attr or `Meta`)

```python
class WowChar(Form):
    class Meta:
        separator = ' | '

    realm: str
    faction: Literal['Alliance', 'Horde']
    level: int

WowChar.parse('Stormrage | Alliance | 70')
```

### Lists, booleans, enums, dates, decimals

```python
from datetime import date
from decimal import Decimal
from enum import Enum

class Currency(str, Enum):
    USD = 'USD'
    RUB = 'RUB'

class Receipt(Form):
    cur: Currency
    amount: Decimal = Field(suffix='₽')
    when: date = Field(date_format='%d.%m.%Y')
    paid: bool
    tags: list[str] = Field(item_separator=';')

Receipt.parse('RUB, 1234,56 ₽, 05.05.2026, yes, vip;loyal')
# → Receipt(cur=Currency.RUB, amount=Decimal('1234.56'),
#           when=date(2026,5,5), paid=True, tags=['vip','loyal'])
```

### Plain dataclass — no inheritance

```python
from dataclasses import dataclass
from segtic import parse

@dataclass
class Simple:
    a: str
    b: int

parse('foo, 42', Simple)   # → Simple(a='foo', b=42)
```

### Strip emojis / decorations with `clean=True`

```python
class Region(Form):
    flag: Literal['Russia', 'Europe', 'USA'] = Field(clean=True)
    qty: int

Region.parse('🇹🇷 USA ⭐, 5')   # → Region(flag='USA', qty=5)
```

### Batch parsing

```python
from segtic import parse_many

parse_many(['Steam, 500 руб.', 'Origin, 1000 руб.'], Topup)
# [Topup(...), Topup(...)]

parse_many(titles, [Short, Long])  # auto-picks per title via parse_any
```

### Custom types

```python
from segtic import register_kind, register_type

class Slug:
    def __init__(self, value: str) -> None: self.value = value

def slug_match(s, spec): return s.strip().replace('-', '').isalnum()
def slug_coerce(s, spec): return Slug(s.strip())

register_kind('slug', matcher=slug_match, coercer=slug_coerce)
register_type(lambda tp: ('slug', (), {}) if tp is Slug else None)

class Page(Form):
    slug: Slug
    views: int
```

## Type mapping

| Annotation              | Behaviour                                           |
|-------------------------|-----------------------------------------------------|
| `str`                   | string segment, optional `clean=True`               |
| `int`                   | integer; recognises `1,000` / `1.000` thousands     |
| `float`                 | float; accepts `,` or `.` as decimal point          |
| `Decimal`               | like `float`, but as `Decimal`                      |
| `bool`                  | `yes/no/да/нет/1/0/...` — customise via `bool_true`/`bool_false` |
| `date` / `datetime`     | ISO format by default; `date_format='%d.%m.%Y'` for custom |
| `Literal['A', 'B']`     | must equal one of the values (casefold)             |
| `Enum`                  | matches by enum value (casefold)                    |
| `list[T]`               | inner items split by `item_separator` (default `;`) |
| `X \| None`             | field is optional; defaults to `None`               |

## `Field()` options

| Option            | Effect                                                                   |
|-------------------|--------------------------------------------------------------------------|
| `suffix=...`      | segment must end with the string (or any of a tuple)                     |
| `prefix=...`      | segment must start with the string (or any of a tuple)                   |
| `pattern=r'...'`  | segment must `fullmatch` the regex                                       |
| `greedy=True`     | swallow multiple separator-joined chunks                                 |
| `clean=True`      | strip emojis / decorations before match and in the output                |
| `bool_true=(...)` | tokens that mean `True` for `bool` fields                                |
| `bool_false=(...)`| tokens that mean `False` for `bool` fields                               |
| `date_format=...` | `strptime` format for `date` / `datetime` fields                         |
| `item_separator=...` | inner separator for `list[T]` fields (default `;`)                    |
| `default=...`     | dataclass-style default                                                  |
| `default_factory=...` | dataclass-style default factory                                      |

## How matching works

1. The title is split by `separator` (default `', '`).
2. For each candidate set of "active" optional fields, the engine tries to align the segments to the field pattern:
   - Without greedy fields → segment count must equal field count.
   - With one greedy field → its slice grows to swallow the surplus.
   - With multiple greedy fields separated by anchored fields → anchor positions are located by linear scan; everything between them collapses into the corresponding greedy field.
3. Each segment is checked against its field's matcher (kind + affix + pattern). If any fails, the whole alignment is rejected and the next combination of optionals is tried.
4. On success, segments are coerced via the kind's coercer and a dataclass instance is returned.

`Form.parse_any` runs this for every variant and picks the one with the highest specificity score.

## Limitations

- No nested forms (`field: SubForm`) — keep schemas flat.
- `list[T]` requires a separate `item_separator` distinct from the form `separator`.
- Pattern/anchor matching is regex-based; no Lark-style grammars.
- The optional-field search is `O(C(N, k))` where `N` is the number of optional fields and `k` is dictated by segment count — fine for `N ≤ ~15`.

## Status

Alpha. API may change before 1.0.

## License

MIT

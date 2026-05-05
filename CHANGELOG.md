# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - Unreleased

## [0.1.0] - 2026-05-05

### Added
- `py.typed` marker so external `mypy` picks up bundled type information.
- Dev dependencies (`pytest`, `mypy`, `ruff`) under `[project.optional-dependencies].dev`.
- GitHub Actions CI matrix for Python 3.10–3.13 plus `ruff`/`mypy` lint job.
- `CHANGELOG.md`, `Issues` and `Changelog` URLs in package metadata.
- `parse_strict()` and `Form.parse_strict()` that raise `SegticParseError`
  with `failed_at`, `reason`, `segments` for diagnostics.
- `Form.parse_any(..., strict=True)` raises `SegticAmbiguousError` on tie.
- `bool` field type with customisable `bool_true` / `bool_false` token sets.
- `Enum` support — matches by enum value, returns enum members.
- `date` / `datetime` support (ISO by default, custom `date_format`).
- `Decimal` support.
- `list[T]` support with configurable `item_separator`.
- `Field(pattern=r'...')` regex anchor.
- `register_kind()` and `register_type()` to plug in custom Python types.
- `Form.Meta.separator` as an alternative to the class-attribute style.
- `parse_many()` batch helper.
- Snapshot test on a fixture of real-world style titles.
- Initial release: `Form`, `Field`, `parse`, `clean_decorations`.
- Anchors: `suffix`, `prefix`, `Literal[...]`.
- `greedy=True` and `clean=True` field options.
- `Form.parse_any` with specificity-based scoring.
- Plain-dataclass parsing via top-level `parse()`.

### Changed
- Single-file `segtic/__init__.py` split into focused modules
  (`_text`, `_types`, `_kinds`, `_spec`, `_parser`, `_form`, `_errors`).
- Optional-field search now iterates only plausible active counts (combinations,
  not full bitmask), removing the `O(2^N)` worst case for large `N`.
- Plain-dataclass parsing caches its spec list on the class on first use.
- `_DECORATION_RE` widened to cover misc-tech, mahjong, cards, geometric,
  alchemical and other emoji blocks.
- Numeric (int/float/decimal) fields now reject coercion-to-None as a hard
  failure instead of silently producing `None` for the field.

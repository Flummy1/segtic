"""Custom type — plug a user-defined Python type into the segtic kind registry.

register_kind()  defines how to match and coerce a raw string segment.
register_type()  maps a Python type annotation to that kind.

After registration, the type can be used in any Form or plain dataclass
exactly like the built-in int / date / Decimal / etc.

Run:
    python examples/custom_type.py
"""

from segtic import Field, Form, register_kind, register_type


# --- 1. Define the custom Python type ----------------------------------------

class IPv4:
    """Minimal IPv4 address wrapper."""

    def __init__(self, value: str) -> None:
        parts = value.strip().split('.')
        if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            raise ValueError(f'invalid IPv4: {value!r}')
        self.value = value.strip()

    def __repr__(self) -> str:
        return f'IPv4({self.value!r})'

    def __eq__(self, other: object) -> bool:
        return isinstance(other, IPv4) and self.value == other.value


# --- 2. Register the kind (matcher + coercer) --------------------------------

def _ipv4_match(s: str, spec) -> bool:  # type: ignore[no-untyped-def]
    try:
        IPv4(s)
        return True
    except ValueError:
        return False

def _ipv4_coerce(s: str, spec) -> IPv4:  # type: ignore[no-untyped-def]
    return IPv4(s)

register_kind('ipv4', matcher=_ipv4_match, coercer=_ipv4_coerce)


# --- 3. Map the Python annotation to the kind --------------------------------

register_type(lambda tp: ('ipv4', (), {}) if tp is IPv4 else None)


# --- 4. Use the type in a Form -----------------------------------------------

class ServerRecord(Form):
    host: IPv4
    port: int
    label: str | None = None

print(ServerRecord.parse('10.0.0.1, 8080'))
# ServerRecord(host=IPv4('10.0.0.1'), port=8080, label=None)

print(ServerRecord.parse('192.168.1.100, 443, production'))
# ServerRecord(host=IPv4('192.168.1.100'), port=443, label='production')

print(ServerRecord.parse('not-an-ip, 8080'))
# None  — matcher rejected the segment

print(ServerRecord.parse('10.0.0.1, not-a-port'))
# None  — int coercion failed

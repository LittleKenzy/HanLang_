"""
HanLang Value System
====================

Defines the runtime value types and the type system for HanLang.
All values in HanLang are wrapped in these types for consistent
type checking and method dispatch.
"""


class HanValue:
    """Base class for all HanLang runtime values."""

    def type_name(self):
        return "tidak_diketahui"

    def to_display(self):
        """Human-readable string for tampil()."""
        return str(self)

    def to_boolean(self):
        """Convert to boolean for conditionals."""
        return True

    def __repr__(self):
        return self.to_display()


class HanNumber(HanValue):
    """Integer or float number."""

    def __init__(self, value):
        if isinstance(value, bool):
            value = int(value)
        self.value = value

    def type_name(self):
        if isinstance(self.value, float):
            return "desimal"
        return "bilangan"

    def to_display(self):
        if isinstance(self.value, float):
            # Show integers without trailing .0 when appropriate
            if self.value == int(self.value) and not (self.value != self.value):  # NaN check
                return str(int(self.value))
            return str(self.value)
        return str(self.value)

    def to_boolean(self):
        return self.value != 0

    def __eq__(self, other):
        if isinstance(other, HanNumber):
            return self.value == other.value
        return NotImplemented

    def __hash__(self):
        return hash(self.value)


class HanString(HanValue):
    """String value."""

    def __init__(self, value):
        self.value = str(value)

    def type_name(self):
        return "teks"

    def to_display(self):
        return self.value

    def to_boolean(self):
        return len(self.value) > 0

    def __eq__(self, other):
        if isinstance(other, HanString):
            return self.value == other.value
        return NotImplemented

    def __hash__(self):
        return hash(self.value)


class HanBoolean(HanValue):
    """Boolean value."""

    def __init__(self, value):
        self.value = bool(value)

    def type_name(self):
        return "boolean"

    def to_display(self):
        return "Benar" if self.value else "Salah"

    def to_boolean(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, HanBoolean):
            return self.value == other.value
        return NotImplemented

    def __hash__(self):
        return hash(self.value)


class HanNull(HanValue):
    """Null value (kosong)."""

    def __init__(self):
        self.value = None

    def type_name(self):
        return "kosong"

    def to_display(self):
        return "kosong"

    def to_boolean(self):
        return False

    def __eq__(self, other):
        if isinstance(other, HanNull):
            return True
        return NotImplemented

    def __hash__(self):
        return hash(None)


class HanList(HanValue):
    """List/array value."""

    def __init__(self, elements=None):
        self.elements = elements if elements is not None else []

    def type_name(self):
        return "daftar"

    def to_display(self):
        inner = ", ".join(value_repr(e) for e in self.elements)
        return f"[{inner}]"

    def to_boolean(self):
        return len(self.elements) > 0

    def __eq__(self, other):
        if isinstance(other, HanList):
            return self.elements == other.elements
        return NotImplemented


class HanMap(HanValue):
    """Map/dictionary value."""

    def __init__(self, pairs=None):
        self.entries = {}
        if pairs:
            for k, v in pairs:
                self.entries[k] = v

    def type_name(self):
        return "peta"

    def to_display(self):
        parts = []
        for k, v in self.entries.items():
            parts.append(f"{value_repr(k)}: {value_repr(v)}")
        inner = ", ".join(parts)
        return "{" + inner + "}"

    def to_boolean(self):
        return len(self.entries) > 0

    def __eq__(self, other):
        if isinstance(other, HanMap):
            return self.entries == other.entries
        return NotImplemented


class HanFunction(HanValue):
    """User-defined function."""

    def __init__(self, name, params, body, closure_env):
        self.name = name
        self.params = params
        self.body = body
        self.closure_env = closure_env

    def type_name(self):
        return "fungsi"

    def to_display(self):
        params = ", ".join(self.params)
        return f"<fungsi {self.name}({params})>"

    def to_boolean(self):
        return True


class HanLambda(HanValue):
    """Anonymous function (lambda)."""

    def __init__(self, params, body, closure_env):
        self.params = params
        self.body = body
        self.closure_env = closure_env

    def type_name(self):
        return "lambda"

    def to_display(self):
        params = ", ".join(self.params)
        return f"<lambda({params})>"

    def to_boolean(self):
        return True


class HanBuiltinFunction(HanValue):
    """Built-in function implemented in Python."""

    def __init__(self, name, func, param_count=None):
        self.name = name
        self.func = func
        self.param_count = param_count  # None means variable args

    def type_name(self):
        return "fungsi_bawaan"

    def to_display(self):
        return f"<fungsi_bawaan {self.name}>"

    def to_boolean(self):
        return True


class HanModule(HanValue):
    """Imported module."""

    def __init__(self, name, members):
        self.name = name
        self.members = members  # dict of name -> HanValue

    def type_name(self):
        return "modul"

    def to_display(self):
        return f"<modul {self.name}>"

    def to_boolean(self):
        return True


class HanError(HanValue):
    """Runtime error value (for catch blocks)."""

    def __init__(self, message, code="H000"):
        self.message = message
        self.code = code

    def type_name(self):
        return "error"

    def to_display(self):
        return f"Error[{self.code}]: {self.message}"

    def to_boolean(self):
        return True


# ── Utility Functions ─────────────────────────────────────────────

def value_repr(val):
    """Get a repr-style string for a value (with quotes around strings)."""
    if isinstance(val, HanString):
        return f'"{val.value}"'
    return val.to_display() if isinstance(val, HanValue) else str(val)


def python_to_han(value):
    """Convert a Python value to a HanLang value."""
    if isinstance(value, HanValue):
        return value
    if value is None:
        return HanNull()
    if isinstance(value, bool):
        return HanBoolean(value)
    if isinstance(value, (int, float)):
        return HanNumber(value)
    if isinstance(value, str):
        return HanString(value)
    if isinstance(value, list):
        return HanList([python_to_han(e) for e in value])
    if isinstance(value, dict):
        m = HanMap()
        for k, v in value.items():
            m.entries[python_to_han(k)] = python_to_han(v)
        return m
    return HanString(str(value))


def han_to_python(value):
    """Convert a HanLang value to a Python value."""
    if isinstance(value, HanNull):
        return None
    if isinstance(value, HanBoolean):
        return value.value
    if isinstance(value, HanNumber):
        return value.value
    if isinstance(value, HanString):
        return value.value
    if isinstance(value, HanList):
        return [han_to_python(e) for e in value.elements]
    if isinstance(value, HanMap):
        return {han_to_python(k): han_to_python(v) for k, v in value.entries.items()}
    return str(value)


def han_equals(a, b):
    """Deep equality check between two HanLang values."""
    if type(a) != type(b):
        # Allow number comparison across int/float
        if isinstance(a, HanNumber) and isinstance(b, HanNumber):
            return a.value == b.value
        return False
    return a == b

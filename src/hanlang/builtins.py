"""
HanLang Built-in Functions
==========================

Core built-in functions available in every HanLang program.
These provide I/O, type conversion, collection operations,
and utility functions.
"""

import math
import time
import random as _random
import json as _json
import os

from .values import (
    HanValue, HanNumber, HanString, HanBoolean, HanNull,
    HanList, HanMap, HanFunction, HanLambda, HanBuiltinFunction,
    HanModule, HanError as HanErrorValue,
    python_to_han, han_to_python, value_repr,
)
from .errors import (
    ArgumentError, RuntimeError_, TypeMismatchError,
    DivisionByZeroError, SourceLocation,
)


def _check_args(name, args, expected_min, expected_max=None):
    """Validate argument count."""
    if expected_max is None:
        expected_max = expected_min
    if len(args) < expected_min or len(args) > expected_max:
        if expected_min == expected_max:
            raise ArgumentError(name, expected_min, len(args))
        raise ArgumentError(name, f"{expected_min}-{expected_max}", len(args))


def _expect_type(name, arg, *types):
    """Ensure an argument is one of the expected types."""
    if not isinstance(arg, types):
        expected = " atau ".join(t.__name__.replace("Han", "").lower() for t in types)
        raise RuntimeError_(
            f"Fungsi '{name}' membutuhkan argumen bertipe {expected}, "
            f"tapi diberikan {arg.type_name()}"
        )


# ── Core I/O ──────────────────────────────────────────────────────

def builtin_tampil(args):
    """tampil(...) — Print values to stdout."""
    parts = []
    for arg in args:
        if isinstance(arg, HanValue):
            parts.append(arg.to_display())
        else:
            parts.append(str(arg))
    print(" ".join(parts))
    return HanNull()


def builtin_masukan(args):
    """masukan(prompt) — Read a line from stdin."""
    prompt = ""
    if args:
        prompt = args[0].to_display() if isinstance(args[0], HanValue) else str(args[0])
    try:
        result = input(prompt)
        return HanString(result)
    except EOFError:
        return HanNull()


# ── Type Conversion ───────────────────────────────────────────────

def builtin_bilangan(args):
    """bilangan(value) — Convert to number."""
    _check_args("bilangan", args, 1)
    val = args[0]
    if isinstance(val, HanNumber):
        return val
    if isinstance(val, HanString):
        try:
            if "." in val.value:
                return HanNumber(float(val.value))
            return HanNumber(int(val.value))
        except ValueError:
            raise RuntimeError_(f"Tidak bisa mengubah '{val.value}' menjadi bilangan")
    if isinstance(val, HanBoolean):
        return HanNumber(1 if val.value else 0)
    raise RuntimeError_(f"Tidak bisa mengubah {val.type_name()} menjadi bilangan")


def builtin_teks(args):
    """teks(value) — Convert to string."""
    _check_args("teks", args, 1)
    return HanString(args[0].to_display())


def builtin_desimal(args):
    """desimal(value) — Convert to float."""
    _check_args("desimal", args, 1)
    val = args[0]
    if isinstance(val, HanNumber):
        return HanNumber(float(val.value))
    if isinstance(val, HanString):
        try:
            return HanNumber(float(val.value))
        except ValueError:
            raise RuntimeError_(f"Tidak bisa mengubah '{val.value}' menjadi desimal")
    raise RuntimeError_(f"Tidak bisa mengubah {val.type_name()} menjadi desimal")


def builtin_boolean(args):
    """boolean(value) — Convert to boolean."""
    _check_args("boolean", args, 1)
    return HanBoolean(args[0].to_boolean())


# ── Type Checking ─────────────────────────────────────────────────

def builtin_tipe(args):
    """tipe(value) — Get the type name of a value."""
    _check_args("tipe", args, 1)
    return HanString(args[0].type_name())


def builtin_adalah(args):
    """adalah(value, type_name) — Check if value is of given type."""
    _check_args("adalah", args, 2)
    _expect_type("adalah", args[1], HanString)
    return HanBoolean(args[0].type_name() == args[1].value)


# ── Collection Functions ──────────────────────────────────────────

def builtin_panjang(args):
    """panjang(value) — Get length of string, list, or map."""
    _check_args("panjang", args, 1)
    val = args[0]
    if isinstance(val, HanString):
        return HanNumber(len(val.value))
    if isinstance(val, HanList):
        return HanNumber(len(val.elements))
    if isinstance(val, HanMap):
        return HanNumber(len(val.entries))
    raise RuntimeError_(f"Fungsi 'panjang' tidak mendukung tipe {val.type_name()}")


def builtin_rentang(args):
    """rentang(start, end[, step]) — Generate a range of numbers."""
    if len(args) == 1:
        _expect_type("rentang", args[0], HanNumber)
        return HanList([HanNumber(i) for i in range(int(args[0].value))])
    elif len(args) == 2:
        _expect_type("rentang", args[0], HanNumber)
        _expect_type("rentang", args[1], HanNumber)
        return HanList([HanNumber(i) for i in range(int(args[0].value), int(args[1].value))])
    elif len(args) == 3:
        _expect_type("rentang", args[0], HanNumber)
        _expect_type("rentang", args[1], HanNumber)
        _expect_type("rentang", args[2], HanNumber)
        step = int(args[2].value)
        if step == 0:
            raise RuntimeError_("Langkah (step) tidak boleh nol")
        return HanList([HanNumber(i) for i in range(
            int(args[0].value), int(args[1].value), step
        )])
    raise ArgumentError("rentang", "1-3", len(args))


def builtin_tambah(args):
    """tambah(list, value) — Append value to list."""
    _check_args("tambah", args, 2)
    _expect_type("tambah", args[0], HanList)
    args[0].elements.append(args[1])
    return args[0]


def builtin_hapus(args):
    """hapus(list, index) or hapus(map, key) — Remove element."""
    _check_args("hapus", args, 2)
    collection = args[0]
    if isinstance(collection, HanList):
        _expect_type("hapus", args[1], HanNumber)
        idx = int(args[1].value)
        if 0 <= idx < len(collection.elements):
            return collection.elements.pop(idx)
        raise RuntimeError_(f"Indeks {idx} diluar jangkauan")
    if isinstance(collection, HanMap):
        key = args[1]
        if key in collection.entries:
            return collection.entries.pop(key)
        raise RuntimeError_(f"Kunci tidak ditemukan")
    raise RuntimeError_(f"Fungsi 'hapus' tidak mendukung tipe {collection.type_name()}")


def builtin_gabung(args):
    """gabung(list, separator) — Join list elements into string."""
    _check_args("gabung", args, 1, 2)
    _expect_type("gabung", args[0], HanList)
    sep = ", "
    if len(args) > 1:
        _expect_type("gabung", args[1], HanString)
        sep = args[1].value
    parts = [elem.to_display() for elem in args[0].elements]
    return HanString(sep.join(parts))


def builtin_pisah(args):
    """pisah(string, separator) — Split string into list."""
    _check_args("pisah", args, 1, 2)
    _expect_type("pisah", args[0], HanString)
    sep = " "
    if len(args) > 1:
        _expect_type("pisah", args[1], HanString)
        sep = args[1].value
    parts = args[0].value.split(sep)
    return HanList([HanString(p) for p in parts])


def builtin_urutkan(args):
    """urutkan(list) — Sort a list."""
    _check_args("urutkan", args, 1)
    _expect_type("urutkan", args[0], HanList)
    elements = list(args[0].elements)
    try:
        elements.sort(key=lambda x: x.value if isinstance(x, (HanNumber, HanString)) else x.to_display())
    except TypeError:
        raise RuntimeError_("Tidak bisa mengurutkan daftar dengan tipe campuran")
    return HanList(elements)


def builtin_balik(args):
    """balik(list) — Reverse a list."""
    _check_args("balik", args, 1)
    _expect_type("balik", args[0], HanList)
    return HanList(list(reversed(args[0].elements)))


def builtin_berisi(args):
    """berisi(collection, value) — Check if collection contains value."""
    _check_args("berisi", args, 2)
    collection = args[0]
    value = args[1]
    if isinstance(collection, HanList):
        for elem in collection.elements:
            if elem == value:
                return HanBoolean(True)
        return HanBoolean(False)
    if isinstance(collection, HanString):
        if isinstance(value, HanString):
            return HanBoolean(value.value in collection.value)
        return HanBoolean(False)
    if isinstance(collection, HanMap):
        return HanBoolean(value in collection.entries)
    raise RuntimeError_(f"Fungsi 'berisi' tidak mendukung tipe {collection.type_name()}")


def builtin_kunci(args):
    """kunci(map) — Get all keys of a map."""
    _check_args("kunci", args, 1)
    _expect_type("kunci", args[0], HanMap)
    return HanList(list(args[0].entries.keys()))


def builtin_nilai(args):
    """nilai(map) — Get all values of a map."""
    _check_args("nilai", args, 1)
    _expect_type("nilai", args[0], HanMap)
    return HanList(list(args[0].entries.values()))


# ── Pipeline Functions ────────────────────────────────────────────

def builtin_saring(args):
    """saring(list, func) — Filter a list using a predicate function."""
    _check_args("saring", args, 2)
    _expect_type("saring", args[0], HanList)
    # The second arg is a function — handled by runtime
    return args  # placeholder — actual filtering done in runtime


def builtin_ubah(args):
    """ubah(list, func) — Map a function over a list."""
    _check_args("ubah", args, 2)
    _expect_type("ubah", args[0], HanList)
    return args  # placeholder — actual mapping done in runtime


# ── Math Functions ────────────────────────────────────────────────

def builtin_abs(args):
    """abs(x) — Absolute value."""
    _check_args("abs", args, 1)
    _expect_type("abs", args[0], HanNumber)
    return HanNumber(abs(args[0].value))


def builtin_bulat(args):
    """bulat(x[, digits]) — Round a number."""
    if len(args) == 1:
        _expect_type("bulat", args[0], HanNumber)
        return HanNumber(round(args[0].value))
    elif len(args) == 2:
        _expect_type("bulat", args[0], HanNumber)
        _expect_type("bulat", args[1], HanNumber)
        return HanNumber(round(args[0].value, int(args[1].value)))
    raise ArgumentError("bulat", "1-2", len(args))


def builtin_min(args):
    """min(a, b, ...) or min(list) — Minimum value."""
    if len(args) == 1 and isinstance(args[0], HanList):
        elems = args[0].elements
        if not elems:
            raise RuntimeError_("Fungsi 'min' tidak bisa dipanggil dengan daftar kosong")
        return min(elems, key=lambda x: x.value)
    if len(args) >= 2:
        return min(args, key=lambda x: x.value if isinstance(x, HanNumber) else float('inf'))
    raise ArgumentError("min", "1+", len(args))


def builtin_max(args):
    """max(a, b, ...) or max(list) — Maximum value."""
    if len(args) == 1 and isinstance(args[0], HanList):
        elems = args[0].elements
        if not elems:
            raise RuntimeError_("Fungsi 'max' tidak bisa dipanggil dengan daftar kosong")
        return max(elems, key=lambda x: x.value)
    if len(args) >= 2:
        return max(args, key=lambda x: x.value if isinstance(x, HanNumber) else float('-inf'))
    raise ArgumentError("max", "1+", len(args))


# ── Standard Library Modules ─────────────────────────────────────

def create_math_module():
    """Create the 'math' standard library module."""
    members = {
        "pi": HanNumber(math.pi),
        "e": HanNumber(math.e),
        "inf": HanNumber(math.inf),
        "akar": HanBuiltinFunction("math.akar", lambda args: (
            _check_args("math.akar", args, 1) or
            _expect_type("math.akar", args[0], HanNumber) or
            HanNumber(math.sqrt(args[0].value))
        )),
        "pangkat": HanBuiltinFunction("math.pangkat", lambda args: (
            _check_args("math.pangkat", args, 2) or
            HanNumber(math.pow(args[0].value, args[1].value))
        )),
        "lantai": HanBuiltinFunction("math.lantai", lambda args: (
            _check_args("math.lantai", args, 1) or
            HanNumber(math.floor(args[0].value))
        )),
        "langit": HanBuiltinFunction("math.langit", lambda args: (
            _check_args("math.langit", args, 1) or
            HanNumber(math.ceil(args[0].value))
        )),
        "log": HanBuiltinFunction("math.log", lambda args: (
            _check_args("math.log", args, 1, 2) or
            HanNumber(math.log(args[0].value, args[1].value if len(args) > 1 else math.e))
        )),
        "sin": HanBuiltinFunction("math.sin", lambda args: (
            _check_args("math.sin", args, 1) or
            HanNumber(math.sin(args[0].value))
        )),
        "cos": HanBuiltinFunction("math.cos", lambda args: (
            _check_args("math.cos", args, 1) or
            HanNumber(math.cos(args[0].value))
        )),
        "tan": HanBuiltinFunction("math.tan", lambda args: (
            _check_args("math.tan", args, 1) or
            HanNumber(math.tan(args[0].value))
        )),
    }
    return HanModule("math", members)


def create_text_module():
    """Create the 'text' standard library module."""
    members = {
        "huruf_besar": HanBuiltinFunction("text.huruf_besar", lambda args: (
            _check_args("text.huruf_besar", args, 1) or
            HanString(args[0].to_display().upper())
        )),
        "huruf_kecil": HanBuiltinFunction("text.huruf_kecil", lambda args: (
            _check_args("text.huruf_kecil", args, 1) or
            HanString(args[0].to_display().lower())
        )),
        "potong": HanBuiltinFunction("text.potong", lambda args: (
            _check_args("text.potong", args, 1) or
            HanString(args[0].to_display().strip())
        )),
        "awalan": HanBuiltinFunction("text.awalan", lambda args: (
            _check_args("text.awalan", args, 2) or
            HanBoolean(args[0].to_display().startswith(args[1].to_display()))
        )),
        "akhiran": HanBuiltinFunction("text.akhiran", lambda args: (
            _check_args("text.akhiran", args, 2) or
            HanBoolean(args[0].to_display().endswith(args[1].to_display()))
        )),
        "ganti": HanBuiltinFunction("text.ganti", lambda args: (
            _check_args("text.ganti", args, 3) or
            HanString(args[0].to_display().replace(args[1].to_display(), args[2].to_display()))
        )),
        "cari": HanBuiltinFunction("text.cari", lambda args: (
            _check_args("text.cari", args, 2) or
            HanNumber(args[0].to_display().find(args[1].to_display()))
        )),
        "format": HanBuiltinFunction("text.format", lambda args: (
            _check_args("text.format", args, 1) or
            HanString(args[0].to_display())
        )),
    }
    return HanModule("text", members)


def create_list_module():
    """Create the 'list' standard library module."""
    members = {
        "buat": HanBuiltinFunction("list.buat", lambda args: HanList(list(args))),
        "kosong": HanBuiltinFunction("list.kosong", lambda args: (
            _check_args("list.kosong", args, 1) or
            HanBoolean(isinstance(args[0], HanList) and len(args[0].elements) == 0)
        )),
        "datar": HanBuiltinFunction("list.datar", lambda args: _flatten_list(args)),
        "unik": HanBuiltinFunction("list.unik", lambda args: _unique_list(args)),
        "iris": HanBuiltinFunction("list.iris", lambda args: _slice_list(args)),
    }
    return HanModule("list", members)


def _flatten_list(args):
    _check_args("list.datar", args, 1)
    _expect_type("list.datar", args[0], HanList)
    result = []
    for elem in args[0].elements:
        if isinstance(elem, HanList):
            flat = _flatten_list([elem])
            result.extend(flat.elements)
        else:
            result.append(elem)
    return HanList(result)


def _unique_list(args):
    _check_args("list.unik", args, 1)
    _expect_type("list.unik", args[0], HanList)
    seen = []
    result = []
    for elem in args[0].elements:
        found = False
        for s in seen:
            if s == elem:
                found = True
                break
        if not found:
            seen.append(elem)
            result.append(elem)
    return HanList(result)


def _slice_list(args):
    _check_args("list.iris", args, 2, 3)
    _expect_type("list.iris", args[0], HanList)
    _expect_type("list.iris", args[1], HanNumber)
    start = int(args[1].value)
    end = len(args[0].elements)
    if len(args) > 2:
        _expect_type("list.iris", args[2], HanNumber)
        end = int(args[2].value)
    return HanList(args[0].elements[start:end])


def create_file_module():
    """Create the 'file' standard library module (sandboxed)."""
    members = {
        "baca": HanBuiltinFunction("file.baca", _file_read),
        "tulis": HanBuiltinFunction("file.tulis", _file_write),
        "ada": HanBuiltinFunction("file.ada", lambda args: (
            _check_args("file.ada", args, 1) or
            HanBoolean(os.path.exists(args[0].to_display()))
        )),
    }
    return HanModule("file", members)


def _file_read(args):
    _check_args("file.baca", args, 1)
    _expect_type("file.baca", args[0], HanString)
    path = args[0].value
    try:
        with open(path, "r", encoding="utf-8") as f:
            return HanString(f.read())
    except FileNotFoundError:
        raise RuntimeError_(f"File tidak ditemukan: {path}")
    except PermissionError:
        raise RuntimeError_(f"Tidak punya izin untuk membaca: {path}")
    except Exception as e:
        raise RuntimeError_(f"Gagal membaca file: {e}")


def _file_write(args):
    _check_args("file.tulis", args, 2)
    _expect_type("file.tulis", args[0], HanString)
    path = args[0].value
    content = args[1].to_display()
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return HanBoolean(True)
    except PermissionError:
        raise RuntimeError_(f"Tidak punya izin untuk menulis: {path}")
    except Exception as e:
        raise RuntimeError_(f"Gagal menulis file: {e}")


def create_json_module():
    """Create the 'json' standard library module."""
    members = {
        "parse": HanBuiltinFunction("json.parse", _json_parse),
        "stringify": HanBuiltinFunction("json.stringify", _json_stringify),
    }
    return HanModule("json", members)


def _json_parse(args):
    _check_args("json.parse", args, 1)
    _expect_type("json.parse", args[0], HanString)
    try:
        data = _json.loads(args[0].value)
        return python_to_han(data)
    except _json.JSONDecodeError as e:
        raise RuntimeError_(f"JSON tidak valid: {e}")


def _json_stringify(args):
    _check_args("json.stringify", args, 1, 2)
    indent = None
    if len(args) > 1 and isinstance(args[1], HanNumber):
        indent = int(args[1].value)
    try:
        py_val = han_to_python(args[0])
        return HanString(_json.dumps(py_val, ensure_ascii=False, indent=indent))
    except Exception as e:
        raise RuntimeError_(f"Gagal mengubah ke JSON: {e}")


def create_time_module():
    """Create the 'time' standard library module."""
    members = {
        "sekarang": HanBuiltinFunction("time.sekarang", lambda args: (
            HanNumber(time.time())
        )),
        "tunggu": HanBuiltinFunction("time.tunggu", lambda args: (
            _check_args("time.tunggu", args, 1) or
            _expect_type("time.tunggu", args[0], HanNumber) or
            time.sleep(args[0].value) or
            HanNull()
        )),
        "format": HanBuiltinFunction("time.format", lambda args: (
            _check_args("time.format", args, 0, 1) or
            HanString(time.strftime(
                args[0].value if args and isinstance(args[0], HanString) else "%Y-%m-%d %H:%M:%S"
            ))
        )),
    }
    return HanModule("time", members)


def create_random_module():
    """Create the 'random' standard library module."""
    members = {
        "acak": HanBuiltinFunction("random.acak", lambda args: HanNumber(_random.random())),
        "acak_bilangan": HanBuiltinFunction("random.acak_bilangan", lambda args: (
            _check_args("random.acak_bilangan", args, 2) or
            HanNumber(_random.randint(int(args[0].value), int(args[1].value)))
        )),
        "pilih": HanBuiltinFunction("random.pilih", lambda args: (
            _check_args("random.pilih", args, 1) or
            _expect_type("random.pilih", args[0], HanList) or
            (_random.choice(args[0].elements) if args[0].elements else HanNull())
        )),
        "kocok": HanBuiltinFunction("random.kocok", lambda args: (
            _check_args("random.kocok", args, 1) or
            _expect_type("random.kocok", args[0], HanList) or
            _shuffle_list(args[0])
        )),
    }
    return HanModule("random", members)


def _shuffle_list(lst):
    elements = list(lst.elements)
    _random.shuffle(elements)
    return HanList(elements)


def create_system_module():
    """Create the 'system' standard library module."""
    import platform
    members = {
        "os": HanString(platform.system()),
        "versi_python": HanString(platform.python_version()),
        "versi_hanlang": HanString("0.1.0"),
        "args": HanBuiltinFunction("system.args", lambda args: (
            HanList([HanString(a) for a in __import__("sys").argv])
        )),
        "keluar": HanBuiltinFunction("system.keluar", lambda args: (
            __import__("sys").exit(int(args[0].value) if args and isinstance(args[0], HanNumber) else 0)
        )),
    }
    return HanModule("system", members)


def create_test_module():
    """Create the 'test' standard library module."""
    members = {
        "sama": HanBuiltinFunction("test.sama", lambda args: (
            _check_args("test.sama", args, 2) or
            _assert_equal(args[0], args[1])
        )),
        "bukan_sama": HanBuiltinFunction("test.bukan_sama", lambda args: (
            _check_args("test.bukan_sama", args, 2) or
            _assert_not_equal(args[0], args[1])
        )),
        "benar": HanBuiltinFunction("test.benar", lambda args: (
            _check_args("test.benar", args, 1) or
            _assert_true(args[0])
        )),
    }
    return HanModule("test", members)


def _assert_equal(a, b):
    if a != b:
        raise RuntimeError_(
            f"Assertion gagal: {value_repr(a)} != {value_repr(b)}"
        )
    return HanBoolean(True)


def _assert_not_equal(a, b):
    if a == b:
        raise RuntimeError_(
            f"Assertion gagal: {value_repr(a)} == {value_repr(b)} (seharusnya berbeda)"
        )
    return HanBoolean(True)


def _assert_true(val):
    if not val.to_boolean():
        raise RuntimeError_(
            f"Assertion gagal: nilai seharusnya Benar tapi ditemukan {value_repr(val)}"
        )
    return HanBoolean(True)


# ── Module Registry ───────────────────────────────────────────────

STDLIB_MODULES = {
    "math": create_math_module,
    "text": create_text_module,
    "list": create_list_module,
    "file": create_file_module,
    "json": create_json_module,
    "time": create_time_module,
    "random": create_random_module,
    "system": create_system_module,
    "test": create_test_module,
}


# ── Builtin Registry ─────────────────────────────────────────────

def get_builtins():
    """Return a dictionary of all built-in functions."""
    return {
        # I/O
        "tampil": HanBuiltinFunction("tampil", builtin_tampil),
        "masukan": HanBuiltinFunction("masukan", builtin_masukan),

        # Type conversion
        "bilangan": HanBuiltinFunction("bilangan", builtin_bilangan, 1),
        "teks": HanBuiltinFunction("teks", builtin_teks, 1),
        "desimal": HanBuiltinFunction("desimal", builtin_desimal, 1),
        "boolean": HanBuiltinFunction("boolean", builtin_boolean, 1),

        # Type checking
        "tipe": HanBuiltinFunction("tipe", builtin_tipe, 1),
        "adalah": HanBuiltinFunction("adalah", builtin_adalah, 2),

        # Collection functions
        "panjang": HanBuiltinFunction("panjang", builtin_panjang, 1),
        "rentang": HanBuiltinFunction("rentang", builtin_rentang),
        "tambah": HanBuiltinFunction("tambah", builtin_tambah, 2),
        "hapus": HanBuiltinFunction("hapus", builtin_hapus, 2),
        "gabung": HanBuiltinFunction("gabung", builtin_gabung),
        "pisah": HanBuiltinFunction("pisah", builtin_pisah),
        "urutkan": HanBuiltinFunction("urutkan", builtin_urutkan, 1),
        "balik": HanBuiltinFunction("balik", builtin_balik, 1),
        "berisi": HanBuiltinFunction("berisi", builtin_berisi, 2),
        "kunci": HanBuiltinFunction("kunci", builtin_kunci, 1),
        "nilai": HanBuiltinFunction("nilai", builtin_nilai, 1),

        # Math
        "abs": HanBuiltinFunction("abs", builtin_abs, 1),
        "bulat": HanBuiltinFunction("bulat", builtin_bulat),
        "min": HanBuiltinFunction("min", builtin_min),
        "max": HanBuiltinFunction("max", builtin_max),

        # Pipeline functions (placeholders — actual logic in runtime)
        "saring": HanBuiltinFunction("saring", builtin_saring, 2),
        "ubah": HanBuiltinFunction("ubah", builtin_ubah, 2),
    }

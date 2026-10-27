"""
HanLang Error System
====================

All error types used throughout the HanLang interpreter, with error codes,
source location tracking, and user-friendly diagnostic messages.
"""


class SourceLocation:
    """Represents a position in source code."""

    __slots__ = ("file", "line", "column", "length")

    def __init__(self, file="<unknown>", line=0, column=0, length=0):
        self.file = file
        self.line = line
        self.column = column
        self.length = length

    def __repr__(self):
        return f"SourceLocation({self.file}:{self.line}:{self.column})"


class HanError(Exception):
    """Base error for all HanLang errors."""

    code = "H000"
    category = "Error"

    def __init__(self, message, location=None, help_text=None):
        self.message = message
        self.location = location or SourceLocation()
        self.help_text = help_text
        super().__init__(message)

    def format_error(self, source_lines=None):
        """Format a rich, Rust-style error diagnostic."""
        parts = []
        parts.append(f"\033[1;31mHanLang {self.category} [{self.code}]\033[0m")
        parts.append(f"\033[1m{self.message}\033[0m")

        loc = self.location
        if loc.line > 0:
            parts.append(f"")
            parts.append(f" \033[34m-->\033[0m {loc.file}:{loc.line}:{loc.column}")

            if source_lines and 0 < loc.line <= len(source_lines):
                line_text = source_lines[loc.line - 1]
                line_num_str = str(loc.line)
                padding = " " * len(line_num_str)

                parts.append(f"  \033[34m{padding} |\033[0m")
                parts.append(
                    f"  \033[34m{line_num_str} |\033[0m {line_text}"
                )

                if loc.column > 0:
                    marker_pad = " " * (loc.column - 1)
                    marker_len = max(loc.length, 1)
                    marker = "^" * marker_len
                    parts.append(
                        f"  \033[34m{padding} |\033[0m "
                        f"{marker_pad}\033[1;31m{marker}\033[0m"
                    )

                parts.append(f"  \033[34m{padding} |\033[0m")

        if self.help_text:
            parts.append(f"\033[1;32mhelp\033[0m: {self.help_text}")

        parts.append("")
        return "\n".join(parts)


# ── Lexer Errors ──────────────────────────────────────────────────

class LexerError(HanError):
    """Error during tokenization."""
    code = "H100"
    category = "Lexer Error"


class UnterminatedStringError(LexerError):
    """String literal was never closed."""
    code = "H101"

    def __init__(self, location=None):
        super().__init__(
            "String yang belum ditutup",
            location,
            help_text="Tambahkan tanda kutip penutup di akhir string."
        )


class InvalidCharacterError(LexerError):
    """Unexpected character in source."""
    code = "H102"

    def __init__(self, char, location=None):
        super().__init__(
            f"Karakter tidak valid: '{char}'",
            location,
            help_text="Periksa apakah karakter ini seharusnya ada di sini."
        )


class InvalidNumberError(LexerError):
    """Malformed number literal."""
    code = "H103"

    def __init__(self, text, location=None):
        super().__init__(
            f"Format angka tidak valid: '{text}'",
            location,
            help_text="Gunakan format angka yang benar, contoh: 42 atau 3.14"
        )


# ── Parser Errors ─────────────────────────────────────────────────

class ParseError(HanError):
    """Error during parsing."""
    code = "H200"
    category = "Parse Error"


class UnexpectedTokenError(ParseError):
    """Parser encountered an unexpected token."""
    code = "H201"

    def __init__(self, expected, got, location=None):
        super().__init__(
            f"Diharapkan {expected}, tapi ditemukan '{got}'",
            location,
            help_text=f"Ganti '{got}' dengan {expected}."
        )


class MissingTokenError(ParseError):
    """Expected token was not found."""
    code = "H202"

    def __init__(self, expected, location=None):
        super().__init__(
            f"Diharapkan {expected}",
            location,
            help_text=f"Tambahkan {expected} di posisi ini."
        )


# ── Runtime Errors ────────────────────────────────────────────────

class RuntimeError_(HanError):
    """Error during program execution."""
    code = "H300"
    category = "Runtime Error"


class UndefinedVariableError(RuntimeError_):
    """Variable was used before being defined."""
    code = "H301"

    def __init__(self, name, location=None):
        super().__init__(
            f"Variabel tidak ditemukan: '{name}'",
            location,
            help_text=f"Deklarasikan variabel dengan: tetapkan {name} = <nilai>"
        )


class TypeMismatchError(RuntimeError_):
    """Operation applied to incompatible types."""
    code = "H302"

    def __init__(self, operation, left_type, right_type, location=None):
        super().__init__(
            f"Operasi '{operation}' tidak bisa dilakukan antara "
            f"'{left_type}' dan '{right_type}'",
            location,
            help_text="Periksa tipe data operand Anda."
        )


class DivisionByZeroError(RuntimeError_):
    """Division by zero attempted."""
    code = "H303"

    def __init__(self, location=None):
        super().__init__(
            "Pembagian dengan nol tidak diperbolehkan",
            location,
            help_text="Pastikan pembagi bukan nol sebelum melakukan pembagian."
        )


class ArgumentError(RuntimeError_):
    """Wrong number of arguments passed to function."""
    code = "H304"

    def __init__(self, func_name, expected, got, location=None):
        super().__init__(
            f"Fungsi '{func_name}' membutuhkan {expected} argumen, "
            f"tapi diberikan {got}",
            location,
            help_text=f"Berikan tepat {expected} argumen ke fungsi '{func_name}'."
        )


class RecursionLimitError(RuntimeError_):
    """Maximum recursion depth exceeded."""
    code = "H305"

    def __init__(self, location=None):
        super().__init__(
            "Batas rekursi terlampaui (maks 500 panggilan)",
            location,
            help_text="Kurangi kedalaman rekursi atau gunakan loop."
        )


class IndexOutOfRangeError(RuntimeError_):
    """Index is out of bounds."""
    code = "H306"

    def __init__(self, index, length, location=None):
        super().__init__(
            f"Indeks {index} diluar jangkauan (panjang: {length})",
            location,
            help_text=f"Gunakan indeks antara 0 dan {length - 1}."
        )


class KeyNotFoundError(RuntimeError_):
    """Key does not exist in map."""
    code = "H307"

    def __init__(self, key, location=None):
        super().__init__(
            f"Kunci '{key}' tidak ditemukan dalam peta",
            location,
            help_text="Periksa apakah kunci sudah ada sebelum mengaksesnya."
        )


class ReadOnlyError(RuntimeError_):
    """Attempted to reassign a constant."""
    code = "H308"

    def __init__(self, name, location=None):
        super().__init__(
            f"Variabel '{name}' bersifat konstan dan tidak bisa diubah",
            location,
            help_text="Gunakan 'tetapkan' alih-alih 'konstan' jika nilai perlu diubah."
        )


class ImportError_(RuntimeError_):
    """Failed to import a module."""
    code = "H309"

    def __init__(self, module_name, location=None):
        super().__init__(
            f"Modul '{module_name}' tidak ditemukan",
            location,
            help_text=f"Periksa nama modul. Modul yang tersedia: math, text, list, file, json, time, random, system"
        )


class LoopLimitError(RuntimeError_):
    """Loop exceeded maximum iteration count."""
    code = "H310"

    def __init__(self, limit, location=None):
        super().__init__(
            f"Loop melebihi batas iterasi maksimum ({limit})",
            location,
            help_text="Tambahkan kondisi berhenti yang tepat untuk loop Anda."
        )


class ReturnSignal(Exception):
    """Internal signal used to propagate return values up the call stack."""
    def __init__(self, value):
        self.value = value
        super().__init__()


class BreakSignal(Exception):
    """Internal signal for 'berhenti' (break) statements."""
    pass


class ContinueSignal(Exception):
    """Internal signal for 'lanjut' (continue) statements."""
    pass

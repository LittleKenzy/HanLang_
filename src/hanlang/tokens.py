"""
HanLang Token Definitions
=========================

All token types used by the HanLang lexer.
"""

from enum import Enum, auto


class TokenType(Enum):
    """Every token type in the HanLang language."""

    # ── Literals ──────────────────────────────────────────────────
    INTEGER = auto()       # 42
    FLOAT = auto()         # 3.14
    STRING = auto()        # "hello"
    BOOLEAN = auto()       # Benar / Salah
    NULL = auto()          # kosong

    # ── Identifiers ───────────────────────────────────────────────
    IDENTIFIER = auto()    # variable/function names

    # ── Keywords ──────────────────────────────────────────────────
    TETAPKAN = auto()      # tetapkan  (let/var declaration)
    KONSTAN = auto()       # konstan   (const declaration)
    JIKA = auto()          # jika      (if)
    JIKA_TIDAK_JIKA = auto()  # jika_tidak_jika (else if)
    JIKA_TIDAK = auto()    # jika_tidak (else)
    FUNGSI = auto()        # fungsi    (function)
    KEMBALI = auto()       # kembali   (return)
    ULANGI = auto()        # ulangi    (loop keyword)
    UNTUK = auto()         # untuk     (for)
    SELAMA = auto()        # selama    (while)
    DALAM = auto()         # dalam     (in)
    BERHENTI = auto()      # berhenti  (break)
    LANJUT = auto()        # lanjut    (continue)
    DAN = auto()           # dan       (and)
    ATAU = auto()          # atau      (or)
    BUKAN = auto()         # bukan     (not)
    COBA = auto()          # coba      (try)
    TANGKAP = auto()       # tangkap   (catch)
    AKHIRNYA = auto()      # akhirnya  (finally)
    IMPOR = auto()         # impor     (import)
    DARI = auto()          # dari      (from)
    KELAS = auto()         # kelas     (class)
    DIRI = auto()          # diri      (self)
    UJI = auto()           # uji       (test)
    PASTIKAN = auto()      # pastikan  (assert)
    JELAJAHI = auto()      # jelajahi  (explore/inspect)
    COCOKKAN = auto()      # cocokkan  (match/switch)
    POLA = auto()          # pola      (case/pattern)
    LAINNYA = auto()       # lainnya   (default case)

    # ── Operators ─────────────────────────────────────────────────
    PLUS = auto()          # +
    MINUS = auto()         # -
    STAR = auto()          # *
    SLASH = auto()         # /
    FLOOR_DIV = auto()     # //
    PERCENT = auto()       # %
    POWER = auto()         # **
    ASSIGN = auto()        # =
    EQ = auto()            # ==
    NEQ = auto()           # !=
    LT = auto()            # <
    GT = auto()            # >
    LTE = auto()           # <=
    GTE = auto()           # >=
    PLUS_ASSIGN = auto()   # +=
    MINUS_ASSIGN = auto()  # -=
    STAR_ASSIGN = auto()   # *=
    SLASH_ASSIGN = auto()  # /=
    PIPE = auto()          # |>  (pipeline operator)
    ARROW = auto()         # =>  (lambda arrow)
    DOT = auto()           # .

    # ── Delimiters ────────────────────────────────────────────────
    LPAREN = auto()        # (
    RPAREN = auto()        # )
    LBRACE = auto()        # {
    RBRACE = auto()        # }
    LBRACKET = auto()      # [
    RBRACKET = auto()      # ]
    COMMA = auto()         # ,
    COLON = auto()         # :
    SEMICOLON = auto()     # ;  (optional line terminator)

    # ── Special ───────────────────────────────────────────────────
    NEWLINE = auto()       # line break
    EOF = auto()           # end of file
    COMMENT = auto()       # # comment (skipped)


class Token:
    """A single lexical token with source position information."""

    __slots__ = ("type", "value", "line", "column", "length")

    def __init__(self, type, value, line=0, column=0, length=0):
        self.type = type
        self.value = value
        self.line = line
        self.column = column
        self.length = length

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.column})"

    def __eq__(self, other):
        if isinstance(other, Token):
            return self.type == other.type and self.value == other.value
        return NotImplemented


# ── Keyword lookup table ──────────────────────────────────────────

KEYWORDS = {
    "tetapkan": TokenType.TETAPKAN,
    "konstan": TokenType.KONSTAN,
    "jika": TokenType.JIKA,
    "jika_tidak_jika": TokenType.JIKA_TIDAK_JIKA,
    "jika_tidak": TokenType.JIKA_TIDAK,
    "fungsi": TokenType.FUNGSI,
    "kembali": TokenType.KEMBALI,
    "ulangi": TokenType.ULANGI,
    "untuk": TokenType.UNTUK,
    "selama": TokenType.SELAMA,
    "dalam": TokenType.DALAM,
    "berhenti": TokenType.BERHENTI,
    "lanjut": TokenType.LANJUT,
    "dan": TokenType.DAN,
    "atau": TokenType.ATAU,
    "bukan": TokenType.BUKAN,
    "coba": TokenType.COBA,
    "tangkap": TokenType.TANGKAP,
    "akhirnya": TokenType.AKHIRNYA,
    "impor": TokenType.IMPOR,
    "dari": TokenType.DARI,
    "kelas": TokenType.KELAS,
    "diri": TokenType.DIRI,
    "uji": TokenType.UJI,
    "pastikan": TokenType.PASTIKAN,
    "jelajahi": TokenType.JELAJAHI,
    "cocokkan": TokenType.COCOKKAN,
    "pola": TokenType.POLA,
    "lainnya": TokenType.LAINNYA,
    "Benar": TokenType.BOOLEAN,
    "Salah": TokenType.BOOLEAN,
    "kosong": TokenType.NULL,
}

"""
HanLang Lexer
=============

Converts HanLang source code into a stream of tokens. Handles strings with
interpolation markers, comments, multi-character operators, numbers, and
keywords with full source position tracking.
"""

from .tokens import Token, TokenType, KEYWORDS
from .errors import (
    LexerError,
    UnterminatedStringError,
    InvalidCharacterError,
    InvalidNumberError,
    SourceLocation,
)


class Lexer:
    """Tokenizes HanLang source code."""

    def __init__(self, source, filename="<stdin>"):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []

    def _location(self, length=1):
        """Create a SourceLocation for the current position."""
        return SourceLocation(self.filename, self.line, self.column, length)

    def _peek(self, offset=0):
        """Look at a character without consuming it."""
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return "\0"

    def _advance(self):
        """Consume the current character and return it."""
        if self.pos >= len(self.source):
            return "\0"
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _match(self, expected):
        """Consume the next character if it matches."""
        if self._peek() == expected:
            self._advance()
            return True
        return False

    def _add_token(self, type, value, line, column, length=None):
        """Add a token to the list."""
        if length is None:
            length = len(str(value))
        self.tokens.append(Token(type, value, line, column, length))

    def _skip_whitespace_and_comments(self):
        """Skip spaces, tabs, and comments. Emit NEWLINE tokens."""
        while self.pos < len(self.source):
            ch = self._peek()

            if ch in (" ", "\t", "\r"):
                self._advance()
            elif ch == "\n":
                line, col = self.line, self.column
                self._advance()
                # Only add newline if the last token isn't already a newline
                if (not self.tokens or
                        self.tokens[-1].type != TokenType.NEWLINE):
                    self._add_token(TokenType.NEWLINE, "\\n", line, col, 1)
            elif ch == "#":
                # Skip to end of line
                while self.pos < len(self.source) and self._peek() != "\n":
                    self._advance()
            else:
                break

    def _read_string(self, quote_char):
        """Read a string literal, supporting escape sequences and interpolation."""
        start_line = self.line
        start_col = self.column
        self._advance()  # consume opening quote

        result = []
        has_interpolation = False

        while self.pos < len(self.source):
            ch = self._peek()

            if ch == "\\":
                self._advance()
                esc = self._advance()
                escape_map = {
                    "n": "\n",
                    "t": "\t",
                    "r": "\r",
                    "\\": "\\",
                    "'": "'",
                    '"': '"',
                    "{": "{",
                    "}": "}",
                    "0": "\0",
                }
                if esc in escape_map:
                    result.append(escape_map[esc])
                else:
                    result.append("\\" + esc)
            elif ch == "{" and quote_char == '"':
                # String interpolation: collect the expression inside braces
                self._advance()  # skip {
                has_interpolation = True
                expr_chars = []
                brace_depth = 1
                while self.pos < len(self.source) and brace_depth > 0:
                    ic = self._peek()
                    if ic == "{":
                        brace_depth += 1
                    elif ic == "}":
                        brace_depth -= 1
                        if brace_depth == 0:
                            self._advance()  # skip closing }
                            break
                    expr_chars.append(ic)
                    self._advance()
                else:
                    if brace_depth > 0:
                        loc = SourceLocation(self.filename, start_line, start_col)
                        raise UnterminatedStringError(loc)
                # Store interpolation as a special marker
                result.append(("\x00INTERP\x00", "".join(expr_chars)))
            elif ch == quote_char:
                self._advance()  # consume closing quote
                # Build the final string value
                if has_interpolation:
                    # Store as a list of parts for the runtime to process
                    parts = []
                    current_str = []
                    for item in result:
                        if isinstance(item, tuple) and item[0] == "\x00INTERP\x00":
                            if current_str:
                                parts.append(("str", "".join(current_str)))
                                current_str = []
                            parts.append(("expr", item[1]))
                        else:
                            current_str.append(item)
                    if current_str:
                        parts.append(("str", "".join(current_str)))
                    self._add_token(
                        TokenType.STRING, parts,
                        start_line, start_col,
                        self.column - start_col
                    )
                else:
                    text = "".join(result)
                    self._add_token(
                        TokenType.STRING, text,
                        start_line, start_col,
                        self.column - start_col
                    )
                return

            elif ch == "\n":
                loc = SourceLocation(self.filename, start_line, start_col)
                raise UnterminatedStringError(loc)
            else:
                result.append(ch)
                self._advance()

        loc = SourceLocation(self.filename, start_line, start_col)
        raise UnterminatedStringError(loc)

    def _read_number(self):
        """Read an integer or float literal."""
        start_line = self.line
        start_col = self.column
        start_pos = self.pos
        has_dot = False

        while self.pos < len(self.source):
            ch = self._peek()
            if ch == ".":
                if has_dot:
                    break
                # Check it's not a method call like 123.toString()
                if self._peek(1).isdigit():
                    has_dot = True
                    self._advance()
                else:
                    break
            elif ch.isdigit() or ch == "_":
                self._advance()
            else:
                break

        text = self.source[start_pos:self.pos].replace("_", "")

        try:
            if has_dot:
                value = float(text)
                self._add_token(TokenType.FLOAT, value,
                                start_line, start_col, len(text))
            else:
                value = int(text)
                self._add_token(TokenType.INTEGER, value,
                                start_line, start_col, len(text))
        except ValueError:
            loc = SourceLocation(self.filename, start_line, start_col, len(text))
            raise InvalidNumberError(text, loc)

    def _read_identifier_or_keyword(self):
        """Read an identifier or keyword, supporting underscores in keywords."""
        start_line = self.line
        start_col = self.column
        start_pos = self.pos

        while self.pos < len(self.source):
            ch = self._peek()
            if ch.isalnum() or ch == "_":
                self._advance()
            else:
                break

        text = self.source[start_pos:self.pos]

        # Check for multi-word keywords: jika_tidak_jika, jika_tidak
        if text in KEYWORDS:
            ttype = KEYWORDS[text]
            if ttype == TokenType.BOOLEAN:
                value = True if text == "Benar" else False
                self._add_token(ttype, value, start_line, start_col, len(text))
            elif ttype == TokenType.NULL:
                self._add_token(ttype, None, start_line, start_col, len(text))
            else:
                self._add_token(ttype, text, start_line, start_col, len(text))
        else:
            self._add_token(TokenType.IDENTIFIER, text,
                            start_line, start_col, len(text))

    def tokenize(self):
        """Tokenize the entire source and return a list of tokens."""
        self.tokens = []
        self.pos = 0
        self.line = 1
        self.column = 1

        while self.pos < len(self.source):
            self._skip_whitespace_and_comments()

            if self.pos >= len(self.source):
                break

            ch = self._peek()
            line, col = self.line, self.column

            # String literals
            if ch in ('"', "'"):
                self._read_string(ch)
                continue

            # Numbers
            if ch.isdigit():
                self._read_number()
                continue

            # Identifiers and keywords
            if ch.isalpha() or ch == "_":
                self._read_identifier_or_keyword()
                continue

            # Multi-character operators
            if ch == "|" and self._peek(1) == ">":
                self._advance()
                self._advance()
                self._add_token(TokenType.PIPE, "|>", line, col, 2)
                continue

            if ch == "=" and self._peek(1) == ">":
                self._advance()
                self._advance()
                self._add_token(TokenType.ARROW, "=>", line, col, 2)
                continue

            if ch == "*" and self._peek(1) == "*":
                self._advance()
                self._advance()
                self._add_token(TokenType.POWER, "**", line, col, 2)
                continue

            if ch == "/" and self._peek(1) == "/":
                self._advance()
                self._advance()
                self._add_token(TokenType.FLOOR_DIV, "//", line, col, 2)
                continue

            if ch == "=" and self._peek(1) == "=":
                self._advance()
                self._advance()
                self._add_token(TokenType.EQ, "==", line, col, 2)
                continue

            if ch == "!" and self._peek(1) == "=":
                self._advance()
                self._advance()
                self._add_token(TokenType.NEQ, "!=", line, col, 2)
                continue

            if ch == "<" and self._peek(1) == "=":
                self._advance()
                self._advance()
                self._add_token(TokenType.LTE, "<=", line, col, 2)
                continue

            if ch == ">" and self._peek(1) == "=":
                self._advance()
                self._advance()
                self._add_token(TokenType.GTE, ">=", line, col, 2)
                continue

            if ch == "+" and self._peek(1) == "=":
                self._advance()
                self._advance()
                self._add_token(TokenType.PLUS_ASSIGN, "+=", line, col, 2)
                continue

            if ch == "-" and self._peek(1) == "=":
                self._advance()
                self._advance()
                self._add_token(TokenType.MINUS_ASSIGN, "-=", line, col, 2)
                continue

            if ch == "*" and self._peek(1) == "=":
                self._advance()
                self._advance()
                self._add_token(TokenType.STAR_ASSIGN, "*=", line, col, 2)
                continue

            if ch == "/" and self._peek(1) == "=":
                self._advance()
                self._advance()
                self._add_token(TokenType.SLASH_ASSIGN, "/=", line, col, 2)
                continue

            # Single-character operators and delimiters
            single_chars = {
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.STAR,
                "/": TokenType.SLASH,
                "%": TokenType.PERCENT,
                "=": TokenType.ASSIGN,
                "<": TokenType.LT,
                ">": TokenType.GT,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                "{": TokenType.LBRACE,
                "}": TokenType.RBRACE,
                "[": TokenType.LBRACKET,
                "]": TokenType.RBRACKET,
                ",": TokenType.COMMA,
                ":": TokenType.COLON,
                ";": TokenType.SEMICOLON,
                ".": TokenType.DOT,
            }

            if ch in single_chars:
                self._advance()
                self._add_token(single_chars[ch], ch, line, col, 1)
                continue

            # Unknown character
            loc = SourceLocation(self.filename, line, col, 1)
            raise InvalidCharacterError(ch, loc)

        # Add EOF
        self._add_token(TokenType.EOF, "", self.line, self.column, 0)

        # Strip leading/trailing newlines
        while len(self.tokens) > 1 and self.tokens[0].type == TokenType.NEWLINE:
            self.tokens.pop(0)

        return self.tokens


def tokenize(source, filename="<stdin>"):
    """Convenience function to tokenize source code."""
    return Lexer(source, filename).tokenize()

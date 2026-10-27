"""
HanLang Lexer Tests
===================
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hanlang.lexer import tokenize
from hanlang.tokens import TokenType
from hanlang.errors import UnterminatedStringError, InvalidCharacterError


class TestLexerBasics(unittest.TestCase):
    """Test basic token recognition."""

    def test_integer(self):
        tokens = tokenize("42")
        self.assertEqual(tokens[0].type, TokenType.INTEGER)
        self.assertEqual(tokens[0].value, 42)

    def test_float(self):
        tokens = tokenize("3.14")
        self.assertEqual(tokens[0].type, TokenType.FLOAT)
        self.assertAlmostEqual(tokens[0].value, 3.14)

    def test_string_double_quote(self):
        tokens = tokenize('"hello"')
        self.assertEqual(tokens[0].type, TokenType.STRING)
        self.assertEqual(tokens[0].value, "hello")

    def test_string_single_quote(self):
        tokens = tokenize("'world'")
        self.assertEqual(tokens[0].type, TokenType.STRING)
        self.assertEqual(tokens[0].value, "world")

    def test_string_escape(self):
        tokens = tokenize(r'"hello\nworld"')
        self.assertEqual(tokens[0].value, "hello\nworld")

    def test_string_interpolation(self):
        tokens = tokenize('"hello {nama}"')
        self.assertEqual(tokens[0].type, TokenType.STRING)
        self.assertIsInstance(tokens[0].value, list)
        self.assertEqual(len(tokens[0].value), 2)
        self.assertEqual(tokens[0].value[0], ("str", "hello "))
        self.assertEqual(tokens[0].value[1][0], "expr")

    def test_boolean_benar(self):
        tokens = tokenize("Benar")
        self.assertEqual(tokens[0].type, TokenType.BOOLEAN)
        self.assertEqual(tokens[0].value, True)

    def test_boolean_salah(self):
        tokens = tokenize("Salah")
        self.assertEqual(tokens[0].type, TokenType.BOOLEAN)
        self.assertEqual(tokens[0].value, False)

    def test_null(self):
        tokens = tokenize("kosong")
        self.assertEqual(tokens[0].type, TokenType.NULL)
        self.assertIsNone(tokens[0].value)

    def test_identifier(self):
        tokens = tokenize("nama_saya")
        self.assertEqual(tokens[0].type, TokenType.IDENTIFIER)
        self.assertEqual(tokens[0].value, "nama_saya")

    def test_eof(self):
        tokens = tokenize("")
        self.assertEqual(tokens[-1].type, TokenType.EOF)


class TestLexerKeywords(unittest.TestCase):
    """Test keyword recognition."""

    def test_tetapkan(self):
        tokens = tokenize("tetapkan")
        self.assertEqual(tokens[0].type, TokenType.TETAPKAN)

    def test_konstan(self):
        tokens = tokenize("konstan")
        self.assertEqual(tokens[0].type, TokenType.KONSTAN)

    def test_jika(self):
        tokens = tokenize("jika")
        self.assertEqual(tokens[0].type, TokenType.JIKA)

    def test_jika_tidak_jika(self):
        tokens = tokenize("jika_tidak_jika")
        self.assertEqual(tokens[0].type, TokenType.JIKA_TIDAK_JIKA)

    def test_jika_tidak(self):
        tokens = tokenize("jika_tidak")
        self.assertEqual(tokens[0].type, TokenType.JIKA_TIDAK)

    def test_fungsi(self):
        tokens = tokenize("fungsi")
        self.assertEqual(tokens[0].type, TokenType.FUNGSI)

    def test_kembali(self):
        tokens = tokenize("kembali")
        self.assertEqual(tokens[0].type, TokenType.KEMBALI)

    def test_ulangi(self):
        tokens = tokenize("ulangi")
        self.assertEqual(tokens[0].type, TokenType.ULANGI)

    def test_untuk(self):
        tokens = tokenize("untuk")
        self.assertEqual(tokens[0].type, TokenType.UNTUK)

    def test_selama(self):
        tokens = tokenize("selama")
        self.assertEqual(tokens[0].type, TokenType.SELAMA)

    def test_dalam(self):
        tokens = tokenize("dalam")
        self.assertEqual(tokens[0].type, TokenType.DALAM)

    def test_coba(self):
        tokens = tokenize("coba")
        self.assertEqual(tokens[0].type, TokenType.COBA)

    def test_tangkap(self):
        tokens = tokenize("tangkap")
        self.assertEqual(tokens[0].type, TokenType.TANGKAP)


class TestLexerOperators(unittest.TestCase):
    """Test operator tokenization."""

    def test_arithmetic(self):
        tokens = tokenize("+ - * / // % **")
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        self.assertIn(TokenType.PLUS, types)
        self.assertIn(TokenType.MINUS, types)
        self.assertIn(TokenType.STAR, types)
        self.assertIn(TokenType.SLASH, types)
        self.assertIn(TokenType.FLOOR_DIV, types)
        self.assertIn(TokenType.PERCENT, types)
        self.assertIn(TokenType.POWER, types)

    def test_comparison(self):
        tokens = tokenize("== != < > <= >=")
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        self.assertIn(TokenType.EQ, types)
        self.assertIn(TokenType.NEQ, types)
        self.assertIn(TokenType.LT, types)
        self.assertIn(TokenType.GT, types)
        self.assertIn(TokenType.LTE, types)
        self.assertIn(TokenType.GTE, types)

    def test_assignment(self):
        tokens = tokenize("= += -= *= /=")
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        self.assertIn(TokenType.ASSIGN, types)
        self.assertIn(TokenType.PLUS_ASSIGN, types)
        self.assertIn(TokenType.MINUS_ASSIGN, types)
        self.assertIn(TokenType.STAR_ASSIGN, types)
        self.assertIn(TokenType.SLASH_ASSIGN, types)

    def test_pipeline(self):
        tokens = tokenize("|>")
        self.assertEqual(tokens[0].type, TokenType.PIPE)

    def test_arrow(self):
        tokens = tokenize("=>")
        self.assertEqual(tokens[0].type, TokenType.ARROW)

    def test_delimiters(self):
        tokens = tokenize("( ) { } [ ] , : .")
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        self.assertIn(TokenType.LPAREN, types)
        self.assertIn(TokenType.RPAREN, types)
        self.assertIn(TokenType.LBRACE, types)
        self.assertIn(TokenType.RBRACE, types)
        self.assertIn(TokenType.LBRACKET, types)
        self.assertIn(TokenType.RBRACKET, types)
        self.assertIn(TokenType.COMMA, types)
        self.assertIn(TokenType.COLON, types)
        self.assertIn(TokenType.DOT, types)


class TestLexerComments(unittest.TestCase):
    """Test comment handling."""

    def test_line_comment(self):
        tokens = tokenize("42 # this is a comment")
        non_special = [t for t in tokens if t.type not in (TokenType.EOF, TokenType.NEWLINE)]
        self.assertEqual(len(non_special), 1)
        self.assertEqual(non_special[0].value, 42)

    def test_comment_only_line(self):
        tokens = tokenize("# just a comment")
        non_special = [t for t in tokens if t.type not in (TokenType.EOF, TokenType.NEWLINE)]
        self.assertEqual(len(non_special), 0)


class TestLexerErrors(unittest.TestCase):
    """Test lexer error handling."""

    def test_unterminated_string(self):
        with self.assertRaises(UnterminatedStringError):
            tokenize('"hello')

    def test_invalid_character(self):
        with self.assertRaises(InvalidCharacterError):
            tokenize("@")


class TestLexerPositions(unittest.TestCase):
    """Test source position tracking."""

    def test_line_numbers(self):
        tokens = tokenize("a\nb\nc")
        idents = [t for t in tokens if t.type == TokenType.IDENTIFIER]
        self.assertEqual(idents[0].line, 1)
        self.assertEqual(idents[1].line, 2)
        self.assertEqual(idents[2].line, 3)

    def test_column_numbers(self):
        tokens = tokenize("abc def")
        idents = [t for t in tokens if t.type == TokenType.IDENTIFIER]
        self.assertEqual(idents[0].column, 1)
        self.assertEqual(idents[1].column, 5)


if __name__ == "__main__":
    unittest.main()

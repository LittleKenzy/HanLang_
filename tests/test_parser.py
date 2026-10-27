"""
HanLang Parser Tests
====================
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hanlang.lexer import tokenize
from hanlang.parser import parse
from hanlang.nodes import *
from hanlang.errors import ParseError


class TestParserExpressions(unittest.TestCase):
    """Test expression parsing."""

    def _parse_expr(self, source):
        tokens = tokenize(source)
        program = parse(tokens)
        self.assertEqual(len(program.statements), 1)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ExpressionStatement)
        return stmt.expression

    def test_integer_literal(self):
        expr = self._parse_expr("42")
        self.assertIsInstance(expr, NumberLiteral)
        self.assertEqual(expr.value, 42)

    def test_float_literal(self):
        expr = self._parse_expr("3.14")
        self.assertIsInstance(expr, NumberLiteral)
        self.assertAlmostEqual(expr.value, 3.14)

    def test_string_literal(self):
        expr = self._parse_expr('"hello"')
        self.assertIsInstance(expr, StringLiteral)
        self.assertEqual(expr.value, "hello")

    def test_boolean_literal(self):
        expr = self._parse_expr("Benar")
        self.assertIsInstance(expr, BooleanLiteral)
        self.assertTrue(expr.value)

    def test_null_literal(self):
        expr = self._parse_expr("kosong")
        self.assertIsInstance(expr, NullLiteral)

    def test_identifier(self):
        expr = self._parse_expr("nama")
        self.assertIsInstance(expr, Identifier)
        self.assertEqual(expr.name, "nama")

    def test_binary_addition(self):
        expr = self._parse_expr("1 + 2")
        self.assertIsInstance(expr, BinaryOp)
        self.assertEqual(expr.operator, "+")

    def test_operator_precedence(self):
        expr = self._parse_expr("1 + 2 * 3")
        self.assertIsInstance(expr, BinaryOp)
        self.assertEqual(expr.operator, "+")
        self.assertIsInstance(expr.right, BinaryOp)
        self.assertEqual(expr.right.operator, "*")

    def test_parentheses(self):
        expr = self._parse_expr("(1 + 2) * 3")
        self.assertIsInstance(expr, BinaryOp)
        self.assertEqual(expr.operator, "*")
        self.assertIsInstance(expr.left, BinaryOp)
        self.assertEqual(expr.left.operator, "+")

    def test_power_right_assoc(self):
        expr = self._parse_expr("2 ** 3 ** 2")
        self.assertIsInstance(expr, BinaryOp)
        self.assertEqual(expr.operator, "**")
        self.assertIsInstance(expr.right, BinaryOp)

    def test_comparison(self):
        expr = self._parse_expr("a > b")
        self.assertIsInstance(expr, ComparisonOp)
        self.assertEqual(expr.operator, ">")

    def test_logical_and(self):
        expr = self._parse_expr("a dan b")
        self.assertIsInstance(expr, LogicalOp)
        self.assertEqual(expr.operator, "dan")

    def test_logical_or(self):
        expr = self._parse_expr("a atau b")
        self.assertIsInstance(expr, LogicalOp)
        self.assertEqual(expr.operator, "atau")

    def test_logical_not(self):
        expr = self._parse_expr("bukan a")
        self.assertIsInstance(expr, UnaryOp)
        self.assertEqual(expr.operator, "bukan")

    def test_unary_minus(self):
        expr = self._parse_expr("-42")
        self.assertIsInstance(expr, UnaryOp)
        self.assertEqual(expr.operator, "-")

    def test_function_call(self):
        expr = self._parse_expr("tampil(42)")
        self.assertIsInstance(expr, FunctionCall)
        self.assertEqual(len(expr.arguments), 1)

    def test_function_call_multiple_args(self):
        expr = self._parse_expr("fungsi_saya(1, 2, 3)")
        self.assertIsInstance(expr, FunctionCall)
        self.assertEqual(len(expr.arguments), 3)

    def test_index_access(self):
        expr = self._parse_expr("data[0]")
        self.assertIsInstance(expr, IndexAccess)

    def test_dot_access(self):
        expr = self._parse_expr("obj.nama")
        self.assertIsInstance(expr, DotAccess)
        self.assertEqual(expr.attribute, "nama")

    def test_method_call(self):
        expr = self._parse_expr("obj.metode()")
        self.assertIsInstance(expr, MethodCall)
        self.assertEqual(expr.method, "metode")

    def test_list_literal(self):
        expr = self._parse_expr("[1, 2, 3]")
        self.assertIsInstance(expr, ListLiteral)
        self.assertEqual(len(expr.elements), 3)

    def test_empty_list(self):
        expr = self._parse_expr("[]")
        self.assertIsInstance(expr, ListLiteral)
        self.assertEqual(len(expr.elements), 0)

    def test_lambda_single_param(self):
        expr = self._parse_expr("x => x + 1")
        self.assertIsInstance(expr, LambdaExpression)
        self.assertEqual(expr.params, ["x"])

    def test_lambda_multi_param(self):
        expr = self._parse_expr("(a, b) => a + b")
        self.assertIsInstance(expr, LambdaExpression)
        self.assertEqual(expr.params, ["a", "b"])

    def test_pipeline(self):
        expr = self._parse_expr("data |> tampil")
        self.assertIsInstance(expr, PipeExpression)


class TestParserStatements(unittest.TestCase):
    """Test statement parsing."""

    def _parse(self, source):
        tokens = tokenize(source)
        return parse(tokens)

    def test_variable_declaration(self):
        program = self._parse("tetapkan x = 42")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, VariableDeclaration)
        self.assertEqual(stmt.name, "x")
        self.assertFalse(stmt.is_constant)

    def test_constant_declaration(self):
        program = self._parse("konstan PI = 3.14")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, VariableDeclaration)
        self.assertTrue(stmt.is_constant)

    def test_assignment(self):
        program = self._parse("x = 42")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, Assignment)

    def test_compound_assignment(self):
        program = self._parse("x += 1")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, Assignment)
        self.assertEqual(stmt.operator, "+=")

    def test_if_statement(self):
        program = self._parse("jika x > 0 { tampil(x) }")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, IfStatement)
        self.assertIsNotNone(stmt.body)

    def test_if_else(self):
        program = self._parse("jika x > 0 { tampil(1) } jika_tidak { tampil(0) }")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, IfStatement)
        self.assertIsNotNone(stmt.else_body)

    def test_if_elif_else(self):
        src = """jika x > 10 {
            tampil("besar")
        } jika_tidak_jika x > 5 {
            tampil("sedang")
        } jika_tidak {
            tampil("kecil")
        }"""
        program = self._parse(src)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, IfStatement)
        self.assertEqual(len(stmt.elif_clauses), 1)
        self.assertIsNotNone(stmt.else_body)

    def test_while_loop(self):
        program = self._parse("ulangi selama x > 0 { x -= 1 }")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, WhileLoop)

    def test_for_loop(self):
        program = self._parse("ulangi untuk i dalam rentang(10) { tampil(i) }")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ForLoop)
        self.assertEqual(stmt.variable, "i")

    def test_for_in_loop(self):
        program = self._parse("untuk x dalam data { tampil(x) }")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ForInLoop)

    def test_function_declaration(self):
        program = self._parse("fungsi salam(nama) { tampil(nama) }")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, FunctionDeclaration)
        self.assertEqual(stmt.name, "salam")
        self.assertEqual(stmt.params, ["nama"])

    def test_return_statement(self):
        program = self._parse("fungsi f() { kembali 42 }")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, FunctionDeclaration)
        body_stmt = stmt.body.statements[0]
        self.assertIsInstance(body_stmt, ReturnStatement)

    def test_try_catch(self):
        program = self._parse("coba { tampil(1) } tangkap e { tampil(e) }")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, TryCatch)
        self.assertEqual(stmt.catch_var, "e")

    def test_import_statement(self):
        program = self._parse("impor math")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ImportStatement)
        self.assertEqual(stmt.module_name, "math")

    def test_test_block(self):
        program = self._parse('uji "test_name" { pastikan Benar }')
        stmt = program.statements[0]
        self.assertIsInstance(stmt, TestBlock)
        self.assertEqual(stmt.description, "test_name")

    def test_assert_statement(self):
        program = self._parse("pastikan 2 + 2 == 4")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, AssertStatement)

    def test_explore_statement(self):
        program = self._parse("jelajahi data")
        stmt = program.statements[0]
        self.assertIsInstance(stmt, ExploreStatement)

    def test_match_statement(self):
        src = 'cocokkan x { pola 1 { tampil("satu") } lainnya { tampil("lain") } }'
        program = self._parse(src)
        stmt = program.statements[0]
        self.assertIsInstance(stmt, MatchStatement)
        self.assertEqual(len(stmt.cases), 1)
        self.assertIsNotNone(stmt.default_case)

    def test_break_continue(self):
        src = "ulangi selama Benar { berhenti }"
        program = self._parse(src)
        stmt = program.statements[0]
        body_stmt = stmt.body.statements[0]
        self.assertIsInstance(body_stmt, BreakStatement)


class TestParserErrors(unittest.TestCase):
    """Test parser error handling."""

    def test_missing_brace(self):
        with self.assertRaises(ParseError):
            tokens = tokenize("jika Benar {")
            parse(tokens)

    def test_unexpected_token(self):
        with self.assertRaises(ParseError):
            tokens = tokenize("tetapkan = 42")
            parse(tokens)


if __name__ == "__main__":
    unittest.main()

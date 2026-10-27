"""
HanLang Runtime Tests
=====================
"""
import unittest
import sys
import os
import io
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hanlang.lexer import tokenize
from hanlang.parser import parse
from hanlang.runtime import Interpreter
from hanlang.values import *
from hanlang.errors import (
    UndefinedVariableError, DivisionByZeroError, TypeMismatchError,
    ArgumentError, IndexOutOfRangeError, ReadOnlyError,
    RecursionLimitError, LoopLimitError, ImportError_, HanError,
)


class RuntimeTestCase(unittest.TestCase):
    """Base class with helpers for runtime tests."""

    def _run(self, source):
        """Run source code and return the interpreter."""
        tokens = tokenize(source)
        ast = parse(tokens)
        interp = Interpreter("<test>", source.splitlines())
        interp.execute(ast)
        return interp

    def _run_get_var(self, source, var_name):
        """Run source and return a variable's value."""
        interp = self._run(source)
        return interp.global_env.get(var_name)

    def _run_capture(self, source):
        """Run source and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            self._run(source)
        return f.getvalue()

    def _run_error(self, source, error_type):
        """Run source expecting an error."""
        with self.assertRaises(error_type):
            self._run(source)


class TestVariables(RuntimeTestCase):
    """Test variable declarations and assignments."""

    def test_tetapkan_integer(self):
        val = self._run_get_var("tetapkan x = 42", "x")
        self.assertIsInstance(val, HanNumber)
        self.assertEqual(val.value, 42)

    def test_tetapkan_string(self):
        val = self._run_get_var('tetapkan s = "hello"', "s")
        self.assertIsInstance(val, HanString)
        self.assertEqual(val.value, "hello")

    def test_tetapkan_boolean(self):
        val = self._run_get_var("tetapkan b = Benar", "b")
        self.assertIsInstance(val, HanBoolean)
        self.assertTrue(val.value)

    def test_tetapkan_null(self):
        val = self._run_get_var("tetapkan n = kosong", "n")
        self.assertIsInstance(val, HanNull)

    def test_assignment(self):
        val = self._run_get_var("tetapkan x = 1\nx = 42", "x")
        self.assertEqual(val.value, 42)

    def test_compound_plus(self):
        val = self._run_get_var("tetapkan x = 10\nx += 5", "x")
        self.assertEqual(val.value, 15)

    def test_compound_minus(self):
        val = self._run_get_var("tetapkan x = 10\nx -= 3", "x")
        self.assertEqual(val.value, 7)

    def test_compound_star(self):
        val = self._run_get_var("tetapkan x = 4\nx *= 3", "x")
        self.assertEqual(val.value, 12)

    def test_compound_slash(self):
        val = self._run_get_var("tetapkan x = 10\nx /= 2", "x")
        self.assertEqual(val.value, 5.0)

    def test_constant_cannot_reassign(self):
        self._run_error("konstan X = 1\nX = 2", ReadOnlyError)

    def test_undefined_variable(self):
        self._run_error("tampil(xyz)", UndefinedVariableError)


class TestExpressions(RuntimeTestCase):
    """Test arithmetic and logical expressions."""

    def test_addition(self):
        val = self._run_get_var("tetapkan r = 2 + 3", "r")
        self.assertEqual(val.value, 5)

    def test_subtraction(self):
        val = self._run_get_var("tetapkan r = 10 - 4", "r")
        self.assertEqual(val.value, 6)

    def test_multiplication(self):
        val = self._run_get_var("tetapkan r = 3 * 7", "r")
        self.assertEqual(val.value, 21)

    def test_division(self):
        val = self._run_get_var("tetapkan r = 10 / 4", "r")
        self.assertEqual(val.value, 2.5)

    def test_floor_division(self):
        val = self._run_get_var("tetapkan r = 10 // 3", "r")
        self.assertEqual(val.value, 3)

    def test_modulo(self):
        val = self._run_get_var("tetapkan r = 10 % 3", "r")
        self.assertEqual(val.value, 1)

    def test_power(self):
        val = self._run_get_var("tetapkan r = 2 ** 10", "r")
        self.assertEqual(val.value, 1024)

    def test_precedence(self):
        val = self._run_get_var("tetapkan r = 2 + 3 * 4", "r")
        self.assertEqual(val.value, 14)

    def test_parentheses(self):
        val = self._run_get_var("tetapkan r = (2 + 3) * 4", "r")
        self.assertEqual(val.value, 20)

    def test_unary_minus(self):
        val = self._run_get_var("tetapkan r = -5", "r")
        self.assertEqual(val.value, -5)

    def test_string_concat(self):
        val = self._run_get_var('tetapkan r = "hello" + " " + "world"', "r")
        self.assertEqual(val.value, "hello world")

    def test_string_repeat(self):
        val = self._run_get_var('tetapkan r = "ha" * 3', "r")
        self.assertEqual(val.value, "hahaha")

    def test_comparison_eq(self):
        val = self._run_get_var("tetapkan r = 5 == 5", "r")
        self.assertTrue(val.value)

    def test_comparison_neq(self):
        val = self._run_get_var("tetapkan r = 5 != 3", "r")
        self.assertTrue(val.value)

    def test_comparison_lt(self):
        val = self._run_get_var("tetapkan r = 3 < 5", "r")
        self.assertTrue(val.value)

    def test_comparison_gt(self):
        val = self._run_get_var("tetapkan r = 5 > 3", "r")
        self.assertTrue(val.value)

    def test_logical_dan(self):
        val = self._run_get_var("tetapkan r = Benar dan Benar", "r")
        self.assertTrue(val.value)

    def test_logical_atau(self):
        val = self._run_get_var("tetapkan r = Salah atau Benar", "r")
        self.assertTrue(val.value)

    def test_logical_bukan(self):
        val = self._run_get_var("tetapkan r = bukan Salah", "r")
        self.assertTrue(val.value)

    def test_division_by_zero(self):
        self._run_error("tetapkan r = 10 / 0", DivisionByZeroError)

    def test_type_mismatch(self):
        self._run_error('tetapkan r = "hello" - 5', TypeMismatchError)


class TestStringInterpolation(RuntimeTestCase):
    """Test string interpolation."""

    def test_simple_interpolation(self):
        output = self._run_capture('tetapkan nama = "dunia"\ntampil("halo {nama}")')
        self.assertIn("halo dunia", output)

    def test_expression_interpolation(self):
        output = self._run_capture('tampil("2 + 3 = {2 + 3}")')
        self.assertIn("2 + 3 = 5", output)

    def test_no_interpolation_single_quote(self):
        output = self._run_capture("tampil('{nama}')")
        self.assertIn("{nama}", output)


class TestConditions(RuntimeTestCase):
    """Test if/elif/else."""

    def test_if_true(self):
        output = self._run_capture('jika Benar { tampil("yes") }')
        self.assertIn("yes", output)

    def test_if_false(self):
        output = self._run_capture('jika Salah { tampil("no") }')
        self.assertEqual(output.strip(), "")

    def test_if_else(self):
        output = self._run_capture('jika Salah { tampil("no") } jika_tidak { tampil("yes") }')
        self.assertIn("yes", output)

    def test_if_elif(self):
        src = """tetapkan x = 5
jika x > 10 {
    tampil("big")
} jika_tidak_jika x > 3 {
    tampil("medium")
} jika_tidak {
    tampil("small")
}"""
        output = self._run_capture(src)
        self.assertIn("medium", output)

    def test_nested_if(self):
        src = """tetapkan x = 5
jika x > 0 {
    jika x < 10 {
        tampil("single digit")
    }
}"""
        output = self._run_capture(src)
        self.assertIn("single digit", output)


class TestLoops(RuntimeTestCase):
    """Test loops."""

    def test_for_loop(self):
        output = self._run_capture("ulangi untuk i dalam rentang(1, 4) { tampil(i) }")
        self.assertIn("1", output)
        self.assertIn("2", output)
        self.assertIn("3", output)

    def test_while_loop(self):
        src = """tetapkan x = 3
ulangi selama x > 0 {
    tampil(x)
    x -= 1
}"""
        output = self._run_capture(src)
        self.assertIn("3", output)
        self.assertIn("2", output)
        self.assertIn("1", output)

    def test_for_in_loop(self):
        output = self._run_capture('untuk x dalam [1, 2, 3] { tampil(x) }')
        self.assertIn("1", output)
        self.assertIn("3", output)

    def test_break(self):
        src = """ulangi untuk i dalam rentang(1, 100) {
    jika i > 3 { berhenti }
    tampil(i)
}"""
        output = self._run_capture(src)
        lines = [l for l in output.strip().split("\n") if l.strip()]
        self.assertEqual(len(lines), 3)

    def test_continue(self):
        src = """ulangi untuk i dalam rentang(1, 6) {
    jika i == 3 { lanjut }
    tampil(i)
}"""
        output = self._run_capture(src)
        self.assertNotIn("3", output.split("\n"))
        self.assertIn("1", output)
        self.assertIn("5", output)


class TestFunctions(RuntimeTestCase):
    """Test function declarations and calls."""

    def test_simple_function(self):
        src = """fungsi dua_kali(x) {
    kembali x * 2
}
tetapkan r = dua_kali(5)"""
        val = self._run_get_var(src, "r")
        self.assertEqual(val.value, 10)

    def test_multiple_params(self):
        src = """fungsi tambah(a, b) {
    kembali a + b
}
tetapkan r = tambah(3, 7)"""
        val = self._run_get_var(src, "r")
        self.assertEqual(val.value, 10)

    def test_recursion_fibonacci(self):
        src = """fungsi fib(n) {
    jika n <= 1 { kembali n }
    kembali fib(n - 1) + fib(n - 2)
}
tetapkan r = fib(10)"""
        val = self._run_get_var(src, "r")
        self.assertEqual(val.value, 55)

    def test_wrong_arg_count(self):
        self._run_error("fungsi f(a) { kembali a }\nf(1, 2)", ArgumentError)

    def test_recursion_limit(self):
        src = """fungsi inf(n) {
    kembali inf(n + 1)
}
inf(0)"""
        with self.assertRaises((RecursionLimitError, RecursionError)):
            self._run(src)

    def test_closure(self):
        src = """tetapkan r = 0
fungsi outer() {
    tetapkan x = 10
    fungsi inner() {
        kembali x
    }
    kembali inner()
}
r = outer()"""
        val = self._run_get_var(src, "r")
        self.assertEqual(val.value, 10)


class TestCollections(RuntimeTestCase):
    """Test lists and maps."""

    def test_list_creation(self):
        val = self._run_get_var("tetapkan l = [1, 2, 3]", "l")
        self.assertIsInstance(val, HanList)
        self.assertEqual(len(val.elements), 3)

    def test_list_index(self):
        val = self._run_get_var("tetapkan l = [10, 20, 30]\ntetapkan r = l[1]", "r")
        self.assertEqual(val.value, 20)

    def test_list_out_of_range(self):
        self._run_error("tetapkan l = [1]\ntetapkan r = l[5]", IndexOutOfRangeError)

    def test_list_append(self):
        val = self._run_get_var("tetapkan l = [1, 2]\ntambah(l, 3)", "l")
        self.assertEqual(len(val.elements), 3)

    def test_list_length(self):
        val = self._run_get_var("tetapkan r = panjang([1, 2, 3])", "r")
        self.assertEqual(val.value, 3)

    def test_list_concat(self):
        val = self._run_get_var("tetapkan r = [1, 2] + [3, 4]", "r")
        self.assertEqual(len(val.elements), 4)

    def test_map_creation(self):
        val = self._run_get_var('tetapkan m = {"a": 1, "b": 2}', "m")
        self.assertIsInstance(val, HanMap)
        self.assertEqual(len(val.entries), 2)

    def test_map_dot_access(self):
        val = self._run_get_var('tetapkan m = {"nama": "test"}\ntetapkan r = m.nama', "r")
        self.assertEqual(val.value, "test")

    def test_map_index_access(self):
        val = self._run_get_var('tetapkan m = {"x": 42}\ntetapkan r = m["x"]', "r")
        self.assertEqual(val.value, 42)


class TestErrorHandling(RuntimeTestCase):
    """Test coba-tangkap error handling."""

    def test_catch_division_by_zero(self):
        output = self._run_capture("""coba {
    tetapkan r = 10 / 0
} tangkap e {
    tampil("caught")
}""")
        self.assertIn("caught", output)

    def test_catch_error_message(self):
        output = self._run_capture("""coba {
    tetapkan r = 10 / 0
} tangkap e {
    tampil(e.pesan)
}""")
        self.assertIn("nol", output)

    def test_finally_runs(self):
        output = self._run_capture("""coba {
    tampil("try")
} tangkap e {
    tampil("catch")
} akhirnya {
    tampil("finally")
}""")
        self.assertIn("try", output)
        self.assertIn("finally", output)
        self.assertNotIn("catch", output)

    def test_finally_runs_on_error(self):
        output = self._run_capture("""coba {
    tetapkan r = 10 / 0
} tangkap e {
    tampil("catch")
} akhirnya {
    tampil("finally")
}""")
        self.assertIn("catch", output)
        self.assertIn("finally", output)


class TestPipeline(RuntimeTestCase):
    """Test pipeline operator."""

    def test_pipeline_simple(self):
        val = self._run_get_var(
            "tetapkan data = [1, 2, 3, 4, 5]\n"
            "tetapkan r = data |> saring(x => x > 3)", "r"
        )
        self.assertIsInstance(val, HanList)
        self.assertEqual(len(val.elements), 2)

    def test_pipeline_ubah(self):
        val = self._run_get_var(
            "tetapkan data = [1, 2, 3]\n"
            "tetapkan r = data |> ubah(x => x * 10)", "r"
        )
        values = [e.value for e in val.elements]
        self.assertEqual(values, [10, 20, 30])

    def test_pipeline_chain(self):
        val = self._run_get_var(
            "tetapkan data = [1, 2, 3, 4, 5]\n"
            "tetapkan r = data |> saring(x => x > 2) |> ubah(x => x * 10)", "r"
        )
        values = [e.value for e in val.elements]
        self.assertEqual(values, [30, 40, 50])


class TestStdlib(RuntimeTestCase):
    """Test standard library modules."""

    def test_import_math(self):
        val = self._run_get_var("impor math\ntetapkan r = math.pi", "r")
        self.assertAlmostEqual(val.value, 3.14159, places=4)

    def test_math_sqrt(self):
        val = self._run_get_var("impor math\ntetapkan r = math.akar(144)", "r")
        self.assertEqual(val.value, 12.0)

    def test_import_text(self):
        val = self._run_get_var('impor text\ntetapkan r = text.huruf_besar("hello")', "r")
        self.assertEqual(val.value, "HELLO")

    def test_invalid_import(self):
        self._run_error("impor nonexistent", ImportError_)


class TestMatch(RuntimeTestCase):
    """Test match statement."""

    def test_match_basic(self):
        src = """tetapkan x = 2
tetapkan r = ""
cocokkan x {
    pola 1 { r = "one" }
    pola 2 { r = "two" }
    lainnya { r = "other" }
}"""
        val = self._run_get_var(src, "r")
        self.assertEqual(val.value, "two")

    def test_match_default(self):
        src = """tetapkan x = 99
tetapkan r = ""
cocokkan x {
    pola 1 { r = "one" }
    lainnya { r = "default" }
}"""
        val = self._run_get_var(src, "r")
        self.assertEqual(val.value, "default")


class TestTestBlocks(RuntimeTestCase):
    """Test the built-in test runner."""

    def test_passing_test(self):
        interp = self._run('uji "test_pass" { pastikan 2 + 2 == 4 }')
        self.assertEqual(len(interp.test_results), 1)
        self.assertTrue(interp.test_results[0][1])

    def test_failing_test(self):
        interp = self._run('uji "test_fail" { pastikan 2 + 2 == 5 }')
        self.assertEqual(len(interp.test_results), 1)
        self.assertFalse(interp.test_results[0][1])


if __name__ == "__main__":
    unittest.main()

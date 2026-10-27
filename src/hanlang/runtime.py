"""
HanLang Runtime (Interpreter)
==============================

Tree-walking interpreter that executes a HanLang AST. Implements lexical
scoping, function calls, loop control, error handling, pipelines, the
data explorer, and all core language semantics.
"""

from .nodes import *
from .values import (
    HanValue, HanNumber, HanString, HanBoolean, HanNull,
    HanList, HanMap, HanFunction, HanLambda, HanBuiltinFunction,
    HanModule, HanError as HanErrorValue,
    python_to_han, han_to_python, value_repr, han_equals,
)
from .errors import (
    HanError,
    RuntimeError_,
    UndefinedVariableError,
    TypeMismatchError,
    DivisionByZeroError,
    ArgumentError,
    RecursionLimitError,
    IndexOutOfRangeError,
    KeyNotFoundError,
    ReadOnlyError,
    ImportError_,
    LoopLimitError,
    ReturnSignal,
    BreakSignal,
    ContinueSignal,
    SourceLocation,
)
from .builtins import get_builtins, STDLIB_MODULES


class Environment:
    """Variable scope with parent chain for lexical scoping."""

    def __init__(self, parent=None):
        self.variables = {}
        self.constants = set()
        self.parent = parent

    def get(self, name, line=0, column=0):
        """Look up a variable, searching parent scopes."""
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get(name, line, column)
        loc = SourceLocation(line=line, column=column)
        raise UndefinedVariableError(name, loc)

    def set(self, name, value, line=0, column=0):
        """Set a variable in the current scope."""
        if name in self.constants:
            loc = SourceLocation(line=line, column=column)
            raise ReadOnlyError(name, loc)
        self.variables[name] = value

    def set_anywhere(self, name, value, line=0, column=0):
        """Set a variable in the scope where it exists, or current scope."""
        if name in self.variables:
            if name in self.constants:
                loc = SourceLocation(line=line, column=column)
                raise ReadOnlyError(name, loc)
            self.variables[name] = value
            return
        if self.parent:
            try:
                self.parent.set_anywhere(name, value, line, column)
                return
            except UndefinedVariableError:
                pass
        self.variables[name] = value

    def declare(self, name, value, is_constant=False):
        """Declare a new variable in the current scope."""
        self.variables[name] = value
        if is_constant:
            self.constants.add(name)

    def has(self, name):
        """Check if a variable exists in any scope."""
        if name in self.variables:
            return True
        if self.parent:
            return self.parent.has(name)
        return False


class Interpreter:
    """HanLang AST interpreter."""

    MAX_RECURSION = 500
    MAX_LOOP_ITERATIONS = 1_000_000

    def __init__(self, filename="<stdin>", source_lines=None):
        self.filename = filename
        self.source_lines = source_lines or []
        self.call_depth = 0
        self.test_results = []
        self.global_env = Environment()

        # Register builtins
        for name, func in get_builtins().items():
            self.global_env.declare(name, func)

    def execute(self, program, env=None):
        """Execute a Program AST node."""
        if env is None:
            env = self.global_env
        result = HanNull()
        for stmt in program.statements:
            result = self._exec_statement(stmt, env)
        return result

    # ── Statement Execution ───────────────────────────────────────

    def _exec_statement(self, node, env):
        """Execute a single statement node."""
        if isinstance(node, VariableDeclaration):
            return self._exec_var_declaration(node, env)
        if isinstance(node, Assignment):
            return self._exec_assignment(node, env)
        if isinstance(node, ExpressionStatement):
            return self._eval_expression(node.expression, env)
        if isinstance(node, IfStatement):
            return self._exec_if(node, env)
        if isinstance(node, WhileLoop):
            return self._exec_while(node, env)
        if isinstance(node, ForLoop):
            return self._exec_for(node, env)
        if isinstance(node, ForInLoop):
            return self._exec_for_in(node, env)
        if isinstance(node, FunctionDeclaration):
            return self._exec_func_declaration(node, env)
        if isinstance(node, ReturnStatement):
            return self._exec_return(node, env)
        if isinstance(node, BreakStatement):
            raise BreakSignal()
        if isinstance(node, ContinueStatement):
            raise ContinueSignal()
        if isinstance(node, TryCatch):
            return self._exec_try_catch(node, env)
        if isinstance(node, ImportStatement):
            return self._exec_import(node, env)
        if isinstance(node, TestBlock):
            return self._exec_test(node, env)
        if isinstance(node, AssertStatement):
            return self._exec_assert(node, env)
        if isinstance(node, ExploreStatement):
            return self._exec_explore(node, env)
        if isinstance(node, MatchStatement):
            return self._exec_match(node, env)
        if isinstance(node, Block):
            return self._exec_block(node, env)

        raise RuntimeError_(
            f"Perintah tidak dikenal: {type(node).__name__}",
            SourceLocation(self.filename, node.line, node.column)
        )

    def _exec_var_declaration(self, node, env):
        value = self._eval_expression(node.value, env)
        env.declare(node.name, value, node.is_constant)
        return value

    def _exec_assignment(self, node, env):
        value = self._eval_expression(node.value, env)

        if isinstance(node.target, Identifier):
            name = node.target.name

            if node.operator == "=":
                env.set_anywhere(name, value, node.line, node.column)
            else:
                current = env.get(name, node.line, node.column)
                computed = self._apply_compound_op(
                    node.operator, current, value, node.line, node.column
                )
                env.set_anywhere(name, computed, node.line, node.column)
            return value

        if isinstance(node.target, IndexAccess):
            obj = self._eval_expression(node.target.object, env)
            idx = self._eval_expression(node.target.index, env)

            if isinstance(obj, HanList) and isinstance(idx, HanNumber):
                index = int(idx.value)
                if 0 <= index < len(obj.elements):
                    if node.operator == "=":
                        obj.elements[index] = value
                    else:
                        obj.elements[index] = self._apply_compound_op(
                            node.operator, obj.elements[index], value,
                            node.line, node.column
                        )
                    return value
                raise IndexOutOfRangeError(
                    index, len(obj.elements),
                    SourceLocation(self.filename, node.line, node.column)
                )
            if isinstance(obj, HanMap):
                if node.operator == "=":
                    obj.entries[idx] = value
                else:
                    if idx not in obj.entries:
                        raise KeyNotFoundError(
                            idx.to_display(),
                            SourceLocation(self.filename, node.line, node.column)
                        )
                    obj.entries[idx] = self._apply_compound_op(
                        node.operator, obj.entries[idx], value,
                        node.line, node.column
                    )
                return value
            raise RuntimeError_(
                f"Tidak bisa mengindeks tipe {obj.type_name()}",
                SourceLocation(self.filename, node.line, node.column)
            )

        if isinstance(node.target, DotAccess):
            obj = self._eval_expression(node.target.object, env)
            if isinstance(obj, HanMap):
                key = HanString(node.target.attribute)
                if node.operator == "=":
                    obj.entries[key] = value
                else:
                    if key not in obj.entries:
                        raise KeyNotFoundError(
                            node.target.attribute,
                            SourceLocation(self.filename, node.line, node.column)
                        )
                    obj.entries[key] = self._apply_compound_op(
                        node.operator, obj.entries[key], value,
                        node.line, node.column
                    )
                return value
            raise RuntimeError_(
                f"Tidak bisa mengakses atribut pada tipe {obj.type_name()}",
                SourceLocation(self.filename, node.line, node.column)
            )

        raise RuntimeError_(
            "Target assignment tidak valid",
            SourceLocation(self.filename, node.line, node.column)
        )

    def _apply_compound_op(self, op, current, value, line, column):
        """Apply compound assignment operator."""
        op_map = {"+=": "+", "-=": "-", "*=": "*", "/=": "/"}
        simple_op = op_map.get(op, op)
        return self._binary_op(simple_op, current, value, line, column)

    def _exec_if(self, node, env):
        condition = self._eval_expression(node.condition, env)
        if self._is_truthy(condition):
            return self._exec_block(node.body, env)

        for elif_cond, elif_body in node.elif_clauses:
            result = self._eval_expression(elif_cond, env)
            if self._is_truthy(result):
                return self._exec_block(elif_body, env)

        if node.else_body:
            return self._exec_block(node.else_body, env)

        return HanNull()

    def _exec_while(self, node, env):
        iterations = 0
        result = HanNull()

        while True:
            iterations += 1
            if iterations > self.MAX_LOOP_ITERATIONS:
                raise LoopLimitError(
                    self.MAX_LOOP_ITERATIONS,
                    SourceLocation(self.filename, node.line, node.column)
                )

            condition = self._eval_expression(node.condition, env)
            if not self._is_truthy(condition):
                break

            try:
                result = self._exec_block(node.body, env)
            except BreakSignal:
                break
            except ContinueSignal:
                continue

        return result

    def _exec_for(self, node, env):
        iterable = self._eval_expression(node.iterable, env)

        if not isinstance(iterable, HanList):
            raise RuntimeError_(
                f"Tidak bisa mengiterasi tipe {iterable.type_name()}",
                SourceLocation(self.filename, node.line, node.column)
            )

        result = HanNull()
        loop_env = Environment(env)
        iterations = 0

        for element in iterable.elements:
            iterations += 1
            if iterations > self.MAX_LOOP_ITERATIONS:
                raise LoopLimitError(
                    self.MAX_LOOP_ITERATIONS,
                    SourceLocation(self.filename, node.line, node.column)
                )

            loop_env.variables[node.variable] = element
            try:
                result = self._exec_block(node.body, loop_env)
            except BreakSignal:
                break
            except ContinueSignal:
                continue

        return result

    def _exec_for_in(self, node, env):
        """Execute: untuk <var> dalam <iterable> { ... }"""
        return self._exec_for(
            ForLoop(node.variable, node.iterable, node.body, node.line, node.column),
            env
        )

    def _exec_func_declaration(self, node, env):
        func = HanFunction(node.name, node.params, node.body, env)
        env.declare(node.name, func)
        return func

    def _exec_return(self, node, env):
        value = HanNull()
        if node.value is not None:
            value = self._eval_expression(node.value, env)
        raise ReturnSignal(value)

    def _exec_try_catch(self, node, env):
        try:
            result = self._exec_block(node.try_body, env)
            if node.finally_body:
                self._exec_block(node.finally_body, env)
            return result
        except (ReturnSignal, BreakSignal, ContinueSignal):
            # Control flow signals pass through — not catchable errors
            if node.finally_body:
                self._exec_block(node.finally_body, env)
            raise
        except HanError as e:
            if node.catch_body:
                catch_env = Environment(env)
                error_val = HanErrorValue(str(e.message), e.code)
                catch_env.declare(node.catch_var, error_val)
                try:
                    result = self._exec_block(node.catch_body, catch_env)
                    if node.finally_body:
                        self._exec_block(node.finally_body, env)
                    return result
                except Exception:
                    if node.finally_body:
                        self._exec_block(node.finally_body, env)
                    raise
            if node.finally_body:
                self._exec_block(node.finally_body, env)
            raise
        except Exception as e:
            if node.catch_body:
                catch_env = Environment(env)
                error_val = HanErrorValue(str(e), "H000")
                catch_env.declare(node.catch_var, error_val)
                try:
                    result = self._exec_block(node.catch_body, catch_env)
                    if node.finally_body:
                        self._exec_block(node.finally_body, env)
                    return result
                except Exception:
                    if node.finally_body:
                        self._exec_block(node.finally_body, env)
                    raise
            if node.finally_body:
                self._exec_block(node.finally_body, env)
            raise

    def _exec_import(self, node, env):
        module_name = node.module_name
        if module_name in STDLIB_MODULES:
            module = STDLIB_MODULES[module_name]()
            env.declare(module_name, module)
            return module
        raise ImportError_(
            module_name,
            SourceLocation(self.filename, node.line, node.column)
        )

    def _exec_test(self, node, env):
        """Execute a test block and record results."""
        test_env = Environment(env)
        try:
            self._exec_block(node.body, test_env)
            self.test_results.append((node.description, True, None))
            return HanBoolean(True)
        except (HanError, RuntimeError_) as e:
            self.test_results.append((node.description, False, str(e.message)))
            return HanBoolean(False)
        except Exception as e:
            self.test_results.append((node.description, False, str(e)))
            return HanBoolean(False)

    def _exec_assert(self, node, env):
        result = self._eval_expression(node.expression, env)
        if not self._is_truthy(result):
            msg = node.message or "Assertion gagal"
            raise RuntimeError_(
                msg,
                SourceLocation(self.filename, node.line, node.column)
            )
        return HanBoolean(True)

    def _exec_explore(self, node, env):
        """jelajahi — Data explorer that displays detailed value information."""
        value = self._eval_expression(node.expression, env)
        self._display_explore(value, 0)
        return HanNull()

    def _display_explore(self, value, indent_level):
        """Display detailed information about a value."""
        indent = "  " * indent_level
        type_name = value.type_name()

        if isinstance(value, HanList):
            count = len(value.elements)
            print(f"{indent}\033[36m┌─ daftar\033[0m ({count} elemen)")
            for i, elem in enumerate(value.elements):
                prefix = "├─" if i < count - 1 else "└─"
                if isinstance(elem, (HanList, HanMap)):
                    print(f"{indent}\033[36m{prefix}\033[0m [{i}]:")
                    self._display_explore(elem, indent_level + 2)
                else:
                    print(f"{indent}\033[36m{prefix}\033[0m [{i}] "
                          f"\033[33m{elem.type_name()}\033[0m = {value_repr(elem)}")

        elif isinstance(value, HanMap):
            count = len(value.entries)
            print(f"{indent}\033[35m┌─ peta\033[0m ({count} pasangan)")
            for i, (k, v) in enumerate(value.entries.items()):
                prefix = "├─" if i < count - 1 else "└─"
                if isinstance(v, (HanList, HanMap)):
                    print(f"{indent}\033[35m{prefix}\033[0m {value_repr(k)}:")
                    self._display_explore(v, indent_level + 2)
                else:
                    print(f"{indent}\033[35m{prefix}\033[0m {value_repr(k)} = "
                          f"\033[33m{v.type_name()}\033[0m {value_repr(v)}")

        elif isinstance(value, HanFunction):
            params = ", ".join(value.params)
            print(f"{indent}\033[32m● fungsi\033[0m {value.name}({params})")

        elif isinstance(value, HanString):
            print(f"{indent}\033[33m● teks\033[0m ({len(value.value)} karakter) = "
                  f'"{value.value}"')

        elif isinstance(value, HanNumber):
            print(f"{indent}\033[33m● {type_name}\033[0m = {value.value}")

        else:
            print(f"{indent}\033[33m● {type_name}\033[0m = {value.to_display()}")

    def _exec_match(self, node, env):
        """Execute match/switch statement."""
        value = self._eval_expression(node.expression, env)

        for pattern_expr, body in node.cases:
            pattern_val = self._eval_expression(pattern_expr, env)
            if han_equals(value, pattern_val):
                return self._exec_block(body, env)

        if node.default_case:
            return self._exec_block(node.default_case, env)

        return HanNull()

    def _exec_block(self, block, env):
        """Execute a block of statements in a new scope."""
        block_env = Environment(env)
        result = HanNull()
        for stmt in block.statements:
            result = self._exec_statement(stmt, block_env)
        return result

    # ── Expression Evaluation ─────────────────────────────────────

    def _eval_expression(self, node, env):
        """Evaluate an expression node and return a HanValue."""
        if isinstance(node, NumberLiteral):
            return HanNumber(node.value)

        if isinstance(node, StringLiteral):
            return HanString(node.value)

        if isinstance(node, InterpolatedString):
            return self._eval_interpolated_string(node, env)

        if isinstance(node, BooleanLiteral):
            return HanBoolean(node.value)

        if isinstance(node, NullLiteral):
            return HanNull()

        if isinstance(node, Identifier):
            return env.get(node.name, node.line, node.column)

        if isinstance(node, BinaryOp):
            left = self._eval_expression(node.left, env)
            right = self._eval_expression(node.right, env)
            return self._binary_op(node.operator, left, right,
                                    node.line, node.column)

        if isinstance(node, UnaryOp):
            operand = self._eval_expression(node.operand, env)
            return self._unary_op(node.operator, operand,
                                   node.line, node.column)

        if isinstance(node, LogicalOp):
            return self._eval_logical(node, env)

        if isinstance(node, ComparisonOp):
            left = self._eval_expression(node.left, env)
            right = self._eval_expression(node.right, env)
            return self._comparison_op(node.operator, left, right,
                                        node.line, node.column)

        if isinstance(node, FunctionCall):
            return self._eval_call(node, env)

        if isinstance(node, MethodCall):
            return self._eval_method_call(node, env)

        if isinstance(node, IndexAccess):
            return self._eval_index_access(node, env)

        if isinstance(node, DotAccess):
            return self._eval_dot_access(node, env)

        if isinstance(node, ListLiteral):
            elements = [self._eval_expression(e, env) for e in node.elements]
            return HanList(elements)

        if isinstance(node, MapLiteral):
            m = HanMap()
            for key_node, val_node in node.pairs:
                k = self._eval_expression(key_node, env)
                v = self._eval_expression(val_node, env)
                m.entries[k] = v
            return m

        if isinstance(node, LambdaExpression):
            return HanLambda(node.params, node, env)

        if isinstance(node, PipeExpression):
            return self._eval_pipeline(node, env)

        raise RuntimeError_(
            f"Ekspresi tidak dikenal: {type(node).__name__}",
            SourceLocation(self.filename, node.line, node.column)
        )

    def _eval_interpolated_string(self, node, env):
        """Evaluate a string with embedded expressions."""
        parts = []
        for ptype, pval in node.parts:
            if ptype == "str":
                parts.append(pval)
            elif ptype == "expr":
                result = self._eval_expression(pval, env)
                parts.append(result.to_display())
        return HanString("".join(parts))

    def _eval_logical(self, node, env):
        """Evaluate logical operators with short-circuit evaluation."""
        left = self._eval_expression(node.left, env)

        if node.operator == "dan":
            if not self._is_truthy(left):
                return left
            return self._eval_expression(node.right, env)

        if node.operator == "atau":
            if self._is_truthy(left):
                return left
            return self._eval_expression(node.right, env)

        raise RuntimeError_(
            f"Operator logika tidak dikenal: {node.operator}",
            SourceLocation(self.filename, node.line, node.column)
        )

    def _eval_call(self, node, env):
        """Evaluate a function call."""
        callee = self._eval_expression(node.callee, env)
        args = [self._eval_expression(a, env) for a in node.arguments]

        if isinstance(callee, HanBuiltinFunction):
            try:
                return callee.func(args)
            except HanError:
                raise
            except (TypeError, ValueError, ZeroDivisionError) as e:
                raise RuntimeError_(
                    str(e),
                    SourceLocation(self.filename, node.line, node.column)
                )

        if isinstance(callee, HanFunction):
            return self._call_function(callee, args, node.line, node.column)

        if isinstance(callee, HanLambda):
            return self._call_lambda(callee, args, node.line, node.column)

        raise RuntimeError_(
            f"'{callee.to_display()}' bukan fungsi yang bisa dipanggil",
            SourceLocation(self.filename, node.line, node.column)
        )

    def _call_function(self, func, args, line, column):
        """Call a user-defined function."""
        if len(args) != len(func.params):
            raise ArgumentError(
                func.name, len(func.params), len(args),
                SourceLocation(self.filename, line, column)
            )

        self.call_depth += 1
        if self.call_depth > self.MAX_RECURSION:
            self.call_depth -= 1
            raise RecursionLimitError(
                SourceLocation(self.filename, line, column)
            )

        try:
            func_env = Environment(func.closure_env)
            for param, arg in zip(func.params, args):
                func_env.declare(param, arg)

            try:
                result = HanNull()
                for stmt in func.body.statements:
                    result = self._exec_statement(stmt, func_env)
                return result
            except ReturnSignal as ret:
                return ret.value
        finally:
            self.call_depth -= 1

    def _call_lambda(self, lam, args, line, column):
        """Call a lambda function."""
        if len(args) != len(lam.params):
            raise ArgumentError(
                "<lambda>", len(lam.params), len(args),
                SourceLocation(self.filename, line, column)
            )

        self.call_depth += 1
        if self.call_depth > self.MAX_RECURSION:
            self.call_depth -= 1
            raise RecursionLimitError(
                SourceLocation(self.filename, line, column)
            )

        try:
            lam_env = Environment(lam.closure_env)
            for param, arg in zip(lam.params, args):
                lam_env.declare(param, arg)

            # Lambda body is a LambdaExpression node — evaluate its body
            return self._eval_expression(lam.body.body, lam_env)
        finally:
            self.call_depth -= 1

    def _eval_method_call(self, node, env):
        """Evaluate a method call: obj.method(args)"""
        obj = self._eval_expression(node.object, env)
        args = [self._eval_expression(a, env) for a in node.arguments]

        # Module method
        if isinstance(obj, HanModule):
            if node.method in obj.members:
                member = obj.members[node.method]
                if isinstance(member, HanBuiltinFunction):
                    try:
                        return member.func(args)
                    except HanError:
                        raise
                    except Exception as e:
                        raise RuntimeError_(
                            str(e),
                            SourceLocation(self.filename, node.line, node.column)
                        )
                return member
            raise RuntimeError_(
                f"Modul '{obj.name}' tidak memiliki '{node.method}'",
                SourceLocation(self.filename, node.line, node.column)
            )

        # String methods
        if isinstance(obj, HanString):
            return self._string_method(obj, node.method, args, node.line, node.column)

        # List methods
        if isinstance(obj, HanList):
            return self._list_method(obj, node.method, args, node.line, node.column)

        # Map methods
        if isinstance(obj, HanMap):
            return self._map_method(obj, node.method, args, node.line, node.column)

        # Error value methods
        if isinstance(obj, HanErrorValue):
            if node.method == "pesan" or node.method == "to_display":
                return HanString(obj.message)
            raise RuntimeError_(
                f"Error tidak memiliki metode '{node.method}'",
                SourceLocation(self.filename, node.line, node.column)
            )

        raise RuntimeError_(
            f"Tipe {obj.type_name()} tidak memiliki metode '{node.method}'",
            SourceLocation(self.filename, node.line, node.column)
        )

    def _string_method(self, s, method, args, line, column):
        """Handle string methods."""
        methods = {
            "panjang": lambda: HanNumber(len(s.value)),
            "huruf_besar": lambda: HanString(s.value.upper()),
            "huruf_kecil": lambda: HanString(s.value.lower()),
            "potong": lambda: HanString(s.value.strip()),
            "pisah": lambda: HanList([
                HanString(p) for p in s.value.split(
                    args[0].value if args and isinstance(args[0], HanString) else " "
                )
            ]),
            "berisi": lambda: HanBoolean(
                args[0].value in s.value if args and isinstance(args[0], HanString) else False
            ),
            "ganti": lambda: HanString(
                s.value.replace(args[0].value, args[1].value)
            ) if len(args) >= 2 else HanString(s.value),
            "awalan": lambda: HanBoolean(
                s.value.startswith(args[0].value) if args else False
            ),
            "akhiran": lambda: HanBoolean(
                s.value.endswith(args[0].value) if args else False
            ),
            "indeks": lambda: HanNumber(
                s.value.find(args[0].value) if args and isinstance(args[0], HanString) else -1
            ),
        }
        if method in methods:
            return methods[method]()
        raise RuntimeError_(
            f"Teks tidak memiliki metode '{method}'",
            SourceLocation(self.filename, line, column)
        )

    def _list_method(self, lst, method, args, line, column):
        """Handle list methods."""
        if method == "tambah":
            if args:
                lst.elements.append(args[0])
            return lst
        if method == "hapus":
            if args and isinstance(args[0], HanNumber):
                idx = int(args[0].value)
                if 0 <= idx < len(lst.elements):
                    return lst.elements.pop(idx)
                raise IndexOutOfRangeError(idx, len(lst.elements),
                                            SourceLocation(self.filename, line, column))
            raise RuntimeError_("Metode 'hapus' membutuhkan indeks bertipe bilangan")
        if method == "panjang":
            return HanNumber(len(lst.elements))
        if method == "berisi":
            for elem in lst.elements:
                if han_equals(elem, args[0]):
                    return HanBoolean(True)
            return HanBoolean(False)
        if method == "gabung":
            sep = args[0].value if args and isinstance(args[0], HanString) else ", "
            return HanString(sep.join(e.to_display() for e in lst.elements))
        if method == "balik":
            return HanList(list(reversed(lst.elements)))
        if method == "urutkan":
            try:
                elements = sorted(lst.elements,
                                  key=lambda x: x.value if isinstance(x, (HanNumber, HanString)) else x.to_display())
                return HanList(elements)
            except TypeError:
                raise RuntimeError_("Tidak bisa mengurutkan daftar dengan tipe campuran")
        if method == "iris":
            start = int(args[0].value) if args else 0
            end = int(args[1].value) if len(args) > 1 else len(lst.elements)
            return HanList(lst.elements[start:end])
        if method == "kosong":
            return HanBoolean(len(lst.elements) == 0)

        raise RuntimeError_(
            f"Daftar tidak memiliki metode '{method}'",
            SourceLocation(self.filename, line, column)
        )

    def _map_method(self, m, method, args, line, column):
        """Handle map methods."""
        if method == "kunci":
            return HanList(list(m.entries.keys()))
        if method == "nilai":
            return HanList(list(m.entries.values()))
        if method == "berisi":
            return HanBoolean(args[0] in m.entries if args else False)
        if method == "hapus":
            if args and args[0] in m.entries:
                return m.entries.pop(args[0])
            raise KeyNotFoundError(
                args[0].to_display() if args else "???",
                SourceLocation(self.filename, line, column)
            )
        if method == "panjang":
            return HanNumber(len(m.entries))

        raise RuntimeError_(
            f"Peta tidak memiliki metode '{method}'",
            SourceLocation(self.filename, line, column)
        )

    def _eval_index_access(self, node, env):
        """Evaluate obj[index]."""
        obj = self._eval_expression(node.object, env)
        index = self._eval_expression(node.index, env)

        if isinstance(obj, HanList):
            if not isinstance(index, HanNumber):
                raise RuntimeError_(
                    "Indeks daftar harus berupa bilangan",
                    SourceLocation(self.filename, node.line, node.column)
                )
            idx = int(index.value)
            if 0 <= idx < len(obj.elements):
                return obj.elements[idx]
            raise IndexOutOfRangeError(
                idx, len(obj.elements),
                SourceLocation(self.filename, node.line, node.column)
            )

        if isinstance(obj, HanString):
            if not isinstance(index, HanNumber):
                raise RuntimeError_(
                    "Indeks teks harus berupa bilangan",
                    SourceLocation(self.filename, node.line, node.column)
                )
            idx = int(index.value)
            if 0 <= idx < len(obj.value):
                return HanString(obj.value[idx])
            raise IndexOutOfRangeError(
                idx, len(obj.value),
                SourceLocation(self.filename, node.line, node.column)
            )

        if isinstance(obj, HanMap):
            if index in obj.entries:
                return obj.entries[index]
            raise KeyNotFoundError(
                index.to_display(),
                SourceLocation(self.filename, node.line, node.column)
            )

        raise RuntimeError_(
            f"Tidak bisa mengindeks tipe {obj.type_name()}",
            SourceLocation(self.filename, node.line, node.column)
        )

    def _eval_dot_access(self, node, env):
        """Evaluate obj.attribute."""
        obj = self._eval_expression(node.object, env)

        # Module attribute
        if isinstance(obj, HanModule):
            if node.attribute in obj.members:
                return obj.members[node.attribute]
            raise RuntimeError_(
                f"Modul '{obj.name}' tidak memiliki '{node.attribute}'",
                SourceLocation(self.filename, node.line, node.column)
            )

        # Map attribute (sugar for map[key])
        if isinstance(obj, HanMap):
            key = HanString(node.attribute)
            if key in obj.entries:
                return obj.entries[key]
            raise KeyNotFoundError(
                node.attribute,
                SourceLocation(self.filename, node.line, node.column)
            )

        # Error .pesan
        if isinstance(obj, HanErrorValue):
            if node.attribute == "pesan":
                return HanString(obj.message)
            if node.attribute == "kode":
                return HanString(obj.code)

        # String .panjang
        if isinstance(obj, HanString) and node.attribute == "panjang":
            return HanNumber(len(obj.value))

        # List .panjang
        if isinstance(obj, HanList) and node.attribute == "panjang":
            return HanNumber(len(obj.elements))

        raise RuntimeError_(
            f"Tipe {obj.type_name()} tidak memiliki atribut '{node.attribute}'",
            SourceLocation(self.filename, node.line, node.column)
        )

    def _eval_pipeline(self, node, env):
        """Evaluate pipeline: value |> function"""
        value = self._eval_expression(node.value, env)
        func_node = node.function

        # Handle: value |> func(args) — inject value as first argument
        if isinstance(func_node, FunctionCall):
            callee = self._eval_expression(func_node.callee, env)
            args = [value] + [self._eval_expression(a, env) for a in func_node.arguments]

            if isinstance(callee, HanBuiltinFunction):
                # Special handling for saring/ubah with lambdas
                if callee.name in ("saring", "ubah"):
                    return self._pipeline_filter_map(callee.name, args, env,
                                                     node.line, node.column)
                try:
                    return callee.func(args)
                except HanError:
                    raise
            if isinstance(callee, HanFunction):
                return self._call_function(callee, args, node.line, node.column)
            if isinstance(callee, HanLambda):
                return self._call_lambda(callee, args, node.line, node.column)

        # Handle: value |> identifier (call with value as sole arg)
        if isinstance(func_node, Identifier):
            callee = env.get(func_node.name, func_node.line, func_node.column)
            if isinstance(callee, HanBuiltinFunction):
                try:
                    return callee.func([value])
                except HanError:
                    raise
            if isinstance(callee, HanFunction):
                return self._call_function(callee, [value], node.line, node.column)
            if isinstance(callee, HanLambda):
                return self._call_lambda(callee, [value], node.line, node.column)

        # Evaluate as expression and try to call
        callee = self._eval_expression(func_node, env)
        if isinstance(callee, (HanFunction, HanLambda, HanBuiltinFunction)):
            if isinstance(callee, HanBuiltinFunction):
                return callee.func([value])
            if isinstance(callee, HanFunction):
                return self._call_function(callee, [value], node.line, node.column)
            return self._call_lambda(callee, [value], node.line, node.column)

        raise RuntimeError_(
            "Pipeline membutuhkan fungsi di sisi kanan",
            SourceLocation(self.filename, node.line, node.column)
        )

    def _pipeline_filter_map(self, op_name, args, env, line, column):
        """Handle saring/ubah with proper lambda execution."""
        if len(args) < 2:
            raise ArgumentError(op_name, 2, len(args),
                                SourceLocation(self.filename, line, column))

        lst = args[0]
        func = args[1]

        if not isinstance(lst, HanList):
            raise RuntimeError_(
                f"'{op_name}' membutuhkan daftar sebagai argumen pertama",
                SourceLocation(self.filename, line, column)
            )

        result = []
        for elem in lst.elements:
            if isinstance(func, HanLambda):
                val = self._call_lambda(func, [elem], line, column)
            elif isinstance(func, HanFunction):
                val = self._call_function(func, [elem], line, column)
            elif isinstance(func, HanBuiltinFunction):
                val = func.func([elem])
            else:
                raise RuntimeError_(
                    f"'{op_name}' membutuhkan fungsi sebagai argumen kedua",
                    SourceLocation(self.filename, line, column)
                )

            if op_name == "saring":
                if self._is_truthy(val):
                    result.append(elem)
            else:  # ubah
                result.append(val)

        return HanList(result)

    # ── Operators ─────────────────────────────────────────────────

    def _binary_op(self, op, left, right, line, column):
        """Execute a binary operation."""
        loc = SourceLocation(self.filename, line, column)

        # String concatenation
        if op == "+" and isinstance(left, HanString):
            return HanString(left.value + right.to_display())

        if op == "+" and isinstance(right, HanString):
            return HanString(left.to_display() + right.value)

        # String repetition
        if op == "*" and isinstance(left, HanString) and isinstance(right, HanNumber):
            return HanString(left.value * int(right.value))

        # List concatenation
        if op == "+" and isinstance(left, HanList) and isinstance(right, HanList):
            return HanList(left.elements + right.elements)

        # Number arithmetic
        if isinstance(left, HanNumber) and isinstance(right, HanNumber):
            a, b = left.value, right.value
            if op == "+":
                return HanNumber(a + b)
            if op == "-":
                return HanNumber(a - b)
            if op == "*":
                return HanNumber(a * b)
            if op == "/":
                if b == 0:
                    raise DivisionByZeroError(loc)
                return HanNumber(a / b)
            if op == "//":
                if b == 0:
                    raise DivisionByZeroError(loc)
                return HanNumber(a // b)
            if op == "%":
                if b == 0:
                    raise DivisionByZeroError(loc)
                return HanNumber(a % b)
            if op == "**":
                if isinstance(b, (int, float)) and abs(b) > 1000:
                    raise RuntimeError_(
                        "Nilai pangkat terlalu besar (maks 1000)",
                        loc
                    )
                return HanNumber(a ** b)

        raise TypeMismatchError(
            op, left.type_name(), right.type_name(), loc
        )

    def _unary_op(self, op, operand, line, column):
        """Execute a unary operation."""
        if op == "-":
            if isinstance(operand, HanNumber):
                return HanNumber(-operand.value)
            raise TypeMismatchError(
                "-", operand.type_name(), "",
                SourceLocation(self.filename, line, column)
            )

        if op == "+":
            if isinstance(operand, HanNumber):
                return operand
            raise TypeMismatchError(
                "+", operand.type_name(), "",
                SourceLocation(self.filename, line, column)
            )

        if op == "bukan":
            return HanBoolean(not self._is_truthy(operand))

        raise RuntimeError_(
            f"Operator unary tidak dikenal: {op}",
            SourceLocation(self.filename, line, column)
        )

    def _comparison_op(self, op, left, right, line, column):
        """Execute a comparison operation."""
        if op == "==":
            return HanBoolean(han_equals(left, right))
        if op == "!=":
            return HanBoolean(not han_equals(left, right))

        # Numeric comparisons
        if isinstance(left, HanNumber) and isinstance(right, HanNumber):
            a, b = left.value, right.value
            if op == "<":
                return HanBoolean(a < b)
            if op == ">":
                return HanBoolean(a > b)
            if op == "<=":
                return HanBoolean(a <= b)
            if op == ">=":
                return HanBoolean(a >= b)

        # String comparisons
        if isinstance(left, HanString) and isinstance(right, HanString):
            a, b = left.value, right.value
            if op == "<":
                return HanBoolean(a < b)
            if op == ">":
                return HanBoolean(a > b)
            if op == "<=":
                return HanBoolean(a <= b)
            if op == ">=":
                return HanBoolean(a >= b)

        raise TypeMismatchError(
            op, left.type_name(), right.type_name(),
            SourceLocation(self.filename, line, column)
        )

    def _is_truthy(self, value):
        """Determine if a value is truthy."""
        if isinstance(value, HanValue):
            return value.to_boolean()
        return bool(value)

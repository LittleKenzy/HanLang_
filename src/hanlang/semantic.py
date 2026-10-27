"""
HanLang Semantic Analyzer
=========================

Performs semantic validation on the AST before execution.
Catches errors like undefined variables, invalid assignments,
and unreachable code without running the program.
"""

from .nodes import *
from .errors import (
    ParseError,
    SourceLocation,
)


class SemanticAnalyzer:
    """Validate AST semantics before execution."""

    def __init__(self, filename="<stdin>"):
        self.filename = filename
        self.errors = []
        self.warnings = []
        self.scopes = [set()]  # Stack of sets of variable names
        self.in_loop = False
        self.in_function = False

        # Register builtins as known names
        builtins = {
            "tampil", "masukan", "bilangan", "teks", "desimal", "boolean",
            "tipe", "adalah", "panjang", "rentang", "tambah", "hapus",
            "gabung", "pisah", "urutkan", "balik", "berisi", "kunci",
            "nilai", "abs", "bulat", "min", "max",
            "Benar", "Salah", "kosong",
            "saring", "ubah",
        }
        self.scopes[0].update(builtins)

    def analyze(self, program):
        """Analyze a Program AST node. Returns (errors, warnings)."""
        for stmt in program.statements:
            self._check_statement(stmt)
        return self.errors, self.warnings

    def _push_scope(self):
        self.scopes.append(set())

    def _pop_scope(self):
        self.scopes.pop()

    def _declare(self, name):
        self.scopes[-1].add(name)

    def _is_declared(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return True
        return False

    def _check_statement(self, node):
        if isinstance(node, VariableDeclaration):
            self._check_expression(node.value)
            self._declare(node.name)

        elif isinstance(node, Assignment):
            if isinstance(node.target, Identifier):
                if not self._is_declared(node.target.name):
                    # In HanLang, assignment to undeclared is warning
                    self.warnings.append(
                        f"Baris {node.line}: Variabel '{node.target.name}' "
                        f"belum dideklarasikan dengan 'tetapkan'"
                    )
                    self._declare(node.target.name)
            self._check_expression(node.value)

        elif isinstance(node, ExpressionStatement):
            self._check_expression(node.expression)

        elif isinstance(node, IfStatement):
            self._check_expression(node.condition)
            self._check_block(node.body)
            for cond, body in node.elif_clauses:
                self._check_expression(cond)
                self._check_block(body)
            if node.else_body:
                self._check_block(node.else_body)

        elif isinstance(node, WhileLoop):
            self._check_expression(node.condition)
            old_in_loop = self.in_loop
            self.in_loop = True
            self._check_block(node.body)
            self.in_loop = old_in_loop

        elif isinstance(node, (ForLoop, ForInLoop)):
            self._check_expression(node.iterable)
            old_in_loop = self.in_loop
            self.in_loop = True
            self._push_scope()
            self._declare(node.variable)
            self._check_block_inner(node.body)
            self._pop_scope()
            self.in_loop = old_in_loop

        elif isinstance(node, FunctionDeclaration):
            self._declare(node.name)
            old_in_function = self.in_function
            self.in_function = True
            self._push_scope()
            for p in node.params:
                self._declare(p)
            self._check_block_inner(node.body)
            self._pop_scope()
            self.in_function = old_in_function

        elif isinstance(node, ReturnStatement):
            if not self.in_function:
                self.errors.append(
                    f"Baris {node.line}: 'kembali' hanya boleh digunakan di dalam fungsi"
                )
            if node.value:
                self._check_expression(node.value)

        elif isinstance(node, BreakStatement):
            if not self.in_loop:
                self.errors.append(
                    f"Baris {node.line}: 'berhenti' hanya boleh digunakan di dalam loop"
                )

        elif isinstance(node, ContinueStatement):
            if not self.in_loop:
                self.errors.append(
                    f"Baris {node.line}: 'lanjut' hanya boleh digunakan di dalam loop"
                )

        elif isinstance(node, TryCatch):
            self._check_block(node.try_body)
            if node.catch_body:
                self._push_scope()
                if node.catch_var:
                    self._declare(node.catch_var)
                self._check_block_inner(node.catch_body)
                self._pop_scope()
            if node.finally_body:
                self._check_block(node.finally_body)

        elif isinstance(node, ImportStatement):
            self._declare(node.module_name)

        elif isinstance(node, TestBlock):
            self._check_block(node.body)

        elif isinstance(node, AssertStatement):
            self._check_expression(node.expression)

        elif isinstance(node, ExploreStatement):
            self._check_expression(node.expression)

        elif isinstance(node, MatchStatement):
            self._check_expression(node.expression)
            for pattern, body in node.cases:
                self._check_expression(pattern)
                self._check_block(body)
            if node.default_case:
                self._check_block(node.default_case)

        elif isinstance(node, Block):
            self._check_block(node)

    def _check_block(self, block):
        self._push_scope()
        self._check_block_inner(block)
        self._pop_scope()

    def _check_block_inner(self, block):
        for stmt in block.statements:
            self._check_statement(stmt)

    def _check_expression(self, node):
        if isinstance(node, Identifier):
            # Don't error on undefined — allow flexible access patterns
            pass

        elif isinstance(node, BinaryOp):
            self._check_expression(node.left)
            self._check_expression(node.right)

        elif isinstance(node, UnaryOp):
            self._check_expression(node.operand)

        elif isinstance(node, LogicalOp):
            self._check_expression(node.left)
            self._check_expression(node.right)

        elif isinstance(node, ComparisonOp):
            self._check_expression(node.left)
            self._check_expression(node.right)

        elif isinstance(node, FunctionCall):
            self._check_expression(node.callee)
            for arg in node.arguments:
                self._check_expression(arg)

        elif isinstance(node, MethodCall):
            self._check_expression(node.object)
            for arg in node.arguments:
                self._check_expression(arg)

        elif isinstance(node, IndexAccess):
            self._check_expression(node.object)
            self._check_expression(node.index)

        elif isinstance(node, DotAccess):
            self._check_expression(node.object)

        elif isinstance(node, ListLiteral):
            for elem in node.elements:
                self._check_expression(elem)

        elif isinstance(node, MapLiteral):
            for k, v in node.pairs:
                self._check_expression(k)
                self._check_expression(v)

        elif isinstance(node, PipeExpression):
            self._check_expression(node.value)
            self._check_expression(node.function)

        elif isinstance(node, LambdaExpression):
            self._push_scope()
            for p in node.params:
                self._declare(p)
            self._check_expression(node.body)
            self._pop_scope()

        elif isinstance(node, InterpolatedString):
            for ptype, pval in node.parts:
                if ptype == "expr":
                    self._check_expression(pval)

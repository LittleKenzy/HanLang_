"""
HanLang AST Node Definitions
=============================

All Abstract Syntax Tree node types used by the HanLang parser.
Each node stores source location information for error reporting.
"""


class ASTNode:
    """Base class for all AST nodes."""

    def __init__(self, line=0, column=0):
        self.line = line
        self.column = column


# ── Program ───────────────────────────────────────────────────────

class Program(ASTNode):
    """Root node: a sequence of statements."""
    def __init__(self, statements, line=0, column=0):
        super().__init__(line, column)
        self.statements = statements


# ── Literals ──────────────────────────────────────────────────────

class NumberLiteral(ASTNode):
    def __init__(self, value, line=0, column=0):
        super().__init__(line, column)
        self.value = value


class StringLiteral(ASTNode):
    """Plain string literal (no interpolation)."""
    def __init__(self, value, line=0, column=0):
        super().__init__(line, column)
        self.value = value


class InterpolatedString(ASTNode):
    """String with {expression} interpolation."""
    def __init__(self, parts, line=0, column=0):
        super().__init__(line, column)
        self.parts = parts  # list of (type, value/node)


class BooleanLiteral(ASTNode):
    def __init__(self, value, line=0, column=0):
        super().__init__(line, column)
        self.value = value


class NullLiteral(ASTNode):
    def __init__(self, line=0, column=0):
        super().__init__(line, column)
        self.value = None


class ListLiteral(ASTNode):
    def __init__(self, elements, line=0, column=0):
        super().__init__(line, column)
        self.elements = elements


class MapLiteral(ASTNode):
    def __init__(self, pairs, line=0, column=0):
        super().__init__(line, column)
        self.pairs = pairs  # list of (key_node, value_node)


# ── Expressions ───────────────────────────────────────────────────

class Identifier(ASTNode):
    def __init__(self, name, line=0, column=0):
        super().__init__(line, column)
        self.name = name


class BinaryOp(ASTNode):
    def __init__(self, operator, left, right, line=0, column=0):
        super().__init__(line, column)
        self.operator = operator
        self.left = left
        self.right = right


class UnaryOp(ASTNode):
    def __init__(self, operator, operand, line=0, column=0):
        super().__init__(line, column)
        self.operator = operator
        self.operand = operand


class LogicalOp(ASTNode):
    def __init__(self, operator, left, right, line=0, column=0):
        super().__init__(line, column)
        self.operator = operator  # "dan" or "atau"
        self.left = left
        self.right = right


class ComparisonOp(ASTNode):
    def __init__(self, operator, left, right, line=0, column=0):
        super().__init__(line, column)
        self.operator = operator
        self.left = left
        self.right = right


class FunctionCall(ASTNode):
    def __init__(self, callee, arguments, line=0, column=0):
        super().__init__(line, column)
        self.callee = callee
        self.arguments = arguments


class MethodCall(ASTNode):
    def __init__(self, object, method, arguments, line=0, column=0):
        super().__init__(line, column)
        self.object = object
        self.method = method
        self.arguments = arguments


class IndexAccess(ASTNode):
    def __init__(self, object, index, line=0, column=0):
        super().__init__(line, column)
        self.object = object
        self.index = index


class DotAccess(ASTNode):
    def __init__(self, object, attribute, line=0, column=0):
        super().__init__(line, column)
        self.object = object
        self.attribute = attribute


class PipeExpression(ASTNode):
    """Pipeline expression: value |> func"""
    def __init__(self, value, function, line=0, column=0):
        super().__init__(line, column)
        self.value = value
        self.function = function


class LambdaExpression(ASTNode):
    """Anonymous function: (params) => expression or param => expression"""
    def __init__(self, params, body, line=0, column=0):
        super().__init__(line, column)
        self.params = params
        self.body = body


class AssignmentExpr(ASTNode):
    """Assignment as expression for compound assignments."""
    def __init__(self, target, operator, value, line=0, column=0):
        super().__init__(line, column)
        self.target = target
        self.operator = operator
        self.value = value


# ── Statements ────────────────────────────────────────────────────

class VariableDeclaration(ASTNode):
    def __init__(self, name, value, is_constant=False, line=0, column=0):
        super().__init__(line, column)
        self.name = name
        self.value = value
        self.is_constant = is_constant


class Assignment(ASTNode):
    def __init__(self, target, value, operator="=", line=0, column=0):
        super().__init__(line, column)
        self.target = target  # Identifier, IndexAccess, or DotAccess
        self.value = value
        self.operator = operator


class ExpressionStatement(ASTNode):
    def __init__(self, expression, line=0, column=0):
        super().__init__(line, column)
        self.expression = expression


class Block(ASTNode):
    def __init__(self, statements, line=0, column=0):
        super().__init__(line, column)
        self.statements = statements


class IfStatement(ASTNode):
    def __init__(self, condition, body, elif_clauses=None, else_body=None,
                 line=0, column=0):
        super().__init__(line, column)
        self.condition = condition
        self.body = body
        self.elif_clauses = elif_clauses or []  # list of (condition, body)
        self.else_body = else_body


class WhileLoop(ASTNode):
    """ulangi selama <condition> { ... }"""
    def __init__(self, condition, body, line=0, column=0):
        super().__init__(line, column)
        self.condition = condition
        self.body = body


class ForLoop(ASTNode):
    """ulangi untuk <var> dalam <iterable> { ... }"""
    def __init__(self, variable, iterable, body, line=0, column=0):
        super().__init__(line, column)
        self.variable = variable
        self.iterable = iterable
        self.body = body


class ForInLoop(ASTNode):
    """untuk <var> dalam <iterable> { ... }"""
    def __init__(self, variable, iterable, body, line=0, column=0):
        super().__init__(line, column)
        self.variable = variable
        self.iterable = iterable
        self.body = body


class FunctionDeclaration(ASTNode):
    def __init__(self, name, params, body, line=0, column=0):
        super().__init__(line, column)
        self.name = name
        self.params = params  # list of parameter names
        self.body = body


class ReturnStatement(ASTNode):
    def __init__(self, value=None, line=0, column=0):
        super().__init__(line, column)
        self.value = value


class BreakStatement(ASTNode):
    def __init__(self, line=0, column=0):
        super().__init__(line, column)


class ContinueStatement(ASTNode):
    def __init__(self, line=0, column=0):
        super().__init__(line, column)


class TryCatch(ASTNode):
    def __init__(self, try_body, catch_var=None, catch_body=None,
                 finally_body=None, line=0, column=0):
        super().__init__(line, column)
        self.try_body = try_body
        self.catch_var = catch_var
        self.catch_body = catch_body
        self.finally_body = finally_body


class ImportStatement(ASTNode):
    def __init__(self, module_name, names=None, line=0, column=0):
        super().__init__(line, column)
        self.module_name = module_name
        self.names = names  # None means import whole module


class TestBlock(ASTNode):
    """uji "description" { ... }"""
    def __init__(self, description, body, line=0, column=0):
        super().__init__(line, column)
        self.description = description
        self.body = body


class AssertStatement(ASTNode):
    """pastikan <expression>"""
    def __init__(self, expression, message=None, line=0, column=0):
        super().__init__(line, column)
        self.expression = expression
        self.message = message


class ExploreStatement(ASTNode):
    """jelajahi <expression>"""
    def __init__(self, expression, line=0, column=0):
        super().__init__(line, column)
        self.expression = expression


class MatchStatement(ASTNode):
    """cocokkan <expression> { pola <value> { ... } lainnya { ... } }"""
    def __init__(self, expression, cases, default_case=None, line=0, column=0):
        super().__init__(line, column)
        self.expression = expression
        self.cases = cases  # list of (pattern_expr, body)
        self.default_case = default_case

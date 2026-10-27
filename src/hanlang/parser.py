"""
HanLang Parser
==============

Recursive-descent parser that converts a token stream into an Abstract
Syntax Tree. Supports full operator precedence, nested blocks, function
definitions, control flow, collections, pipelines, and all HanLang constructs.
"""

from .tokens import TokenType
from .nodes import *
from .errors import (
    ParseError,
    UnexpectedTokenError,
    MissingTokenError,
    SourceLocation,
)


class Parser:
    """Recursive-descent parser for HanLang."""

    def __init__(self, tokens, filename="<stdin>", source=""):
        self.tokens = tokens
        self.filename = filename
        self.source = source
        self.pos = 0

    def _current(self):
        """Get the current token."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # EOF

    def _peek(self, offset=1):
        """Look ahead at a token."""
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def _at(self, *types):
        """Check if current token is one of the given types."""
        return self._current().type in types

    def _advance(self):
        """Consume and return the current token."""
        token = self._current()
        self.pos += 1
        return token

    def _expect(self, type, description=None):
        """Consume the current token if it matches, otherwise raise an error."""
        tok = self._current()
        if tok.type != type:
            desc = description or type.name
            loc = SourceLocation(self.filename, tok.line, tok.column, tok.length)
            raise UnexpectedTokenError(desc, tok.value, loc)
        return self._advance()

    def _skip_newlines(self):
        """Skip newline tokens."""
        while self._at(TokenType.NEWLINE):
            self._advance()

    def _at_statement_end(self):
        """Check if we're at a statement boundary."""
        return self._at(TokenType.NEWLINE, TokenType.EOF, TokenType.RBRACE,
                        TokenType.SEMICOLON)

    def _consume_statement_end(self):
        """Consume statement terminators (newlines or semicolons)."""
        while self._at(TokenType.NEWLINE, TokenType.SEMICOLON):
            self._advance()

    # ── Top-level Parsing ─────────────────────────────────────────

    def parse(self):
        """Parse all tokens into a Program AST node."""
        self._skip_newlines()
        statements = []

        while not self._at(TokenType.EOF):
            stmt = self._parse_statement()
            if stmt is not None:
                statements.append(stmt)
            self._consume_statement_end()
            self._skip_newlines()

        return Program(statements, line=1, column=1)

    # ── Statement Parsing ─────────────────────────────────────────

    def _parse_statement(self):
        """Parse a single statement."""
        self._skip_newlines()
        tok = self._current()

        if tok.type == TokenType.TETAPKAN:
            return self._parse_variable_declaration(is_constant=False)

        if tok.type == TokenType.KONSTAN:
            return self._parse_variable_declaration(is_constant=True)

        if tok.type == TokenType.JIKA:
            return self._parse_if_statement()

        if tok.type == TokenType.ULANGI:
            return self._parse_loop()

        if tok.type == TokenType.UNTUK:
            return self._parse_for_in_loop()

        if tok.type == TokenType.FUNGSI:
            return self._parse_function_declaration()

        if tok.type == TokenType.KEMBALI:
            return self._parse_return_statement()

        if tok.type == TokenType.BERHENTI:
            self._advance()
            return BreakStatement(line=tok.line, column=tok.column)

        if tok.type == TokenType.LANJUT:
            self._advance()
            return ContinueStatement(line=tok.line, column=tok.column)

        if tok.type == TokenType.COBA:
            return self._parse_try_catch()

        if tok.type == TokenType.IMPOR:
            return self._parse_import()

        if tok.type == TokenType.UJI:
            return self._parse_test_block()

        if tok.type == TokenType.PASTIKAN:
            return self._parse_assert()

        if tok.type == TokenType.JELAJAHI:
            return self._parse_explore()

        if tok.type == TokenType.COCOKKAN:
            return self._parse_match()

        # Assignment or expression statement
        return self._parse_assignment_or_expression()

    def _parse_variable_declaration(self, is_constant=False):
        """Parse: tetapkan <name> = <value> or konstan <name> = <value>"""
        tok = self._advance()  # consume tetapkan/konstan
        name_tok = self._expect(TokenType.IDENTIFIER, "nama variabel")
        self._expect(TokenType.ASSIGN, "'='")
        value = self._parse_expression()
        return VariableDeclaration(
            name_tok.value, value, is_constant,
            line=tok.line, column=tok.column
        )

    def _parse_if_statement(self):
        """Parse: jika <cond> { ... } jika_tidak_jika <cond> { ... } jika_tidak { ... }"""
        tok = self._advance()  # consume jika
        condition = self._parse_expression()
        self._skip_newlines()
        body = self._parse_block()

        elif_clauses = []
        else_body = None

        while True:
            self._skip_newlines()
            if self._at(TokenType.JIKA_TIDAK_JIKA):
                self._advance()
                elif_cond = self._parse_expression()
                self._skip_newlines()
                elif_body = self._parse_block()
                elif_clauses.append((elif_cond, elif_body))
            elif self._at(TokenType.JIKA_TIDAK):
                self._advance()
                self._skip_newlines()
                else_body = self._parse_block()
                break
            else:
                break

        return IfStatement(
            condition, body, elif_clauses, else_body,
            line=tok.line, column=tok.column
        )

    def _parse_loop(self):
        """Parse ulangi loops: 'ulangi untuk' or 'ulangi selama'."""
        tok = self._advance()  # consume ulangi

        if self._at(TokenType.UNTUK):
            return self._parse_ulangi_for(tok)
        elif self._at(TokenType.SELAMA):
            return self._parse_ulangi_while(tok)
        else:
            loc = SourceLocation(self.filename, tok.line, tok.column)
            raise ParseError(
                "Setelah 'ulangi' harus ada 'untuk' atau 'selama'",
                loc,
                help_text="Contoh: ulangi untuk x dalam rentang(1, 10) { ... }"
            )

    def _parse_ulangi_for(self, ulangi_tok):
        """Parse: ulangi untuk <var> dalam <iterable> { ... }"""
        self._advance()  # consume untuk
        var_tok = self._expect(TokenType.IDENTIFIER, "nama variabel")
        self._expect(TokenType.DALAM, "'dalam'")
        iterable = self._parse_expression()
        self._skip_newlines()
        body = self._parse_block()
        return ForLoop(
            var_tok.value, iterable, body,
            line=ulangi_tok.line, column=ulangi_tok.column
        )

    def _parse_ulangi_while(self, ulangi_tok):
        """Parse: ulangi selama <condition> { ... }"""
        self._advance()  # consume selama
        condition = self._parse_expression()
        self._skip_newlines()
        body = self._parse_block()
        return WhileLoop(
            condition, body,
            line=ulangi_tok.line, column=ulangi_tok.column
        )

    def _parse_for_in_loop(self):
        """Parse: untuk <var> dalam <iterable> { ... }"""
        tok = self._advance()  # consume untuk
        var_tok = self._expect(TokenType.IDENTIFIER, "nama variabel")
        self._expect(TokenType.DALAM, "'dalam'")
        iterable = self._parse_expression()
        self._skip_newlines()
        body = self._parse_block()
        return ForInLoop(
            var_tok.value, iterable, body,
            line=tok.line, column=tok.column
        )

    def _parse_function_declaration(self):
        """Parse: fungsi <name>(<params>) { ... }"""
        tok = self._advance()  # consume fungsi
        name_tok = self._expect(TokenType.IDENTIFIER, "nama fungsi")
        self._expect(TokenType.LPAREN, "'('")

        params = []
        if not self._at(TokenType.RPAREN):
            params.append(self._expect(TokenType.IDENTIFIER, "nama parameter").value)
            while self._at(TokenType.COMMA):
                self._advance()
                params.append(
                    self._expect(TokenType.IDENTIFIER, "nama parameter").value
                )

        self._expect(TokenType.RPAREN, "')'")
        self._skip_newlines()
        body = self._parse_block()

        return FunctionDeclaration(
            name_tok.value, params, body,
            line=tok.line, column=tok.column
        )

    def _parse_return_statement(self):
        """Parse: kembali [<expression>]"""
        tok = self._advance()  # consume kembali
        value = None
        if not self._at_statement_end():
            value = self._parse_expression()
        return ReturnStatement(value, line=tok.line, column=tok.column)

    def _parse_try_catch(self):
        """Parse: coba { ... } tangkap <var> { ... } [akhirnya { ... }]"""
        tok = self._advance()  # consume coba
        self._skip_newlines()
        try_body = self._parse_block()

        catch_var = None
        catch_body = None
        finally_body = None

        self._skip_newlines()
        if self._at(TokenType.TANGKAP):
            self._advance()
            catch_var_tok = self._expect(TokenType.IDENTIFIER, "nama variabel error")
            catch_var = catch_var_tok.value
            self._skip_newlines()
            catch_body = self._parse_block()

        self._skip_newlines()
        if self._at(TokenType.AKHIRNYA):
            self._advance()
            self._skip_newlines()
            finally_body = self._parse_block()

        return TryCatch(
            try_body, catch_var, catch_body, finally_body,
            line=tok.line, column=tok.column
        )

    def _parse_import(self):
        """Parse: impor <module> or dari <module> impor <name>, ..."""
        tok = self._advance()  # consume impor
        module_tok = self._expect(TokenType.IDENTIFIER, "nama modul")
        return ImportStatement(
            module_tok.value, line=tok.line, column=tok.column
        )

    def _parse_test_block(self):
        """Parse: uji "description" { ... }"""
        tok = self._advance()  # consume uji
        desc_tok = self._expect(TokenType.STRING, "deskripsi test")
        self._skip_newlines()
        body = self._parse_block()
        desc = desc_tok.value if isinstance(desc_tok.value, str) else str(desc_tok.value)
        return TestBlock(desc, body, line=tok.line, column=tok.column)

    def _parse_assert(self):
        """Parse: pastikan <expression> [, "message"]"""
        tok = self._advance()  # consume pastikan
        expr = self._parse_expression()
        message = None
        if self._at(TokenType.COMMA):
            self._advance()
            msg_tok = self._expect(TokenType.STRING, "pesan error")
            message = msg_tok.value if isinstance(msg_tok.value, str) else str(msg_tok.value)
        return AssertStatement(expr, message, line=tok.line, column=tok.column)

    def _parse_explore(self):
        """Parse: jelajahi <expression>"""
        tok = self._advance()  # consume jelajahi
        expr = self._parse_expression()
        return ExploreStatement(expr, line=tok.line, column=tok.column)

    def _parse_match(self):
        """Parse: cocokkan <expr> { pola <val> { ... } lainnya { ... } }"""
        tok = self._advance()  # consume cocokkan
        expr = self._parse_expression()
        self._skip_newlines()
        self._expect(TokenType.LBRACE, "'{'")
        self._skip_newlines()

        cases = []
        default_case = None

        while not self._at(TokenType.RBRACE, TokenType.EOF):
            self._skip_newlines()
            if self._at(TokenType.POLA):
                self._advance()
                pattern = self._parse_expression()
                self._skip_newlines()
                body = self._parse_block()
                cases.append((pattern, body))
            elif self._at(TokenType.LAINNYA):
                self._advance()
                self._skip_newlines()
                default_case = self._parse_block()
            else:
                break
            self._skip_newlines()

        self._expect(TokenType.RBRACE, "'}'")
        return MatchStatement(
            expr, cases, default_case,
            line=tok.line, column=tok.column
        )

    def _parse_block(self):
        """Parse a brace-delimited block of statements."""
        self._skip_newlines()
        tok = self._expect(TokenType.LBRACE, "'{'")
        self._skip_newlines()

        statements = []
        while not self._at(TokenType.RBRACE, TokenType.EOF):
            stmt = self._parse_statement()
            if stmt is not None:
                statements.append(stmt)
            self._consume_statement_end()
            self._skip_newlines()

        self._expect(TokenType.RBRACE, "'}'")
        return Block(statements, line=tok.line, column=tok.column)

    def _parse_assignment_or_expression(self):
        """Parse assignment or expression statement."""
        expr = self._parse_expression()

        # Check for assignment operators
        if self._at(TokenType.ASSIGN):
            self._advance()
            value = self._parse_expression()
            if isinstance(expr, Identifier):
                return Assignment(expr, value, "=",
                                  line=expr.line, column=expr.column)
            elif isinstance(expr, IndexAccess):
                return Assignment(expr, value, "=",
                                  line=expr.line, column=expr.column)
            elif isinstance(expr, DotAccess):
                return Assignment(expr, value, "=",
                                  line=expr.line, column=expr.column)
            else:
                loc = SourceLocation(self.filename, expr.line, expr.column)
                raise ParseError(
                    "Target assignment tidak valid",
                    loc,
                    help_text="Hanya variabel, indeks, atau atribut yang bisa di-assign."
                )

        # Compound assignment
        compound_ops = {
            TokenType.PLUS_ASSIGN: "+=",
            TokenType.MINUS_ASSIGN: "-=",
            TokenType.STAR_ASSIGN: "*=",
            TokenType.SLASH_ASSIGN: "/=",
        }
        for tok_type, op_str in compound_ops.items():
            if self._at(tok_type):
                self._advance()
                value = self._parse_expression()
                if isinstance(expr, Identifier):
                    return Assignment(expr, value, op_str,
                                      line=expr.line, column=expr.column)
                elif isinstance(expr, IndexAccess):
                    return Assignment(expr, value, op_str,
                                      line=expr.line, column=expr.column)
                elif isinstance(expr, DotAccess):
                    return Assignment(expr, value, op_str,
                                      line=expr.line, column=expr.column)
                loc = SourceLocation(self.filename, expr.line, expr.column)
                raise ParseError(
                    "Target assignment tidak valid", loc,
                )

        return ExpressionStatement(expr, line=expr.line, column=expr.column)

    # ── Expression Parsing (Precedence Climbing) ──────────────────

    def _parse_expression(self):
        """Parse an expression, starting from lowest precedence."""
        return self._parse_pipeline()

    def _parse_pipeline(self):
        """Parse pipeline expressions: expr |> func (supports multiline)"""
        left = self._parse_logical_or()

        while True:
            # Check for |> possibly across newlines
            if self._at(TokenType.PIPE):
                self._advance()
                self._skip_newlines()
                right = self._parse_logical_or()
                left = PipeExpression(left, right, line=left.line, column=left.column)
            elif self._at(TokenType.NEWLINE):
                # Peek past newlines to see if there's a |> continuation
                saved_pos = self.pos
                self._skip_newlines()
                if self._at(TokenType.PIPE):
                    self._advance()
                    self._skip_newlines()
                    right = self._parse_logical_or()
                    left = PipeExpression(left, right, line=left.line, column=left.column)
                else:
                    # Not a pipeline continuation, restore position
                    self.pos = saved_pos
                    break
            else:
                break

        return left

    def _parse_logical_or(self):
        """Parse: expr atau expr"""
        left = self._parse_logical_and()

        while self._at(TokenType.ATAU):
            self._advance()
            right = self._parse_logical_and()
            left = LogicalOp("atau", left, right, line=left.line, column=left.column)

        return left

    def _parse_logical_and(self):
        """Parse: expr dan expr"""
        left = self._parse_logical_not()

        while self._at(TokenType.DAN):
            self._advance()
            right = self._parse_logical_not()
            left = LogicalOp("dan", left, right, line=left.line, column=left.column)

        return left

    def _parse_logical_not(self):
        """Parse: bukan expr"""
        if self._at(TokenType.BUKAN):
            tok = self._advance()
            operand = self._parse_logical_not()
            return UnaryOp("bukan", operand, line=tok.line, column=tok.column)
        return self._parse_comparison()

    def _parse_comparison(self):
        """Parse comparison operators: ==, !=, <, >, <=, >="""
        left = self._parse_addition()

        comparison_ops = {
            TokenType.EQ: "==",
            TokenType.NEQ: "!=",
            TokenType.LT: "<",
            TokenType.GT: ">",
            TokenType.LTE: "<=",
            TokenType.GTE: ">=",
        }

        while self._current().type in comparison_ops:
            op_token = self._advance()
            op = comparison_ops[op_token.type]
            right = self._parse_addition()
            left = ComparisonOp(op, left, right,
                                line=left.line, column=left.column)

        return left

    def _parse_addition(self):
        """Parse + and - with left associativity."""
        left = self._parse_multiplication()

        while self._at(TokenType.PLUS, TokenType.MINUS):
            op = "+" if self._current().type == TokenType.PLUS else "-"
            self._advance()
            right = self._parse_multiplication()
            left = BinaryOp(op, left, right,
                            line=left.line, column=left.column)

        return left

    def _parse_multiplication(self):
        """Parse *, /, //, and % with left associativity."""
        left = self._parse_power()

        while self._at(TokenType.STAR, TokenType.SLASH,
                       TokenType.FLOOR_DIV, TokenType.PERCENT):
            op_map = {
                TokenType.STAR: "*",
                TokenType.SLASH: "/",
                TokenType.FLOOR_DIV: "//",
                TokenType.PERCENT: "%",
            }
            op = op_map[self._current().type]
            self._advance()
            right = self._parse_power()
            left = BinaryOp(op, left, right,
                            line=left.line, column=left.column)

        return left

    def _parse_power(self):
        """Parse ** (right associative)."""
        base = self._parse_unary()

        if self._at(TokenType.POWER):
            self._advance()
            exponent = self._parse_power()  # right-associative
            return BinaryOp("**", base, exponent,
                            line=base.line, column=base.column)

        return base

    def _parse_unary(self):
        """Parse unary - and +."""
        if self._at(TokenType.MINUS):
            tok = self._advance()
            operand = self._parse_unary()
            return UnaryOp("-", operand, line=tok.line, column=tok.column)

        if self._at(TokenType.PLUS):
            tok = self._advance()
            operand = self._parse_unary()
            return UnaryOp("+", operand, line=tok.line, column=tok.column)

        return self._parse_postfix()

    def _parse_postfix(self):
        """Parse postfix operations: function calls, indexing, dot access."""
        node = self._parse_primary()

        while True:
            if self._at(TokenType.LPAREN):
                node = self._parse_call(node)
            elif self._at(TokenType.LBRACKET):
                node = self._parse_index(node)
            elif self._at(TokenType.DOT):
                self._advance()
                attr_tok = self._expect(TokenType.IDENTIFIER, "nama atribut")
                # Check if it's a method call
                if self._at(TokenType.LPAREN):
                    args = self._parse_argument_list()
                    node = MethodCall(
                        node, attr_tok.value, args,
                        line=node.line, column=node.column
                    )
                else:
                    node = DotAccess(
                        node, attr_tok.value,
                        line=node.line, column=node.column
                    )
            else:
                break

        return node

    def _parse_call(self, callee):
        """Parse function call arguments."""
        args = self._parse_argument_list()
        return FunctionCall(callee, args, line=callee.line, column=callee.column)

    def _parse_argument_list(self):
        """Parse: ( arg1, arg2, ... )"""
        self._expect(TokenType.LPAREN, "'('")
        args = []
        self._skip_newlines()

        if not self._at(TokenType.RPAREN):
            args.append(self._parse_expression())
            while self._at(TokenType.COMMA):
                self._advance()
                self._skip_newlines()
                if self._at(TokenType.RPAREN):
                    break  # trailing comma
                args.append(self._parse_expression())

        self._skip_newlines()
        self._expect(TokenType.RPAREN, "')'")
        return args

    def _parse_index(self, obj):
        """Parse: obj[index]"""
        self._advance()  # consume [
        index = self._parse_expression()
        self._expect(TokenType.RBRACKET, "']'")
        return IndexAccess(obj, index, line=obj.line, column=obj.column)

    def _parse_primary(self):
        """Parse primary expressions (atoms)."""
        tok = self._current()

        # Number literals
        if tok.type == TokenType.INTEGER:
            self._advance()
            return NumberLiteral(tok.value, line=tok.line, column=tok.column)

        if tok.type == TokenType.FLOAT:
            self._advance()
            return NumberLiteral(tok.value, line=tok.line, column=tok.column)

        # String literals
        if tok.type == TokenType.STRING:
            self._advance()
            if isinstance(tok.value, list):
                # Interpolated string — parse embedded expressions
                parts = []
                for ptype, pval in tok.value:
                    if ptype == "str":
                        parts.append(("str", pval))
                    elif ptype == "expr":
                        # Parse the expression text
                        from .lexer import Lexer
                        sub_lexer = Lexer(pval, self.filename)
                        sub_tokens = sub_lexer.tokenize()
                        sub_parser = Parser(sub_tokens, self.filename, self.source)
                        expr_node = sub_parser._parse_expression()
                        parts.append(("expr", expr_node))
                return InterpolatedString(parts, line=tok.line, column=tok.column)
            return StringLiteral(tok.value, line=tok.line, column=tok.column)

        # Boolean
        if tok.type == TokenType.BOOLEAN:
            self._advance()
            return BooleanLiteral(tok.value, line=tok.line, column=tok.column)

        # Null
        if tok.type == TokenType.NULL:
            self._advance()
            return NullLiteral(line=tok.line, column=tok.column)

        # Identifier (or lambda)
        if tok.type == TokenType.IDENTIFIER:
            # Check for single-param lambda: param => expr
            if self._peek().type == TokenType.ARROW:
                return self._parse_lambda_expression()
            self._advance()
            return Identifier(tok.value, line=tok.line, column=tok.column)

        # Parenthesized expression or lambda
        if tok.type == TokenType.LPAREN:
            return self._parse_paren_or_lambda()

        # List literal
        if tok.type == TokenType.LBRACKET:
            return self._parse_list_literal()

        # Map literal
        if tok.type == TokenType.LBRACE:
            return self._parse_map_literal()

        # Unexpected token
        loc = SourceLocation(self.filename, tok.line, tok.column, tok.length)
        raise UnexpectedTokenError("ekspresi", tok.value, loc)

    def _parse_paren_or_lambda(self):
        """Parse parenthesized expression or lambda: (params) => body"""
        # Save position to backtrack if needed
        saved_pos = self.pos

        try:
            # Try to parse as lambda
            self._advance()  # consume (
            params = []

            if self._at(TokenType.IDENTIFIER):
                params.append(self._current().value)
                self._advance()
                while self._at(TokenType.COMMA):
                    self._advance()
                    params.append(
                        self._expect(TokenType.IDENTIFIER, "nama parameter").value
                    )

            if self._at(TokenType.RPAREN):
                self._advance()
                if self._at(TokenType.ARROW):
                    self._advance()
                    body = self._parse_expression()
                    tok = self.tokens[saved_pos]
                    return LambdaExpression(
                        params, body,
                        line=tok.line, column=tok.column
                    )
        except (ParseError, IndexError):
            pass

        # Backtrack and parse as parenthesized expression
        self.pos = saved_pos
        self._advance()  # consume (
        expr = self._parse_expression()
        self._expect(TokenType.RPAREN, "')'")
        return expr

    def _parse_lambda_expression(self):
        """Parse: param => expr"""
        tok = self._advance()  # consume identifier
        self._advance()  # consume =>
        body = self._parse_expression()
        return LambdaExpression(
            [tok.value], body,
            line=tok.line, column=tok.column
        )

    def _parse_list_literal(self):
        """Parse: [elem1, elem2, ...]"""
        tok = self._advance()  # consume [
        elements = []
        self._skip_newlines()

        if not self._at(TokenType.RBRACKET):
            elements.append(self._parse_expression())
            while self._at(TokenType.COMMA):
                self._advance()
                self._skip_newlines()
                if self._at(TokenType.RBRACKET):
                    break
                elements.append(self._parse_expression())

        self._skip_newlines()
        self._expect(TokenType.RBRACKET, "']'")
        return ListLiteral(elements, line=tok.line, column=tok.column)

    def _parse_map_literal(self):
        """Parse: { key: value, ... }"""
        tok = self._advance()  # consume {
        pairs = []
        self._skip_newlines()

        if not self._at(TokenType.RBRACE):
            key = self._parse_expression()
            self._expect(TokenType.COLON, "':'")
            value = self._parse_expression()
            pairs.append((key, value))

            while self._at(TokenType.COMMA):
                self._advance()
                self._skip_newlines()
                if self._at(TokenType.RBRACE):
                    break
                key = self._parse_expression()
                self._expect(TokenType.COLON, "':'")
                value = self._parse_expression()
                pairs.append((key, value))

        self._skip_newlines()
        self._expect(TokenType.RBRACE, "'}'")
        return MapLiteral(pairs, line=tok.line, column=tok.column)


def parse(tokens, filename="<stdin>", source=""):
    """Convenience function to parse tokens into an AST."""
    return Parser(tokens, filename, source).parse()

"""expr for parser LOOM programming language"""

from AstLOOM import (
    Assign, Ternary, Binary, Unary,
    PreIncDec, PostIncDec,
    Call, Index, Member,
    Literal, Identifier,
    ArrayLiteral, DictLiteral,
    ConsoleCall, InputCall,
    ThisExpr, SuperExpr,
    AwaitExpr,
    RangeExpr,
)

from TokensLOOM import (
    ASSIGN_OPS,
    BINARY_OP_TEXT,
    UNARY_OP_TEXT,
)

class ExprMixin:

    def parse_expr(self):
        return self.parse_assignment()

    def parse_assignment(self):
        left = self.parse_ternary()
        if self.ts.peek().type in ASSIGN_OPS:
            op_tok = self.ts.next()
            op = ASSIGN_OPS[op_tok.type]
            right = self.parse_assignment()
            return Assign(op_tok.line, op_tok.col, op, left, right)
        return left

    def parse_ternary(self):
        cond = self.parse_logic_or()
        if self.ts.at('QUESTION'):
            q = self.ts.next()
            then = self.parse_expr()
            self.ts.expect('COLON')
            else_ = self.parse_expr()
            return Ternary(q.line, q.col, cond, then, else_)
        return cond

    def parse_logic_or(self):
        return self._parse_binop(self.parse_logic_and, {'OR'})

    def parse_logic_and(self):
        return self._parse_binop(self.parse_bitwise_or, {'AND'})

    def parse_bitwise_or(self):
        return self._parse_binop(self.parse_bitwise_xor, {'BIT_OR'})

    def parse_bitwise_xor(self):
        return self._parse_binop(self.parse_bitwise_and, {'BIT_XOR'})

    def parse_bitwise_and(self):
        return self._parse_binop(self.parse_equality, {'BIT_AND'})

    def parse_equality(self):
        return self._parse_binop(self.parse_comparison, {'EQ', 'NEQ'})

    def parse_comparison(self):
        return self._parse_binop(
            self.parse_range_top,
            {'LT', 'GT', 'LE', 'GE'},
        )

    def parse_range_top(self):
        left = self.parse_shift()
        if self.ts.at('RANGE_DOTS', 'RANGE_DOTS_EQ'):
            op = self.ts.next()
            right = self.parse_shift()
            inclusive = (op.type == 'RANGE_DOTS_EQ')
            return RangeExpr(left.line, left.col, left, right, None, inclusive)
        return left

    def parse_shift(self):
        return self._parse_binop(self.parse_additive, {'LSHIFT', 'RSHIFT'})

    def parse_additive(self):
        return self._parse_binop(self.parse_multiplicative, {'PLUS', 'MINUS'})

    def parse_multiplicative(self):
        return self._parse_binop(
            self.parse_power,
            {'MUL', 'DIV', 'IDIV', 'MOD'},
        )

    def parse_power(self):
        left = self.parse_unary()
        if self.ts.at('POW'):
            op = self.ts.next()
            right = self.parse_unary()
            return Binary(op.line, op.col, '**', left, right)
        return left

    def parse_unary(self):
        t = self.ts.peek()

        if t.type in ('MINUS', 'NOT', 'BIT_NOT'):
            self.ts.next()
            op_text = UNARY_OP_TEXT[t.type]
            operand = self.parse_unary()
            return Unary(t.line, t.col, op_text, operand)

        if t.type in ('INC', 'DEC'):
            self.ts.next()
            op_text = '++' if t.type == 'INC' else '--'
            operand = self.parse_unary()
            return PreIncDec(t.line, t.col, op_text, operand)

        if t.type == 'AWAIT':
            self.ts.next()
            operand = self.parse_unary()
            return AwaitExpr(t.line, t.col, operand)

        return self.parse_postfix()

    def parse_postfix(self):
        expr = self.parse_primary()

        while True:
            t = self.ts.peek()

            if t.type == 'LPAREN':
                expr = self._finish_call(expr)

            elif t.type == 'LBRACKET':
                self.ts.next()
                idx = self.parse_expr()
                self.ts.expect('RBRACKET')
                expr = Index(t.line, t.col, expr, idx)

            elif t.type == 'DOT':
                self.ts.next()
                name = self.ts.expect('ID')
                expr = Member(t.line, t.col, expr, name.value)

            elif t.type == 'DOUBLE_COLON':
                self.ts.next()
                name = self.ts.expect('ID')
                expr = Member(t.line, t.col, expr, name.value)

            elif t.type in ('INC', 'DEC'):
                self.ts.next()
                op_text = '++' if t.type == 'INC' else '--'
                expr = PostIncDec(t.line, t.col, op_text, expr)

            else:
                break

        return expr

    def _finish_call(self, callee):
        lp = self.ts.expect('LPAREN')
        args = []
        if not self.ts.at('RPAREN'):
            args.append(self.parse_expr())
            while self.ts.at('COMMA'):
                self.ts.next()
                args.append(self.parse_expr())
        self.ts.expect('RPAREN')
        return Call(lp.line, lp.col, callee, args)

    def parse_primary(self):
        t = self.ts.peek()

        # --- literals ---
        if t.type == 'LITERAL_INT':
            self.ts.next()
            return Literal(t.line, t.col, t.value, 'int')

        if t.type == 'LITERAL_DOUBLE':
            self.ts.next()
            return Literal(t.line, t.col, t.value, 'double')

        if t.type == 'LITERAL_STR':
            self.ts.next()
            return Literal(t.line, t.col, t.value, 'str')

        if t.type == 'LITERAL_CHAR':
            self.ts.next()
            return Literal(t.line, t.col, t.value, 'char')

        if t.type in ('TRUE', 'FALSE'):
            self.ts.next()
            return Literal(t.line, t.col, t.type == 'TRUE', 'bool')

        if t.type == 'ID':
            self.ts.next()
            return Identifier(t.line, t.col, t.value)

        if t.type == 'LPAREN':
            self.ts.next()
            e = self.parse_expr()
            self.ts.expect('RPAREN')
            return e

        if t.type == 'LBRACKET':
            return self.parse_array_literal()

        if t.type == 'LBRACE':
            return self.parse_dict_literal()

        if t.type == 'CONSOLE':
            return self.parse_console()

        if t.type == 'INPUT':
            return self.parse_input()

        if t.type in ('THIS', 'SELF'):
            self.ts.next()
            return ThisExpr(t.line, t.col)

        if t.type == 'SUPER':
            self.ts.next()
            method = None
            if self.ts.at('DOT'):
                self.ts.next()
                method = self.ts.expect('ID').value
            return SuperExpr(t.line, t.col, method)

        if t.type == 'LAMBDA':
            return self.parse_lambda()

        if t.type == 'NEW':
            return self.parse_new()

        if t.type in ('MAP', 'FILTER', 'REDUCE'):
            return self.parse_func_builtin()

        raise self.error(f"unexpected token {t.type} ({t.value!r})")

    def parse_array_literal(self):
        lb = self.ts.expect('LBRACKET')
        items = []
        if not self.ts.at('RBRACKET'):
            items.append(self.parse_expr())
            while self.ts.at('COMMA'):
                self.ts.next()
                if self.ts.at('RBRACKET'):
                    break
                items.append(self.parse_expr())
        self.ts.expect('RBRACKET')
        return ArrayLiteral(lb.line, lb.col, items)

    def parse_dict_literal(self):
        lb = self.ts.expect('LBRACE')
        entries = []
        if not self.ts.at('RBRACE'):
            entries.append(self._parse_dict_entry())
            while self.ts.at('COMMA'):
                self.ts.next()
                if self.ts.at('RBRACE'):
                    break
                entries.append(self._parse_dict_entry())
        self.ts.expect('RBRACE')
        return DictLiteral(lb.line, lb.col, entries)

    def _parse_dict_entry(self):
        key = self.parse_expr()
        self.ts.expect('COLON')
        val = self.parse_expr()
        return (key, val)

    def parse_console(self):
        kw = self.ts.expect('CONSOLE')
        self.ts.expect('DOT')
        method_tok = self.ts.expect('ID')
        self.ts.expect('LPAREN')
        args = []
        if not self.ts.at('RPAREN'):
            args.append(self.parse_expr())
            while self.ts.at('COMMA'):
                self.ts.next()
                args.append(self.parse_expr())
        self.ts.expect('RPAREN')
        return ConsoleCall(kw.line, kw.col, method_tok.value, args)

    def parse_input(self):
        kw = self.ts.expect('INPUT')
        self.ts.expect('LPAREN')
        prompt = None
        if not self.ts.at('RPAREN'):
            prompt = self.parse_expr()
        self.ts.expect('RPAREN')
        return InputCall(kw.line, kw.col, prompt)

    def _parse_binop(self, next_parser, ops):
        left = next_parser()
        while self.ts.peek().type in ops:
            op_tok = self.ts.next()
            right = next_parser()
            left = Binary(
                op_tok.line, op_tok.col,
                BINARY_OP_TEXT[op_tok.type],
                left, right,
            )
        return left
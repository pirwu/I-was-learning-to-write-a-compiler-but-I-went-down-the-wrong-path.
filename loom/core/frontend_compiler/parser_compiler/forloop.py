"""For-loop for parser LOOM programming language"""

from AstLOOM import (
    ForIn, ForCStyle, Block,
    RangeExpr, RangeCall,
    EnumerateExpr, ZipExpr, ReversedExpr,
    Identifier, Call,
)

class ForMixin:

    def parse_for(self):
        kw = self.ts.expect('FOR')
        self.ts.expect('LPAREN')

        if self.ts.at('ID') and self.ts.peek(1).type in ('IN', 'OF'):
            name_tok = self.ts.next()
            self.ts.next()
            iterable = self.parse_for_iterable()
            self.ts.expect('RPAREN')
            body = self.parse_block()
            if self.ts.at('ENDFOR'):
                self.ts.next()
            return ForIn(
                line=kw.line,
                col=kw.col,
                var=name_tok.value,
                iterable=iterable,
                body=body,
            )

        init = self._parse_for_init()
        self.ts.expect('SEMICOLON')
        cond = None if self.ts.at('SEMICOLON') else self.parse_expr()
        self.ts.expect('SEMICOLON')
        step = None if self.ts.at('RPAREN') else self.parse_expr()
        self.ts.expect('RPAREN')
        body = self.parse_block()
        if self.ts.at('ENDFOR'):
            self.ts.next()
        return ForCStyle(
            line=kw.line,
            col=kw.col,
            init=init,
            cond=cond,
            step=step,
            body=body,
        )

    def _parse_for_init(self):
        
        t = self.ts.peek()

        if t.type in ('VAR', 'CONST'):
            kw = self.ts.next()
            kind = 'var' if kw.type == 'VAR' else 'const'
            name_tok = self.ts.expect('ID')
            self.ts.expect('COLON')
            type_ = self.parse_type()
            init = None
            if self.ts.at('ASSIGN'):
                self.ts.next()
                init = self.parse_expr()
            from AstLOOM import VarDecl
            return VarDecl(kw.line, kw.col, kind, name_tok.value, type_, init)

        if t.type == 'SEMICOLON':
            return None

        return self.parse_expr()

    def parse_for_iterable(self):
        t = self.ts.peek()

        if t.type == 'RANGE':
            return self._parse_range_call()

        if t.type == 'ENUMERATE':
            return self._parse_enumerate()

        if t.type == 'ZIP':
            return self._parse_zip()

        if t.type == 'REVERSED':
            return self._parse_reversed()

        return self.parse_expr()

    def _parse_range_call(self):
        kw = self.ts.expect('RANGE')
        self.ts.expect('LPAREN')
        args = []
        if not self.ts.at('RPAREN'):
            args.append(self.parse_expr())
            while self.ts.at('COMMA'):
                self.ts.next()
                args.append(self.parse_expr())
        self.ts.expect('RPAREN')
        return RangeCall(kw.line, kw.col, args)

    def _parse_enumerate(self):
        kw = self.ts.expect('ENUMERATE')
        self.ts.expect('LPAREN')
        inner = self.parse_expr()
        self.ts.expect('RPAREN')
        return EnumerateExpr(kw.line, kw.col, inner)

    def _parse_zip(self):
        kw = self.ts.expect('ZIP')
        self.ts.expect('LPAREN')
        parts = []
        if not self.ts.at('RPAREN'):
            parts.append(self.parse_expr())
            while self.ts.at('COMMA'):
                self.ts.next()
                parts.append(self.parse_expr())
        self.ts.expect('RPAREN')
        return ZipExpr(kw.line, kw.col, parts)

    def _parse_reversed(self):
        kw = self.ts.expect('REVERSED')
        self.ts.expect('LPAREN')
        inner = self.parse_expr()
        self.ts.expect('RPAREN')
        return ReversedExpr(kw.line, kw.col, inner)
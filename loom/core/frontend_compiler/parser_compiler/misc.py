"""Misce for parser LPL"""

from AstLOOM import (
    Goto, Assert, Raise, Throw,
    Decorator,
    FuncDecl, ClassDecl,
)

class MiscMixin:

    def parse_goto(self):
        kw = self.ts.expect('GOTO')
        label = self.ts.expect('ID').value
        self.ts.expect('SEMICOLON')
        return Goto(kw.line, kw.col, label)

    def parse_assert(self):
        kw = self.ts.expect('ASSERT')
        cond = self.parse_expr()
        message = None
        if self.ts.at('COLON'):
            self.ts.next()
            message = self.parse_expr()
        self.ts.expect('SEMICOLON')
        return Assert(kw.line, kw.col, cond, message)

    def parse_raise(self):
        kw = self.ts.next()
        value = self.parse_expr()
        self.ts.expect('SEMICOLON')
        if kw.type == 'RAISE':
            return Raise(kw.line, kw.col, value)
        return Throw(kw.line, kw.col, value)

    def parse_decorated(self):
        decorators = []
        while self.ts.at('AT'):
            decorators.append(self._parse_decorator())

        if self.ts.at('FUNCTION'):
            return self.parse_func_decl(decorators)
        if self.ts.at('ASYNC', 'STATIC'):
            return self.parse_func_decl(decorators)
        if self.ts.at('ABSTRACT', 'CLASS'):
            return self.parse_class_decl(decorators)

        t = self.ts.peek()
        raise self.error(
            f"decorators can only be applied to function or class, "
            f"got {t.type} ({t.value!r})", t)

    def _parse_decorator(self):
        at = self.ts.expect('AT')
        name_tok = self.ts.expect('ID')
        args = []
        if self.ts.at('LPAREN'):
            self.ts.next()
            if not self.ts.at('RPAREN'):
                args.append(self.parse_expr())
                while self.ts.at('COMMA'):
                    self.ts.next()
                    args.append(self.parse_expr())
            self.ts.expect('RPAREN')
        return Decorator(at.line, at.col, name_tok.value, args)
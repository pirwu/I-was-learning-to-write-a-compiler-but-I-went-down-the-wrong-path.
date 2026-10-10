"""Try / except / finally parsing for parser LOOMPL"""

from AstLOOM import Try, ExceptClause, Block

class TryMixin:

    def parse_try(self):
        kw = self.ts.expect('TRY')
        body = self.parse_block()

        excepts = []
        while self.ts.at('EXCEPT'):
            excepts.append(self._parse_except_clause())

        finally_ = None
        if self.ts.at('FINALLY'):
            self.ts.next()
            finally_ = self.parse_block()

        if self.ts.at('ENDTRY'):
            self.ts.next()

        if not excepts and finally_ is None:
            raise self.error(
                "try must have at least one 'except' or a 'finally' block",
                kw)

        return Try(kw.line, kw.col, body, excepts, finally_)

    def _parse_except_clause(self):
        kw = self.ts.expect('EXCEPT')

        exc_type = None
        alias = None

        if self.ts.at('ID'):
            name_tok = self.ts.next()
            from AstLOOM import Identifier
            exc_type = Identifier(name_tok.line, name_tok.col, name_tok.value)
            if self.ts.at('AS'):
                self.ts.next()
                alias = self.ts.expect('ID').value

        body = self.parse_block()
        return ExceptClause(kw.line, kw.col, exc_type, alias, body)
"""Pattern for parser LOOM programming langguage"""

from AstLOOM import (
    Match, MatchArm,
    Switch, CaseClause, DefaultClause,
    Block,
    PatternLiteral, PatternIdent, PatternWildcard,
    PatternOr, PatternCall,
    Literal, Identifier,
)

class PatternMixin:

    def parse_match(self):
        kw = self.ts.expect('MATCH')
        subject = self.parse_expr()
        self.ts.expect('LBRACE')

        arms = []
        while self.ts.at('WHEN'):
            arms.append(self._parse_match_arm())

        self.ts.expect('RBRACE')
        if self.ts.at('ENDMATCH'):
            self.ts.next()

        if not arms:
            raise self.error("match must have at least one 'when' arm", kw)

        return Match(kw.line, kw.col, subject, arms)

    def _parse_match_arm(self):
        w = self.ts.expect('WHEN')
        pattern = self.parse_pattern()

        guard = None
        if self.ts.at('IF'):
            self.ts.next()
            guard = self.parse_expr()

        self.ts.expect('ARROW_FAT')

        if self.ts.at('LBRACE'):
            body = self.parse_block()
        else:
            body = self.parse_expr()

        if self.ts.at('COMMA'):
            self.ts.next()

        return MatchArm(w.line, w.col, pattern, guard, body)

    def parse_pattern(self):
        return self._parse_pattern_or()

    def _parse_pattern_or(self):
        parts = [self._parse_pattern_primary()]
        while self.ts.at('BIT_OR'):
            self.ts.next()
            parts.append(self._parse_pattern_primary())
        if len(parts) == 1:
            return parts[0]
        return PatternOr(parts[0].line, parts[0].col, parts)

    def _parse_pattern_primary(self):
        t = self.ts.peek()

        if t.type == 'ID' and t.value == '_':
            self.ts.next()
            return PatternWildcard(t.line, t.col)

        if t.type == 'LITERAL_INT':
            self.ts.next()
            return PatternLiteral(t.line, t.col, t.value, 'int')
        if t.type == 'LITERAL_DOUBLE':
            self.ts.next()
            return PatternLiteral(t.line, t.col, t.value, 'double')
        if t.type == 'LITERAL_STR':
            self.ts.next()
            return PatternLiteral(t.line, t.col, t.value, 'str')
        if t.type == 'LITERAL_CHAR':
            self.ts.next()
            return PatternLiteral(t.line, t.col, t.value, 'char')
        if t.type in ('TRUE', 'FALSE'):
            self.ts.next()
            return PatternLiteral(t.line, t.col, t.type == 'TRUE', 'bool')

        if t.type == 'ID':
            self.ts.next()
            if self.ts.at('LPAREN'):
                self.ts.next()
                args = []
                if not self.ts.at('RPAREN'):
                    args.append(self.parse_pattern())
                    while self.ts.at('COMMA'):
                        self.ts.next()
                        args.append(self.parse_pattern())
                self.ts.expect('RPAREN')
                return PatternCall(t.line, t.col, t.value, args)
            return PatternIdent(t.line, t.col, t.value)

        if t.type == 'LPAREN':
            self.ts.next()
            inner = self.parse_pattern()
            self.ts.expect('RPAREN')
            return inner

        raise self.error(
            f"expected pattern, got {t.type} ({t.value!r})", t)

    def parse_switch(self):
        kw = self.ts.expect('SWITCH')
        self.ts.expect('LPAREN')
        subject = self.parse_expr()
        self.ts.expect('RPAREN')
        self.ts.expect('LBRACE')

        cases = []
        default = None

        while not self.ts.at('RBRACE', 'EOF'):
            if self.ts.at('CASE'):
                cases.append(self._parse_case_clause())
            elif self.ts.at('DEFAULT'):
                if default is not None:
                    raise self.error("duplicate 'default' clause")
                default = self._parse_default_clause()
            else:
                t = self.ts.peek()
                raise self.error(
                    f"expected 'case' or 'default', got {t.type}", t)

        self.ts.expect('RBRACE')
        if self.ts.at('ENDSWITCH'):
            self.ts.next()

        return Switch(kw.line, kw.col, subject, cases, default)

    def _parse_case_clause(self):
        kw = self.ts.expect('CASE')
        value = self.parse_expr()
        self.ts.expect('COLON')

        stmts = []
        while not self.ts.at('CASE', 'DEFAULT', 'RBRACE', 'EOF'):
            stmts.append(self.parse_stmt())

        return CaseClause(kw.line, kw.col, value, stmts)

    def _parse_default_clause(self):
        kw = self.ts.expect('DEFAULT')
        self.ts.expect('COLON')

        stmts = []
        while not self.ts.at('CASE', 'DEFAULT', 'RBRACE', 'EOF'):
            stmts.append(self.parse_stmt())

        return DefaultClause(kw.line, kw.col, stmts)
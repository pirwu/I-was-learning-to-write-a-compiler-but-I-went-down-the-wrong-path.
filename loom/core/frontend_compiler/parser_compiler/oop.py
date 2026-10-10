"""OOP for parser LPL"""

from AstLOOM import (
    ClassDecl, InterfaceDecl, StructDecl, RecordDecl,
    ClassMember, Constructor, Destructor,
    VarDecl, Block,
    NewExpr,
    Identifier,
)

class OOPMixin:

    def parse_class_decl(self, decorators=None):
        decorators = decorators or []

        is_abstract = False
        if self.ts.at('ABSTRACT'):
            self.ts.next()
            is_abstract = True

        kw = self.ts.expect('CLASS')
        name = self.ts.expect('ID').value

        extends = None
        if self.ts.at('EXTENDS'):
            self.ts.next()
            extends = self.parse_type()

        implements = []
        if self.ts.at('IMPLEMENTS'):
            self.ts.next()
            implements.append(self.parse_type())
            while self.ts.at('COMMA'):
                self.ts.next()
                implements.append(self.parse_type())

        self.ts.expect('LBRACE')
        members = []
        while not self.ts.at('RBRACE', 'EOF'):
            members.append(self._parse_class_member())
        if self.ts.at('EOF'):
            raise self.error("unexpected end of file, expected '}'", kw)
        self.ts.expect('RBRACE')

        if self.ts.at('ENDCLASS'):
            self.ts.next()

        return ClassDecl(
            kw.line, kw.col,
            name=name,
            extends=extends,
            implements=implements,
            members=members,
            is_abstract=is_abstract,
            decorators=decorators,
        )

    def _parse_class_member(self):
        access = None
        is_static = False
        is_override = False

        while True:
            if self.ts.at('PUBLIC', 'PRIVATE', 'PROTECTED') and access is None:
                tok = self.ts.next()
                access = {
                    'PUBLIC':    'public',
                    'PRIVATE':   'private',
                    'PROTECTED': 'protected',
                    }[tok.type]
            elif self.ts.at('STATIC') and not is_static:
                self.ts.next()
                is_static = True
            elif self.ts.at('OVERRIDE') and not is_override:
                self.ts.next()
                is_override = True
            else:
                break

        t = self.ts.peek()

        if t.type == 'CONSTRUCTOR':
            inner = self._parse_constructor()
        elif t.type == 'DESTRUCTOR':
            inner = self._parse_destructor()
        elif t.type in ('VAR', 'CONST'):
            inner = self.parse_var_decl()
        elif t.type == 'FUNCTION':
            inner = self.parse_func_decl()
        elif t.type == 'ASYNC':
            inner = self.parse_func_decl()
        else:
            raise self.error(
                f"unexpected token in class body: {t.type} ({t.value!r})", t)

        return ClassMember(
            line=inner.line, col=inner.col,
            access=access,
            is_static=is_static,
            is_override=is_override,
            inner=inner,
        )

    def _parse_constructor(self):
        kw = self.ts.expect('CONSTRUCTOR')
        self.ts.expect('LPAREN')
        params = self.parse_param_list_opt()
        self.ts.expect('RPAREN')
        body = self.parse_block()
        return Constructor(kw.line, kw.col, params, body)

    def _parse_destructor(self):
        kw = self.ts.expect('DESTRUCTOR')
        self.ts.expect('LPAREN')
        self.ts.expect('RPAREN')
        body = self.parse_block()
        return Destructor(kw.line, kw.col, body)

    def parse_interface_decl(self):
        kw = self.ts.expect('INTERFACE')
        name = self.ts.expect('ID').value
        self.ts.expect('LBRACE')

        members = []
        while not self.ts.at('RBRACE', 'EOF'):
            members.append(self._parse_class_member())
        if self.ts.at('EOF'):
            raise self.error("unexpected end of file, expected '}'", kw)
        self.ts.expect('RBRACE')

        return InterfaceDecl(kw.line, kw.col, name, members)

    def parse_struct_decl(self):
        kw = self.ts.expect('STRUCT')
        name = self.ts.expect('ID').value
        self.ts.expect('LBRACE')

        members = []
        while not self.ts.at('RBRACE', 'EOF'):
            members.append(self._parse_struct_member())
        if self.ts.at('EOF'):
            raise self.error("unexpected end of file, expected '}'", kw)
        self.ts.expect('RBRACE')

        if self.ts.at('ENDSTRUCT'):
            self.ts.next()

        return StructDecl(kw.line, kw.col, name, members)

    def _parse_struct_member(self):
        access = None
        if self.ts.at('PUBLIC', 'PRIVATE', 'PROTECTED'):
            tok = self.ts.next()
            access = {
                'PUBLIC':    'public',
                'PRIVATE':   'private',
                'PROTECTED': 'protected',
            }[tok.type]

        t = self.ts.peek()
        if t.type in ('VAR', 'CONST'):
            inner = self.parse_var_decl()
        else:
            raise self.error(
                f"struct members must be var/const, got {t.type} ({t.value!r})", t)

        return ClassMember(
            line=inner.line, col=inner.col,
            access=access,
            is_static=False,
            is_override=False,
            inner=inner,
        )

    def parse_record_decl(self):
        kw = self.ts.expect('RECORD')
        name = self.ts.expect('ID').value
        self.ts.expect('LPAREN')
        params = self.parse_param_list_opt()
        self.ts.expect('RPAREN')
        self.ts.expect('SEMICOLON')
        return RecordDecl(kw.line, kw.col, name, params)

    def parse_new(self):
        kw = self.ts.expect('NEW')
        type_name = self.ts.expect('ID').value
        self.ts.expect('LPAREN')
        args = []
        if not self.ts.at('RPAREN'):
            args.append(self.parse_expr())
            while self.ts.at('COMMA'):
                self.ts.next()
                args.append(self.parse_expr())
        self.ts.expect('RPAREN')
        return NewExpr(kw.line, kw.col, type_name, args)
"""Function and lambda for parser loom programming language"""

from AstLOOM import (
    FuncDecl, LambdaExpr, Param,
    FuncBuiltin,
    Block,
)

class FuncMixin:
    
    def parse_func_decl(self, decorators=None):
        decorators = decorators or []

        is_async = False
        is_static = False

        if self.ts.at('ASYNC'):
            self.ts.next()
            is_async = True
        if self.ts.at('STATIC'):
            self.ts.next()
            is_static = True

        kw = self.ts.expect('FUNCTION')
        name_tok = self.ts.expect('ID')
        self.ts.expect('LPAREN')
        params = self.parse_param_list_opt()
        self.ts.expect('RPAREN')

        ret_type = None
        if self.ts.at('ARROW'):
            self.ts.next()
            ret_type = self.parse_type()

        body = self.parse_block()
        if self.ts.at('ENDFUNCTION'):
            self.ts.next()

        return FuncDecl(
            kw.line, kw.col,
            name=name_tok.value,
            params=params,
            ret_type=ret_type,
            body=body,
            is_async=is_async,
            is_static=is_static,
            decorators=decorators,
        )

    def parse_lambda(self):
        kw = self.ts.expect('LAMBDA')
        self.ts.expect('LPAREN')
        params = self.parse_param_list_opt()
        self.ts.expect('RPAREN')

        ret_type = None
        if self.ts.at('ARROW'):
            self.ts.next()
            ret_type = self.parse_type()

        self.ts.expect('ARROW_FAT')

        if self.ts.at('LBRACE'):
            body = self.parse_block()
        else:
            body = self.parse_expr()

        return LambdaExpr(kw.line, kw.col, params, ret_type, body)

    def parse_param_list_opt(self):
        if self.ts.at('RPAREN'):
            return []
        params = [self.parse_param()]
        while self.ts.at('COMMA'):
            self.ts.next()
            params.append(self.parse_param())
        return params

    def parse_param(self):
        name_tok = self.ts.expect('ID')
        self.ts.expect('COLON')
        type_ = self.parse_type()
        default = None
        if self.ts.at('ASSIGN'):
            self.ts.next()
            default = self.parse_expr()
        return Param(name_tok.line, name_tok.col,
                     name_tok.value, type_, default)

    def parse_func_builtin(self):
        kw = self.ts.next()
        name = { 'MAP': 'map', 'FILTER': 'filter', 'REDUCE': 'reduce' }[kw.type]

        self.ts.expect('LPAREN')
        args = []
        if not self.ts.at('RPAREN'):
            args.append(self.parse_expr())
            while self.ts.at('COMMA'):
                self.ts.next()
                args.append(self.parse_expr())
        self.ts.expect('RPAREN')

        if name == 'map' and len(args) == 2:
            return FuncBuiltin(kw.line, kw.col, 'map', args[0], args[1])
        if name == 'filter' and len(args) == 2:
            return FuncBuiltin(kw.line, kw.col, 'filter', args[0], args[1])
        if name == 'reduce' and len(args) >= 2:
            return FuncBuiltin(kw.line, kw.col, 'reduce', args[0], args[1])

        raise self.error(f"{name}() expects 2 arguments (or 3 for reduce), got {len(args)}", kw)
"""stmt for parser LOOm programming language"""

from AstLOOM import (
    VarDecl, Block, EmptyStmt, ExprStmt,
    If, While, DoWhile,
    Return, Yield, Break, Continue,
)


class StmtMixin:
    def parse_stmt(self):
        t = self.ts.peek()

        if t.type in ('VAR', 'CONST'):
            return self.parse_var_decl()
        if t.type == 'IF':
            return self.parse_if()
        if t.type == 'WHILE':
            return self.parse_while()
        if t.type == 'DO':
            return self.parse_do_while()
        if t.type == 'LBRACE':
            return self.parse_block()
        if t.type == 'SEMICOLON':
            self.ts.next()
            return EmptyStmt(t.line, t.col)
        if t.type == 'RETURN':
            return self.parse_return()
        if t.type == 'BREAK':
            self.ts.next()
            self.ts.expect('SEMICOLON')
            return Break(t.line, t.col)
        if t.type == 'CONTINUE':
            self.ts.next()
            self.ts.expect('SEMICOLON')
            return Continue(t.line, t.col)
        if t.type == 'FOR':
            return self.parse_for()
        if t.type == 'FUNCTION':
            return self.parse_func_decl()
        if t.type == 'CLASS':
            return self.parse_class_decl()
        if t.type == 'INTERFACE':
            return self.parse_interface_decl()
        if t.type == 'STRUCT':
            return self.parse_struct_decl()
        if t.type == 'RECORD':
            return self.parse_record_decl()
        if t.type == 'MODULE':
            return self.parse_module_decl()
        if t.type == 'NAMESPACE':
            return self.parse_namespace_decl()
        if t.type == 'MATCH':
            return self.parse_match()
        if t.type == 'SWITCH':
            return self.parse_switch()
        if t.type == 'TRY':
            return self.parse_try()
        if t.type == 'GOTO':
            return self.parse_goto()
        if t.type == 'ASSERT':
            return self.parse_assert()
        if t.type in ('RAISE', 'THROW'):
            return self.parse_raise()
        if t.type == 'ASYNC':
            return self.parse_async_stmt()
        if t.type == 'SYNC':
            return self.parse_sync_block()
        if t.type == 'LOCK':
            return self.parse_lock_stmt()
        if t.type == 'IMPORT':
            return self.parse_import()
        if t.type == 'FROM':
            return self.parse_from_import()
        if t.type == 'EXPORT':
            return self.parse_export()
        if t.type == 'PACKAGE':
            return self.parse_package_decl()
        if t.type == 'THREAD':
            return self.parse_thread_decl()
        if t.type == 'PROCESS':
            return self.parse_process_decl()
        if t.type == 'COROUTINE':
            return self.parse_coroutine_decl()
        if t.type == 'MUTEX':
            return self.parse_mutex_decl()
        if t.type == 'SEMAPHORE':
            return self.parse_semaphore_decl()
        if t.type == 'YIELD':
            return self.parse_yield()
        if t.type == 'AT':
            return self.parse_decorated()

        return self.parse_expr_stmt()

    def parse_var_decl(self):
        kw = self.ts.next()
        kind = 'var' if kw.type == 'VAR' else 'const'
        name_tok = self.ts.expect('ID')
        self.ts.expect('COLON')
        type_ = self.parse_type()
        init = None
        if self.ts.at('ASSIGN'):
            self.ts.next()
            init = self.parse_expr()
        self.ts.expect('SEMICOLON')
        return VarDecl(kw.line, kw.col, kind, name_tok.value, type_, init)

    def parse_block(self):
        lb = self.ts.expect('LBRACE')
        stmts = []
        while not self.ts.at('RBRACE', 'EOF'):
            stmts.append(self.parse_stmt())
        if self.ts.at('EOF'):
            raise self.error("unexpected end of file, expected '}'")
        self.ts.expect('RBRACE')
        return Block(lb.line, lb.col, stmts)

    def parse_if(self):
        kw = self.ts.expect('IF')
        self.ts.expect('LPAREN')
        cond = self.parse_expr()
        self.ts.expect('RPAREN')
        then = self.parse_block()

        elifs = []
        while self.ts.at('ELSEIF'):
            self.ts.next()
            self.ts.expect('LPAREN')
            ec = self.parse_expr()
            self.ts.expect('RPAREN')
            elifs.append((ec, self.parse_block()))

        else_ = None
        if self.ts.at('ELSE'):
            self.ts.next()
            else_ = self.parse_block()

        if self.ts.at('ENDIF'):
            self.ts.next()

        return If(kw.line, kw.col, cond, then, elifs, else_)

    def parse_while(self):
        kw = self.ts.expect('WHILE')
        self.ts.expect('LPAREN')
        cond = self.parse_expr()
        self.ts.expect('RPAREN')
        body = self.parse_block()
        if self.ts.at('ENDWHILE'):
            self.ts.next()
        return While(kw.line, kw.col, cond, body)

    def parse_do_while(self):
        kw = self.ts.expect('DO')
        body = self.parse_block()
        self.ts.expect('WHILE')
        self.ts.expect('LPAREN')
        cond = self.parse_expr()
        self.ts.expect('RPAREN')
        self.ts.expect('SEMICOLON')
        if self.ts.at('ENDDO'):
            self.ts.next()
        return DoWhile(kw.line, kw.col, body, cond)

    def parse_return(self):
        kw = self.ts.expect('RETURN')
        value = None
        if not self.ts.at('SEMICOLON'):
            value = self.parse_expr()
        self.ts.expect('SEMICOLON')
        return Return(kw.line, kw.col, value)

    def parse_yield(self):
        kw = self.ts.expect('YIELD')
        value = None
        if not self.ts.at('SEMICOLON'):
            value = self.parse_expr()
        self.ts.expect('SEMICOLON')
        return Yield(kw.line, kw.col, value)

    def parse_expr_stmt(self):
        e = self.parse_expr()
        self.ts.expect('SEMICOLON')
        return ExprStmt(e.line, e.col, e)

    def parse_type(self):
        from AstLOOM import BaseType, OptionalType, ArrayType, FunctionType

        t = self.ts.peek()

        if t.type == 'FUNCTION':
            self.ts.next()
            self.ts.expect('LPAREN')
            params = []
            if not self.ts.at('RPAREN'):
                params.append(self.parse_type())
                while self.ts.at('COMMA'):
                    self.ts.next()
                    params.append(self.parse_type())
            self.ts.expect('RPAREN')
            ret = None
            if self.ts.at('ARROW'):
                self.ts.next()
                ret = self.parse_type()
            return FunctionType(t.line, t.col, params, ret)

        if t.type in ('INT', 'DOUBLE', 'STR', 'CHAR', 'BOOL', 'VOID'):
            self.ts.next()
            node = BaseType(t.line, t.col, t.value)
        elif t.type == 'ID':
            self.ts.next()
            node = BaseType(t.line, t.col, t.value)
        else:
            raise self.error(f"expected type, got {t.type} ({t.value!r})")

        if self.ts.at('QUESTION'):
            q = self.ts.next()
            node = OptionalType(q.line, q.col, node)

        while self.ts.at('LBRACKET'):
            lb = self.ts.next()
            size = None
            if not self.ts.at('RBRACKET'):
                size = self.parse_expr()
            self.ts.expect('RBRACKET')
            node = ArrayType(lb.line, lb.col, node, size)

        return node
"""Concurrency pars for LPL"""

from AstLOOM import (
    AsyncStmt, SyncBlock, LockStmt,
    ThreadDecl, ProcessDecl, CoroutineDecl,
    MutexDecl, SemaphoreDecl,
)

class ConcurrencyMixin:

    def parse_async_stmt(self):
        if self.ts.peek(1).type == 'FUNCTION':
            return self.parse_func_decl()
        kw = self.ts.expect('ASYNC')
        body = self.parse_block()
        return AsyncStmt(kw.line, kw.col, body)

    def parse_sync_block(self):
        kw = self.ts.expect('SYNC')
        body = self.parse_block()
        return SyncBlock(kw.line, kw.col, body)

    def parse_lock_stmt(self):
        kw = self.ts.expect('LOCK')
        lock = self.parse_expr()
        body = self.parse_block()
        return LockStmt(kw.line, kw.col, lock, body)

    def parse_thread_decl(self):
        kw = self.ts.expect('THREAD')
        name, params, body = self._parse_named_block(kw)
        return ThreadDecl(kw.line, kw.col, name, params, body)

    def parse_process_decl(self):
        kw = self.ts.expect('PROCESS')
        name, params, body = self._parse_named_block(kw)
        return ProcessDecl(kw.line, kw.col, name, params, body)

    def parse_coroutine_decl(self):
        kw = self.ts.expect('COROUTINE')
        name, params, body = self._parse_named_block(kw)
        return CoroutineDecl(kw.line, kw.col, name, params, body)

    def _parse_named_block(self, kw):
        name = self.ts.expect('ID').value
        self.ts.expect('LPAREN')
        params = self.parse_param_list_opt()
        self.ts.expect('RPAREN')
        body = self.parse_block()
        return name, params, body

    def parse_mutex_decl(self):
        kw = self.ts.expect('MUTEX')
        name = self.ts.expect('ID').value
        self.ts.expect('SEMICOLON')
        return MutexDecl(kw.line, kw.col, name)

    def parse_semaphore_decl(self):
        kw = self.ts.expect('SEMAPHORE')
        name = self.ts.expect('ID').value
        init = None
        if self.ts.at('ASSIGN'):
            self.ts.next()
            init = self.parse_expr()
        self.ts.expect('SEMICOLON')
        return SemaphoreDecl(kw.line, kw.col, name, init)
"""Statement for LPL."""

from Codegen_COMPILER import opcodes as op
from AstLOOM import VarDecl, ExprStmt, Block

class StmtMixin:

    def gen_VarDecl(self, node):
        self.set_line(node.line)

        if node.init is not None:
            self.gen(node.init)
        else:
            self.emit_op(op.PUSH_NULL)

        if node.global_index >= 0:
            self.emit_op(op.STORE_GLOBAL)
            self.emit_u16(node.global_index)
        elif node.slot >= 0:
            self.emit_op(op.STORE_LOCAL)
            self.emit_u8(node.slot)
        else:
            raise self.error(f"VarDecl {node.name!r} has neither slot nor global_index", node)

    def gen_ExprStmt(self, node):
        self.gen(node.expr)
        if not self._expr_void(node.expr):
            self.emit_op(op.POP)

    def _expr_void(self, expr):
        from AstLOOM import ConsoleCall
        return isinstance(expr, ConsoleCall)

    def gen_Block(self, node):
        for stmt in node.stmts:
            self.gen(stmt)

    def gen_If(self, node):
        self.set_line(node.line)

        end_patches = []

        self.gen(node.cond)
        next_patch = self.emit_jump(op.JUMP_IF_FALSE)

        self.gen(node.then)
        end_patches.append(self.emit_jump(op.JUMP))

        for cond, block in node.elifs:
            self.patch_jump(next_patch)
            self.set_line(cond.line)
            self.gen(cond)
            next_patch = self.emit_jump(op.JUMP_IF_FALSE)
            self.gen(block)
            end_patches.append(self.emit_jump(op.JUMP))

        if node.else_ is not None:
            self.patch_jump(next_patch)
            self.gen(node.else_)
        else:
            self.patch_jump(next_patch)

        for p in end_patches:
            self.patch_jump(p)

    def gen_While(self, node):
        self.set_line(node.line)

        from Codegen_COMPILER.carcass import LoopContext

        top_offset = self.here()

        self.gen(node.cond)
        exit_patch = self.emit_jump(op.JUMP_IF_FALSE)

        ctx = LoopContext(continue_target=top_offset)
        self.push_loop(ctx)
        self.gen(node.body)
        self.pop_loop()

        self.emit_op(op.JUMP)
        back_at = self.here()
        self.emit_i16(0)
        self.patch_jump_to(back_at, top_offset)

        self.patch_jump(exit_patch)

        end_here = self.here()
        for p in ctx.break_patches:
            self.patch_jump_to(p, end_here)

    def gen_Return(self, node):
        self.set_line(node.line)

        if node.value is not None:
            self.gen(node.value)
            self.emit_op(op.RETURN)
        else:
            self.emit_op(op.RETURN_VOID)
            
    def gen_Break(self, node):
        ctx = self.current_loop()
        if ctx is None:
            raise self.error("'break' outside of a loop", node)
        at = self.emit_jump(op.JUMP)
        ctx.add_break_patch(at)

    def gen_Continue(self, node):
        ctx = self.current_loop()
        if ctx is None:
            raise self.error("'continue' outside of a loop", node)
        target = ctx.continue_target
        if target is None:
            raise self.error("'continue' target not set", node)
        self.emit_op(op.JUMP)
        at = self.here()
        self.emit_i16(0)
        self.patch_jump_to(at, target)
        
    def gen_ForIn(self, node):
        self.set_line(node.line)
        from Codegen_COMPILER.carcass import LoopContext

        self.gen(node.iterable)
        self.emit_op(op.GET_ITER)

        loop_top = self.here()

        exit_patch = self.emit_jump(op.ITER_NEXT)

        self.emit_op(op.STORE_LOCAL)
        self.emit_u8(node.var_slot)

        ctx = LoopContext(continue_target=loop_top)
        self.push_loop(ctx)
        self.gen(node.body)
        self.pop_loop()

        self.emit_op(op.JUMP)
        back_at = self.here()
        self.emit_i16(0)
        self.patch_jump_to(back_at, loop_top)

        self.patch_jump(exit_patch)
        end_here = self.here()
        for p in ctx.break_patches:
            self.patch_jump_to(p, end_here)

        self.emit_op(op.ITER_CLOSE)

    def gen_DoWhile(self, node):
        self.set_line(node.line)
        from Codegen_COMPILER.carcass import LoopContext

        top_offset = self.here()

        ctx = LoopContext(continue_target=None)
        self.push_loop(ctx)

        self.gen(node.body)

        ctx.continue_target = self.here()

        self.gen(node.cond)
        self.emit_op(op.JUMP_IF_TRUE)
        back_at = self.here()
        self.emit_i16(0)
        self.patch_jump_to(back_at, top_offset)

        self.pop_loop()

        end_here = self.here()
        for p in ctx.break_patches:
            self.patch_jump_to(p, end_here)

    def gen_ForCStyle(self, node):
        self.set_line(node.line)
        from Codegen_COMPILER.carcass import LoopContext

        if node.init is not None:
            self.gen(node.init)

        top_offset = self.here()

        if node.cond is not None:
            self.gen(node.cond)
            exit_patch = self.emit_jump(op.JUMP_IF_FALSE)
        else:
            exit_patch = None

        ctx = LoopContext(continue_target=None)
        self.push_loop(ctx)

        self.gen(node.body)

        ctx.continue_target = self.here()

        if node.step is not None:
            self.gen(node.step)

        self.emit_op(op.JUMP)
        back_at = self.here()
        self.emit_i16(0)
        self.patch_jump_to(back_at, top_offset)

        self.pop_loop()

        if exit_patch is not None:
            self.patch_jump(exit_patch)

        end_here = self.here()
        for p in ctx.break_patches:
            self.patch_jump_to(p, end_here)
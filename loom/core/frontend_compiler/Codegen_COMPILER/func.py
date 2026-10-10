"""Function and closure code generation for LPL."""

from Codegen_COMPILER import opcodes as op
from Codegen_COMPILER.carcass import FunctionBuffer

from AstLOOM import FuncDecl, Return

class FuncMixin:

    def gen_FuncDecl(self, node):
        self.set_line(node.line)

        buf = FunctionBuffer(
            name=node.name,
            arity=len(node.params),
            locals_count=node.frame_size,
            upvalues=node.upvalues or [],
        )

        prev_func = self.current_func
        self.push_function(buf)

        if node.body is not None:
            self.gen(node.body)

        self.emit_op(op.RETURN_VOID)

        self.pop_function()

        buf_index = self._function_index(buf)
        self.emit_op(op.MAKE_CLOSURE)
        self.emit_u16(buf_index)
        self.emit_u8(len(buf.upvalues))

        if node.global_index >= 0:
            self.emit_op(op.STORE_GLOBAL)
            self.emit_u16(node.global_index)
        elif node.slot >= 0:
            self.emit_op(op.STORE_LOCAL)
            self.emit_u8(node.slot)
        else:
            raise self.error(
                f"FuncDecl {node.name!r} has neither slot nor global_index",
                node)

    def _function_index(self, buf):
        for i, b in enumerate(self.module.functions.functions):
            if b is buf:
                return i
        raise RuntimeError("function buffer not found in function table")
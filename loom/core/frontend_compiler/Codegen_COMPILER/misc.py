"""goto, assert, raise, throw, decorators for LOOM."""

from Codegen_COMPILER import opcodes as op
from AstLOOM import Goto, Assert, Raise, Throw, Decorator

class MiscMixin:

    def gen_Goto(self, node):
        name_idx = self.module.pool.add_name(node.label)
        self.emit_op(op.GOTO)
        self.emit_u16(name_idx)

    def gen_Assert(self, node):
        self.set_line(node.line)
        self.gen(node.cond)
        if node.message is not None:
            self.gen(node.message)
        self.emit_op(op.ASSERT_CHECK)

    def gen_Raise(self, node):
        self.set_line(node.line)
        self.gen(node.value)
        self.emit_op(op.THROW)

    def gen_Throw(self, node):
        self.set_line(node.line)
        self.gen(node.value)
        self.emit_op(op.THROW)
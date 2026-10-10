"""LOOM bytecode generator"""

from Codegen_COMPILER import opcodes as op
from Codegen_COMPILER.carcass import CodegenBase, FunctionBuffer, ModuleModel
from Codegen_COMPILER.expr import ExprMixin
from Codegen_COMPILER.stmt import StmtMixin
from Codegen_COMPILER.func import FuncMixin
from Codegen_COMPILER.oop import OOPMixin
from Codegen_COMPILER.pattern import PatternMixin
from Codegen_COMPILER.error_handling import TryMixin
from Codegen_COMPILER.concurrency import ConcurrencyMixin
from Codegen_COMPILER.modules import ModuleMixin
from Codegen_COMPILER.misc import MiscMixin

class Codegen(
    ExprMixin,
    StmtMixin,
    FuncMixin,
    OOPMixin,
    PatternMixin,
    TryMixin,
    ConcurrencyMixin,
    ModuleMixin,
    MiscMixin,
    CodegenBase,
):

    def generate(self, program):
        self._program = program

        init_buf = FunctionBuffer(
            name="<init>",
            arity=0,
            locals_count=program.locals_count,
            upvalues=[],
        )
        self.push_function(init_buf)

        for item in program.items:
            self.gen(item)
            
        self.emit_op(op.RETURN_VOID)

        for name in program.globals:
            self.module.globals.add(name)

        self.module.entry_index = 0

        self.pop_function()
        return self.module

    def gen(self, node):
        if node is None:
            return
        method = getattr(self, "gen_" + type(node).__name__, None)
        if method is not None:
            method(node)
        else:
            raise self.error(f"codegen not implemented for {type(node).__name__}", node)
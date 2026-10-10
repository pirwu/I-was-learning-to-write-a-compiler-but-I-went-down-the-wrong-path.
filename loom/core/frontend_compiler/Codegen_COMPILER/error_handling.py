"""Try / except / finally code generation for LOOM."""

from Codegen_COMPILER import opcodes as op
from AstLOOM import Try

class TryMixin:

    def gen_Try(self, node):
        self.set_line(node.line)

        if not node.excepts:
            self._gen_try_finally_only(node)
            return

        end_patches = []
        next_handler_patch = None

        setup_at = self.emit_jump(op.SETUP_EXCEPT)

        self.gen(node.body)

        self.emit_op(op.POP_EXCEPT)
        end_patches.append(self.emit_jump(op.JUMP))

        for i, clause in enumerate(node.excepts):
            self.patch_jump(setup_at)

            if clause.exc_type is not None:
                name_idx = self.module.pool.add_name(clause.exc_type.name)
                self.emit_op(op.MATCH_EXCEPTION)
                self.emit_u16(name_idx)
                next_handler_patch = self.emit_jump(op.JUMP_IF_FALSE)

            if clause.alias is not None:
                pass

            self.gen(clause.body)
            self.emit_op(op.POP_EXCEPT)
            end_patches.append(self.emit_jump(op.JUMP))

            if next_handler_patch is not None and i < len(node.excepts) - 1:
                setup_at = next_handler_patch
                next_handler_patch = None
            elif next_handler_patch is not None:
                end_patches.append(next_handler_patch)

        if node.finally_ is not None:
            self.gen(node.finally_)

        for p in end_patches:
            self.patch_jump(p)

    def _gen_try_finally_only(self, node):
        self.gen(node.body)
        if node.finally_ is not None:
            self.gen(node.finally_)
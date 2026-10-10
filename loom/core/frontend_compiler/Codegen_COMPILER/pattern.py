"""Pattern matching and switch code generation for LOOM"""

from Codegen_COMPILER import opcodes as op
from AstLOOM import (
    Match, Switch,
    PatternLiteral, PatternIdent, PatternWildcard,
    PatternOr, PatternCall,
    Identifier, Literal,
)

class PatternMixin:

    def gen_Match(self, node):
        self.set_line(node.line)

        end_patches = []

        self.gen(node.subject)

        for i, arm in enumerate(node.arms):
            is_last = (i == len(node.arms) - 1)

            if isinstance(arm.pattern, PatternWildcard) and is_last:
                self._gen_match_wildcard_arm(arm)
                break

            self.emit_op(op.DUP)
            self._gen_pattern_check(arm.pattern)
            if arm.guard is not None:
                pass

            skip_patch = self.emit_jump(op.JUMP_IF_FALSE)

            self.emit_op(op.POP)
            self.gen(arm.body)
            end_patches.append(self.emit_jump(op.JUMP))

            self.patch_jump(skip_patch)

        self.emit_op(op.POP)

        for p in end_patches:
            self.patch_jump(p)

    def _gen_pattern_check(self, pattern):
        if isinstance(pattern, PatternWildcard):
            self.emit_op(op.POP)
            self.emit_op(op.PUSH_TRUE)
            return

        if isinstance(pattern, PatternLiteral):
            self._gen_literal_push(pattern.value, pattern.lit_type)
            self.emit_op(op.CMP_EQ)
            return

        if isinstance(pattern, PatternIdent):
            self.emit_op(op.POP)
            self.emit_op(op.PUSH_TRUE)
            return

        if isinstance(pattern, PatternOr):
            true_patches = []
            for i, sub in enumerate(pattern.parts):
                self.emit_op(op.DUP)
                self._gen_pattern_check(sub)
                true_patches.append(self.emit_jump(op.JUMP_IF_TRUE))
                self.emit_op(op.POP)
                self.emit_op(op.POP)
            self.emit_op(op.POP)
            self.emit_op(op.PUSH_FALSE)
            after_false = self.emit_jump(op.JUMP)
            for p in true_patches:
                self.patch_jump(p)
            self.emit_op(op.POP)
            self.emit_op(op.PUSH_TRUE)
            self.patch_jump(after_false)
            return

        if isinstance(pattern, PatternCall):
            self.emit_op(op.POP)
            self.emit_op(op.PUSH_TRUE)
            return

        raise self.error(
            f"unsupported pattern: {type(pattern).__name__}", pattern)

    def _gen_match_wildcard_arm(self, arm):
        self.emit_op(op.POP)
        self.gen(arm.body)

    def _gen_literal_push(self, value, lit_type):
        if lit_type == 'int':
            self.emit_op(op.PUSH_INT)
            self.emit_i64(value)
        elif lit_type == 'double':
            self.emit_op(op.PUSH_DOUBLE)
            self.emit_f64(value)
        elif lit_type == 'str':
            idx = self.module.pool.add_str(value)
            self.emit_op(op.PUSH_STR)
            self.emit_u16(idx)
        elif lit_type == 'char':
            cp = ord(value) if value else 0
            self.emit_op(op.PUSH_CHAR)
            self.emit_u8(cp & 0xFF)
        elif lit_type == 'bool':
            self.emit_op(op.PUSH_TRUE if value else op.PUSH_FALSE)
        else:
            raise self.error(f"unknown literal type: {lit_type!r}")

    def gen_Switch(self, node):
        self.set_line(node.line)

        end_patches = []
        self.gen(node.subject)

        for case in node.cases:
            self.emit_op(op.DUP)
            self.gen(case.value)
            self.emit_op(op.CMP_EQ)
            skip_patch = self.emit_jump(op.JUMP_IF_FALSE)

            self.emit_op(op.POP)
            for stmt in case.body:
                self.gen(stmt)
            end_patches.append(self.emit_jump(op.JUMP))

            self.patch_jump(skip_patch)

        if node.default is not None:
            self.emit_op(op.POP)
            for stmt in node.default.body:
                self.gen(stmt)
        else:
            self.emit_op(op.POP)

        for p in end_patches:
            self.patch_jump(p)
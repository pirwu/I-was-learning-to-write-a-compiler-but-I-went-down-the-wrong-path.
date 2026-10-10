"""Expression for LPL."""

from Codegen_COMPILER import opcodes as op
from Codegen_COMPILER.carcass import CONST_INT, CONST_DOUBLE, CONST_STR

from AstLOOM import (
    Literal, Identifier, Binary, Unary, Assign, Call,
    Index,
    Member,
    ArrayLiteral, DictLiteral,
    ConsoleCall, InputCall,
)

class ExprMixin:

    def gen_Literal(self, node):
        t = node.lit_type

        if t == 'int':
            self.emit_op(op.PUSH_INT)
            self.emit_i64(node.value)

        elif t == 'double':
            self.emit_op(op.PUSH_DOUBLE)
            self.emit_f64(node.value)

        elif t == 'str':
            idx = self.module.pool.add_str(node.value)
            self.emit_op(op.PUSH_STR)
            self.emit_u16(idx)

        elif t == 'char':
            cp = ord(node.value) if node.value else 0
            self.emit_op(op.PUSH_CHAR)
            self.emit_u8(cp & 0xFF)

        elif t == 'bool':
            self.emit_op(op.PUSH_TRUE if node.value else op.PUSH_FALSE)

        else:
            raise self.error(f"unknown literal type: {t!r}", node)

    def gen_Identifier(self, node):
        binding = node.binding
        if binding == 'local':
            self.emit_op(op.LOAD_LOCAL)
            self.emit_u8(node.slot)
        elif binding == 'global':
            self.emit_op(op.LOAD_GLOBAL)
            self.emit_u16(node.slot)
        elif binding == 'upvalue':
            self.emit_op(op.LOAD_UPVALUE)
            self.emit_u16(node.upvalue_index)
        else:
            raise self.error(
                f"identifier {node.name!r} was not resolved "
                f"(binding={binding!r})", node)

    def gen_Binary(self, node):
        if node.op in ('&&', '||'):
            return self.gen_logical(node)

        self.set_line(node.line)
        self.gen(node.left)
        self.gen(node.right)
        self.emit_binop(node.op, node)

    def emit_binop(self, op_str, node):
        table = {
            '+':  op.ADD,
            '-':  op.SUB,
            '*':  op.MUL,
            '/':  op.DIV,
            '//': op.IDIV,
            '%':  op.MOD,
            '**': op.POW,
            '&':  op.BIT_AND,
            '|':  op.BIT_OR,
            '^':  op.BIT_XOR,
            '<<': op.LSHIFT,
            '>>': op.RSHIFT,
            '==': op.CMP_EQ,
            '!=': op.CMP_NEQ,
            '<':  op.CMP_LT,
            '>':  op.CMP_GT,
            '<=': op.CMP_LE,
            '>=': op.CMP_GE,
        }
        code = table.get(op_str)
        if code is None:
            raise self.error(f"unknown binary operator {op_str!r}", node)
        self.emit_op(code)

    def gen_logical(self, node):
        self.set_line(node.line)

        if node.op == '&&':
            self.gen(node.left)
            patch = self.emit_jump(op.JUMP_IF_FALSE)
            self.emit_op(op.POP)
            self.gen(node.right)
            self.patch_jump(patch)

        elif node.op == '||':
            self.gen(node.left)
            patch = self.emit_jump(op.JUMP_IF_TRUE)
            self.emit_op(op.POP)
            self.gen(node.right)
            self.patch_jump(patch)

        else:
            raise self.error(f"unknown logical operator {node.op!r}", node)

    def gen_Unary(self, node):
        self.set_line(node.line)
        self.gen(node.operand)
        if node.op == '-':
            self.emit_op(op.NEG)
        elif node.op == '!':
            self.emit_op(op.LOGIC_NOT)
        elif node.op == '~':
            self.emit_op(op.BIT_NOT)
        else:
            raise self.error(f"unknown unary operator {node.op!r}", node)

    def gen_Assign(self, node):
        self.set_line(node.line)
        target = node.target
        if isinstance(target, Identifier):
            self._gen_assign_ident(target, node)
        elif isinstance(target, Index):
            self._gen_assign_index(target, node)
        elif isinstance(target, Member):
            self._gen_assign_member(target, node)
        else:
            raise self.error(f"unsupported assignment target: {type(target).__name__}", node)

    def _gen_assign_ident(self, target, node):
        op_str = node.op
        if op_str == '=':
            self.gen(node.value)
            self.emit_op(op.DUP)
            self.emit_store_ident(target)
        else:
            binop = op_str[:-1]
            self.gen(target)
            self.gen(node.value)
            self.emit_binop(binop, node)
            self.emit_op(op.DUP)
            self.emit_store_ident(target)

    def _gen_assign_index(self, target, node):
        if node.op != '=':
            raise self.error("compound assignment to index is not supported yet", node)
                
        self.gen(target.obj)
        self.gen(target.index)
        self.gen(node.value)
        self.emit_op(op.STORE_INDEX)
        self.emit_op(op.PUSH_NULL)

    def _gen_assign_ident(self, target, node):
        op_str = node.op
        if op_str == '=':
            self.gen(node.value)
            self.emit_op(op.DUP)
            self.emit_store_ident(target)
        else:
            binop = op_str[:-1]
            self.gen(target)
            self.gen(node.value)
            self.emit_binop(binop, node)
            self.emit_op(op.DUP)
            self.emit_store_ident(target)

    def _gen_assign_index(self, target, node):
        if node.op != '=':
            raise self.error("compound assignment to index is not supported yet", node)
        
        self.gen(target.obj)
        self.gen(target.index)
        self.gen(node.value)
        self.emit_op(op.STORE_INDEX)
        self.emit_op(op.PUSH_NULL)

    def emit_store_ident(self, ident):
        
        binding = ident.binding
        if binding == 'local':
            self.emit_op(op.STORE_LOCAL)
            self.emit_u8(ident.slot)
        elif binding == 'global':
            self.emit_op(op.STORE_GLOBAL)
            self.emit_u16(ident.slot)
        elif binding == 'upvalue':
            self.emit_op(op.STORE_UPVALUE)
            self.emit_u16(ident.upvalue_index)
        else:
            raise self.error(
                f"identifier {ident.name!r} was not resolved", ident)

    def gen_Call(self, node):
        self.set_line(node.line)

        from AstLOOM import SuperExpr
        if isinstance(node.callee, SuperExpr) and node.callee.method is not None:
            for arg in node.args:
                self.gen(arg)
            name_idx = self.module.pool.add_name(node.callee.method)
            self.emit_op(op.CALL_SUPER)
            self.emit_u16(name_idx)
            self.emit_u8(len(node.args))
            return

        self.gen(node.callee)
        for arg in node.args:
            self.gen(arg)
        self.emit_op(op.CALL)
        self.emit_u8(len(node.args))

    def gen_ConsoleCall(self, node):
        self.set_line(node.line)

        method = node.method
        if method in ("write", "writeln"):
            newline = (method == "writeln")
        else:
            raise self.error(
                f"unknown console method: {method!r} "
                f"(expected 'write' or 'writeln')", node)

        if not node.args:
            idx = self.module.pool.add_str("")
            self.emit_op(op.PUSH_STR)
            self.emit_u16(idx)
            self.emit_op(op.CONSOLE_WRITELN if newline else op.CONSOLE_WRITE)
            return

        for i, arg in enumerate(node.args):
            self.gen(arg)
            is_last = (i == len(node.args) - 1)
            if is_last and newline:
                self.emit_op(op.CONSOLE_WRITELN)
            elif is_last:
                self.emit_op(op.CONSOLE_WRITE)
            else:
                self.emit_op(op.CONSOLE_WRITE)

    def gen_InputCall(self, node):
        self.set_line(node.line)

        if node.prompt is not None:
            self.gen(node.prompt)
            self.emit_op(op.INPUT_READ)
            self.emit_u8(1)
        else:
            self.emit_op(op.INPUT_READ)
            self.emit_u8(0)
            
    def gen_Ternary(self, node):
        self.set_line(node.line)

        self.gen(node.cond)
        else_patch = self.emit_jump(op.JUMP_IF_FALSE)

        self.gen(node.then)
        end_patch = self.emit_jump(op.JUMP)

        self.patch_jump(else_patch)
        self.gen(node.else_)
        self.patch_jump(end_patch)
        
    def gen_PreIncDec(self, node):
        self.set_line(node.line)
        self._gen_incdec(node.operand, node.op, prefix=True, node=node)

    def gen_PostIncDec(self, node):
        self.set_line(node.line)
        self._gen_incdec(node.operand, node.op, prefix=False, node=node)

    def _gen_incdec(self, target, op_str, prefix, node):
        from AstLOOM import Identifier
        if not isinstance(target, Identifier):
            raise self.error(
                f"'{op_str}' target must be an identifier for now "
                f"(member/index support pending)", node)

        is_inc = (op_str == '++')

        self.gen(target)

        if prefix:
            self.emit_op(op.PUSH_INT)
            self.emit_i64(1)
            self.emit_op(op.ADD if is_inc else op.SUB)
            self.emit_op(op.DUP)
            self.emit_store_ident(target)
        else:
            self.emit_op(op.DUP)
            self.emit_op(op.PUSH_INT)
            self.emit_i64(1)
            self.emit_op(op.ADD if is_inc else op.SUB)
            self.emit_store_ident(target)
            
    def gen_ArrayLiteral(self, node):
        self.set_line(node.line)
        for item in node.items:
            self.gen(item)
        self.emit_op(op.NEW_ARRAY)
        self.emit_u16(len(node.items))

    def gen_DictLiteral(self, node):
        self.set_line(node.line)
        for key, value in node.entries:
            self.gen(key)
            self.gen(value)
        self.emit_op(op.NEW_DICT)
        self.emit_u16(len(node.entries))
        
    def gen_Index(self, node):
        self.set_line(node.line)
        self.gen(node.obj)
        self.gen(node.index)
        self.emit_op(op.LOAD_INDEX)
        
    def gen_RangeExpr(self, node):
        self.set_line(node.line)
        self.gen(node.start)
        self.gen(node.end)
        if node.inclusive:
            self.emit_op(op.BUILD_RANGE_INCL)
        else:
            self.emit_op(op.BUILD_RANGE)
        self.emit_u8(0)

    def gen_ArrayLiteral(self, node):
        self.set_line(node.line)
        for item in node.items:
            self.gen(item)
        self.emit_op(op.NEW_ARRAY)
        self.emit_u16(len(node.items))

    def gen_DictLiteral(self, node):
        self.set_line(node.line)
        for key, value in node.entries:
            self.gen(key)
            self.gen(value)
        self.emit_op(op.NEW_DICT)
        self.emit_u16(len(node.entries))

    def gen_Index(self, node):
        self.set_line(node.line)
        self.gen(node.obj)
        self.gen(node.index)
        self.emit_op(op.LOAD_INDEX)
        
    def gen_RangeExpr(self, node):
        self.set_line(node.line)
        self.gen(node.start)
        self.gen(node.end)
        if node.inclusive:
            self.emit_op(op.BUILD_RANGE_INCL)
        else:
            self.emit_op(op.BUILD_RANGE)
        self.emit_u8(0)

    def gen_RangeCall(self, node):
        self.set_line(node.line)
        args = node.args
        if len(args) == 0:
            raise self.error("range() requires at least one argument", node)
        if len(args) == 1:
            self.emit_op(op.PUSH_INT)
            self.emit_i64(0)
            self.gen(args[0])
        elif len(args) == 2:
            self.gen(args[0])
            self.gen(args[1])
        elif len(args) == 3:
            self.gen(args[0])
            self.gen(args[1])
            self.gen(args[2])
            self.emit_op(op.BUILD_RANGE)
            self.emit_u8(0)
            return
        else:
            raise self.error("range() takes 1, 2, or 3 arguments", node)
        self.emit_op(op.PUSH_INT)
        self.emit_i64(1)
        self.emit_op(op.BUILD_RANGE)
        self.emit_u8(0)

    def gen_EnumerateExpr(self, node):
        self.set_line(node.line)
        self.gen(node.inner)
        self.emit_op(op.BUILD_ENUMERATE)

    def gen_ZipExpr(self, node):
        self.set_line(node.line)
        for part in node.parts:
            self.gen(part)
        self.emit_op(op.BUILD_ZIP)
        self.emit_u8(len(node.parts))

    def gen_ReversedExpr(self, node):
        self.set_line(node.line)
        self.gen(node.inner)
        self.emit_op(op.BUILD_REVERSED)
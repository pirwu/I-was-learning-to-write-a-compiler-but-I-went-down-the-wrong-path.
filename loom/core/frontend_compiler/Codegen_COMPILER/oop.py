"""OOP code generation for LOOM."""

from Codegen_COMPILER import opcodes as op
from Codegen_COMPILER.carcass import (
    FunctionBuffer,
    ClassEntry,
)

from AstLOOM import (
    ClassDecl, InterfaceDecl, StructDecl, RecordDecl,
    ClassMember, Constructor, Destructor,
    VarDecl, FuncDecl, Identifier,
    NewExpr, ThisExpr, SuperExpr, Member, Assign,
)

class OOPMixin:

    def gen_ClassDecl(self, node):
        self.set_line(node.line)

        fields = []
        methods = []

        for member in node.members:
            inner = member.inner
            if inner is None:
                continue

            if isinstance(inner, VarDecl):
                fields.append(inner.name)
                continue

            if isinstance(inner, FuncDecl):
                fbuf = self._make_method_buffer(
                    f"{node.name}.{inner.name}", inner)
                idx = self.module.functions.add(fbuf)
                methods.append((inner.name, idx))
                continue

            if isinstance(inner, Constructor):
                fbuf = self._make_constructor_buffer(
                    f"{node.name}.constructor", inner)
                idx = self.module.functions.add(fbuf)
                methods.append(("constructor", idx))
                continue

            if isinstance(inner, Destructor):
                fbuf = self._make_destructor_buffer(
                    f"{node.name}.destructor", inner)
                idx = self.module.functions.add(fbuf)
                methods.append(("destructor", idx))
                continue

        super_name = None
        if node.extends is not None:
            super_name = getattr(node.extends, "name", None)
            
        flags = 0
        if node.is_abstract:
            flags |= 0x01

        entry = ClassEntry(
            name=node.name,
            super_name=super_name,
            flags=flags,
            fields=fields,
            methods=methods,
        )
        self.module.classes.add(entry)

        self.emit_op(op.PUSH_NULL)
        self.emit_op(op.STORE_GLOBAL)
        self.emit_u16(node.global_index)

    def gen_InterfaceDecl(self, node):
        self.set_line(node.line)

        methods = []
        for member in node.members:
            inner = member.inner
            if isinstance(inner, FuncDecl):
                methods.append((inner.name, 0))

        entry = ClassEntry(
            name=node.name,
            super_name=None,
            flags=0x02,
            fields=[],
            methods=methods,
        )
        self.module.classes.add(entry)

        self.emit_op(op.PUSH_NULL)
        self.emit_op(op.STORE_GLOBAL)
        self.emit_u16(node.global_index)

    def gen_StructDecl(self, node):
        self.set_line(node.line)

        fields = []
        for member in node.members:
            inner = member.inner
            if isinstance(inner, VarDecl):
                fields.append(inner.name)

        entry = ClassEntry(
            name=node.name,
            super_name=None,
            flags=0x04,
            fields=fields,
            methods=[],
        )
        self.module.classes.add(entry)

        self.emit_op(op.PUSH_NULL)
        self.emit_op(op.STORE_GLOBAL)
        self.emit_u16(node.global_index)

    def gen_RecordDecl(self, node):
        self.set_line(node.line)

        fields = [p.name for p in node.params]

        entry = ClassEntry(
            name=node.name,
            super_name=None,
            flags=0x08,
            fields=fields,
            methods=[],
        )
        self.module.classes.add(entry)

        self.emit_op(op.PUSH_NULL)
        self.emit_op(op.STORE_GLOBAL)
        self.emit_u16(node.global_index)

    def _make_constructor_buffer(self, name, node):
        buf = FunctionBuffer(
            name=name,
            arity=len(node.params),
            locals_count=getattr(node, "frame_size", 0) or 0,
            upvalues=getattr(node, "upvalues", []) or [],
        )
        self._emit_method_body(buf, node.params, node.body)
        return buf

    def _make_destructor_buffer(self, name, node):
        buf = FunctionBuffer(
            name=name,
            arity=0,
            locals_count=getattr(node, "frame_size", 0) or 0,
            upvalues=getattr(node, "upvalues", []) or [],
        )
        self._emit_method_body(buf, [], node.body)
        return buf

    def _emit_method_body(self, buf, params, body):
        prev_func = self.current_func
        self.current_func = buf

        if body is not None:
            self.gen(body)

        self.emit_op(op.RETURN_VOID)

        self.current_func = prev_func

    def gen_NewExpr(self, node):
        self.set_line(node.line)

        for arg in node.args:
            self.gen(arg)

        name_idx = self.module.pool.add_name(node.type_name)
        self.emit_op(op.NEW_OBJECT)
        self.emit_u16(name_idx)
        self.emit_op(op.INVOKE_CTOR)
        self.emit_u8(len(node.args))

    def gen_ThisExpr(self, node):
        self.set_line(node.line)
        self.emit_op(op.LOAD_SELF)

    def gen_SuperExpr(self, node):
        self.set_line(node.line)
        self.emit_op(op.LOAD_SUPER)

    def gen_Member(self, node):
        self.set_line(node.line)
        self.gen(node.obj)
        name_idx = self.module.pool.add_name(node.name)
        self.emit_op(op.LOAD_ATTR)
        self.emit_u16(name_idx)

    def _gen_assign_member(self, target, node):
        if node.op != '=':
            raise self.error(
                "compound assignment to member is not supported yet", node)
        self.gen(target.obj)
        self.gen(node.value)
        name_idx = self.module.pool.add_name(target.name)
        self.emit_op(op.STORE_ATTR)
        self.emit_u16(name_idx)
        self.emit_op(op.PUSH_NULL)
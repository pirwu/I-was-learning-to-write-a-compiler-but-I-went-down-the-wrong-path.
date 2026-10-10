"""Resolver for LOOM — name resolution, slot allocation, upvalue capture."""

import dataclasses

from AstLOOM import (
    Program, Block,
    VarDecl, Param, Identifier,
    FuncDecl, LambdaExpr, Constructor, Destructor,
    ThreadDecl, ProcessDecl, CoroutineDecl,
    ClassDecl, InterfaceDecl, StructDecl, RecordDecl,
    ClassMember,
    ModuleDecl, NamespaceDecl,
    ExportStmt,
    While, DoWhile, ForIn, ForCStyle,
    Match, MatchArm,
    PatternIdent, PatternOr, PatternCall, PatternWildcard,
    Try, ExceptClause,
    Break, Continue, Return,
    UpvalueDesc,
)
from ErrorLOOM import SemanticError

class Scope:

    def __init__(self, parent, kind, func_node=None):
        self.parent = parent
        self.kind = kind
        self.func_node = func_node
        self.names = {}

        if kind in ("global", "function"):
            self._slot_owner = self
            self._next_local_slot = 0
        else:
            self._slot_owner = parent._slot_owner

        self.globals = {}
        self.next_global_index = 0
        self.upvalues = []
        self.upvalue_names = {}

        self.loop_depth = 0
        self.in_function = (kind != "global")

    @property
    def next_local_slot(self):
        return self._slot_owner._next_local_slot

    @next_local_slot.setter
    def next_local_slot(self, value):
        self._slot_owner._next_local_slot = value

    def declare_local(self, name, line=0, col=0):
        if name in self.names:
            raise SemanticError(
                f"'{name}' is already declared in this scope", line, col)
        slot = self._slot_owner._next_local_slot
        self._slot_owner._next_local_slot += 1
        self.names[name] = slot
        return slot

    def lookup_local(self, name):
        return self.names.get(name)

    def declare_global(self, name, line=0, col=0):
        s = self
        while s.parent is not None:
            s = s.parent
        if name in s.globals:
            raise SemanticError(
                f"global '{name}' is already declared", line, col)
        idx = s.next_global_index
        s.next_global_index += 1
        s.globals[name] = idx
        return idx

    def lookup_global(self, name):
        s = self
        while s is not None:
            if s.kind == "global":
                return s.globals.get(name)
            s = s.parent
        return None

    def resolve_upvalue(self, name):
        if self.parent is None:
            return -1

        parent = self.parent

        slot = parent.lookup_local(name)
        if slot is not None:
            return self._add_upvalue(is_local=True, index=slot, name=name)

        if parent.kind == "function":
            parent_idx = parent.resolve_upvalue(name)
            if parent_idx >= 0:
                return self._add_upvalue(
                    is_local=False, index=parent_idx, name=name)
        return -1

    def _add_upvalue(self, is_local, index, name):
        if name in self.upvalue_names:
            return self.upvalue_names[name]
        idx = len(self.upvalues)
        self.upvalues.append(
            UpvalueDesc(0, 0, is_local=is_local, index=index, name=name))
        self.upvalue_names[name] = idx
        return idx


class Resolver:

    def __init__(self):
        self.scope = None

    def resolve(self, program):
        self.scope = Scope(None, "global", program)

        for item in program.items:
            self._declare_top_level(item)

        for item in program.items:
            self.visit(item)

        program.globals = list(self.scope.globals.keys())
        program.locals_count = self.scope.next_local_slot
        return program

    def _declare_top_level(self, node):
        if isinstance(node, ExportStmt):
            inner = node.inner
            if inner is not None and not isinstance(inner, Identifier):
                self._declare_top_level(inner)
            return

        if isinstance(node, VarDecl):
            node.global_index = self.scope.declare_global(
                node.name, node.line, node.col)
            return

        if isinstance(node, (FuncDecl, ClassDecl, InterfaceDecl,
                             StructDecl, RecordDecl)):
            node.global_index = self.scope.declare_global(
                node.name, node.line, node.col)
            return

    def visit(self, node):
        if node is None:
            return
        method = getattr(self, "visit_" + type(node).__name__, None)
        if method is not None:
            method(node)
        else:
            self.generic_visit(node)

    def generic_visit(self, node):
        for f in dataclasses.fields(node):
            value = getattr(node, f.name)
            self._visit_value(value)

    def _visit_value(self, value):
        if value is None:
            return
        if isinstance(value, list):
            for item in value:
                self._visit_value(item)
        elif isinstance(value, tuple):
            for item in value:
                self._visit_value(item)
        elif hasattr(value, "__dataclass_fields__") and hasattr(value, "line"):
            self.visit(value)

    def visit_Block(self, node):
        prev = self.scope
        self.scope = Scope(prev, "block", prev.func_node)
        for stmt in node.stmts:
            self.visit(stmt)
        self.scope = prev

    def visit_VarDecl(self, node):
        if node.init is not None:
            self.visit(node.init)

        if self.scope.kind == "global" and self.scope.parent is None:
            pass
        else:
            node.slot = self.scope.declare_local(
                node.name, node.line, node.col)
            node.global_index = -1

        if node.type_ is not None:
            self.visit(node.type_)

    def visit_Param(self, node):
        node.slot = self.scope.declare_local(
            node.name, node.line, node.col)
        if node.type_ is not None:
            self.visit(node.type_)
        if node.default is not None:
            self.visit(node.default)

    def visit_Identifier(self, node):
        name = node.name

        s = self.scope
        while s is not None:
            slot = s.lookup_local(name)
            if slot is not None:
                node.binding = "local"
                node.slot = slot
                return
            if s.kind in ("function", "global"):
                break
            s = s.parent

        if self.scope.in_function:
            idx = self.scope.resolve_upvalue(name)
            if idx >= 0:
                node.binding = "upvalue"
                node.upvalue_index = idx
                return

        s = self.scope
        while s is not None:
            if s.kind == "global":
                gidx = s.globals.get(name)
                if gidx is not None:
                    node.binding = "global"
                    node.slot = gidx
                    return
                break
            s = s.parent

        raise SemanticError(f"undefined name '{name}'", node.line, node.col)

    def visit_FuncDecl(self, node):
        self._visit_function_like(node, node.params, node.body)

    def visit_LambdaExpr(self, node):
        self._visit_function_like(node, node.params, node.body)

    def visit_Constructor(self, node):
        self._visit_function_like(node, node.params, node.body)

    def visit_Destructor(self, node):
        self._visit_function_like(node, [], node.body)

    def visit_ThreadDecl(self, node):
        self._visit_function_like(node, node.params, node.body)

    def visit_ProcessDecl(self, node):
        self._visit_function_like(node, node.params, node.body)

    def visit_CoroutineDecl(self, node):
        self._visit_function_like(node, node.params, node.body)

    def _visit_function_like(self, node, params, body):
        prev = self.scope
        fn_scope = Scope(prev, "function", node)
        self.scope = fn_scope

        for p in params:
            self.visit(p)

        if body is None:
            pass
        elif isinstance(body, Block):
            for stmt in body.stmts:
                self.visit(stmt)
        else:
            self.visit(body)

        node.frame_size = fn_scope.next_local_slot
        node.upvalues = fn_scope.upvalues
        self.scope = prev

    def visit_If(self, node):
        self.visit(node.cond)
        self.visit(node.then)
        for cond, blk in node.elifs:
            self.visit(cond)
            self.visit(blk)
        if node.else_ is not None:
            self.visit(node.else_)

    def visit_While(self, node):
        self.visit(node.cond)
        prev_depth = self.scope.loop_depth
        self.scope.loop_depth += 1
        self.visit(node.body)
        self.scope.loop_depth = prev_depth

    def visit_DoWhile(self, node):
        prev_depth = self.scope.loop_depth
        self.scope.loop_depth += 1
        self.visit(node.body)
        self.scope.loop_depth = prev_depth
        self.visit(node.cond)

    def visit_ForIn(self, node):
        self.visit(node.iterable)

        prev = self.scope
        inner = Scope(prev, "block", prev.func_node)
        inner.loop_depth = prev.loop_depth + 1
        self.scope = inner

        node.var_slot = inner.declare_local(node.var, node.line, node.col)

        self.visit(node.body)
        self.scope = prev

    def visit_ForCStyle(self, node):
        prev = self.scope
        inner = Scope(prev, "block", prev.func_node)
        inner.loop_depth = prev.loop_depth + 1
        self.scope = inner

        if node.init is not None:
            self.visit(node.init)
        if node.cond is not None:
            self.visit(node.cond)
        if node.step is not None:
            self.visit(node.step)
        self.visit(node.body)

        self.scope = prev

    def visit_Break(self, node):
        if self.scope.loop_depth == 0:
            raise SemanticError("'break' outside of a loop", node.line, node.col)

    def visit_Continue(self, node):
        if self.scope.loop_depth == 0:
            raise SemanticError("'continue' outside of a loop", node.line, node.col)

    def visit_Return(self, node):
        if not self.scope.in_function:
            raise SemanticError("'return' outside of a function", node.line, node.col)
        if node.value is not None:
            self.visit(node.value)

    def visit_Match(self, node):
        self.visit(node.subject)
        for arm in node.arms:
            self._visit_match_arm(arm)

    def _visit_match_arm(self, arm):
        prev = self.scope
        self.scope = Scope(prev, "block", prev.func_node)

        self._declare_pattern(arm.pattern)

        if arm.guard is not None:
            self.visit(arm.guard)

        self.visit(arm.body)
        self.scope = prev

    def _declare_pattern(self, pattern):
        if pattern is None:
            return
        if isinstance(pattern, PatternIdent):
            if pattern.name == "_":
                return
            if pattern.name not in self.scope.names:
                self.scope.declare_local(
                    pattern.name, pattern.line, pattern.col)
        elif isinstance(pattern, PatternOr):
            for p in pattern.parts:
                self._declare_pattern(p)
        elif isinstance(pattern, PatternCall):
            for p in pattern.args:
                self._declare_pattern(p)

    def visit_Try(self, node):
        self.visit(node.body)
        for clause in node.excepts:
            self._visit_except(clause)
        if node.finally_ is not None:
            self.visit(node.finally_)

    def _visit_except(self, clause):
        prev = self.scope
        self.scope = Scope(prev, "block", prev.func_node)

        if clause.exc_type is not None:
            self.visit(clause.exc_type)

        if clause.alias is not None:
            self.scope.declare_local(
                clause.alias, clause.line, clause.col)

        self.visit(clause.body)
        self.scope = prev

    def visit_ClassDecl(self, node):
        if node.extends is not None:
            self.visit(node.extends)
        for iface in node.implements:
            self.visit(iface)
        for member in node.members:
            self._visit_class_member(member)

    def visit_InterfaceDecl(self, node):
        for member in node.members:
            self._visit_class_member(member)

    def visit_StructDecl(self, node):
        for member in node.members:
            self._visit_class_member(member)

    def visit_RecordDecl(self, node):
        prev = self.scope
        self.scope = Scope(prev, "block", prev.func_node)
        for p in node.params:
            self.visit(p)
        self.scope = prev

    def _visit_class_member(self, member):
        inner = member.inner
        if inner is None:
            return

        if isinstance(inner, VarDecl):
            if inner.type_ is not None:
                self.visit(inner.type_)
            if inner.init is not None:
                self.visit(inner.init)
            return

        if isinstance(inner, (FuncDecl, Constructor, Destructor)):
            self._visit_method(inner)
            return

        self.visit(inner)

    def _visit_method(self, node):
        prev = self.scope
        fn_scope = Scope(prev, "function", node)
        fn_scope.declare_local("this", node.line, node.col)
        self.scope = fn_scope

        params = getattr(node, "params", []) or []
        for p in params:
            self.visit(p)

        body = getattr(node, "body", None)
        if body is None:
            pass
        elif isinstance(body, Block):
            for stmt in body.stmts:
                self.visit(stmt)
        else:
            self.visit(body)

        node.frame_size = fn_scope.next_local_slot
        node.upvalues = fn_scope.upvalues
        self.scope = prev
    
    def visit_ModuleDecl(self, node):
        if node.body is not None:
            self.visit(node.body)

    def visit_NamespaceDecl(self, node):
        if node.body is not None:
            self.visit(node.body)

    def visit_ExportStmt(self, node):
        if node.inner is not None:
            self.visit(node.inner)
            
    def visit_ImportStmt(self, node):
        if node.from_path is None and node.path:
            name = node.alias if node.alias is not None else node.path[-1]
            self.scope.declare_global(name, node.line, node.col)
            return

        if node.names is not None:
            for name, alias in node.names:
                declared = alias if alias is not None else name
                self.scope.declare_global(declared, node.line, node.col)
            return
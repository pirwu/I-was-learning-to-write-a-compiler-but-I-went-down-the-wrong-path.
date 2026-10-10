"""Module system for LOOM"""

from Codegen_COMPILER import opcodes as op
from AstLOOM import (
    ImportStmt, ExportStmt,
    ModuleDecl, NamespaceDecl,
)

class ModuleMixin:

    def gen_ImportStmt(self, node):
        self.set_line(node.line)

        if node.from_path is not None:
            self._gen_from_import(node)
            return

        path_name = "::".join(node.path)
        path_idx = self.module.pool.add_name(path_name)
        self.emit_op(op.IMPORT_MODULE)
        self.emit_u16(path_idx)

        if node.alias is not None:
            alias_idx = self.module.pool.add_name(node.alias)
            self.emit_op(op.IMPORT_AS)
            self.emit_u16(path_idx)
            self.emit_u16(alias_idx)

    def _gen_from_import(self, node):
        path_name = "::".join(node.from_path)
        path_idx = self.module.pool.add_name(path_name)

        if node.star:
            self.emit_op(op.IMPORT_ALL)
            self.emit_u16(path_idx)
            return

        for name, alias in node.names:
            name_idx = self.module.pool.add_name(name)
            self.emit_op(op.IMPORT_FROM)
            self.emit_u16(path_idx)
            self.emit_u16(name_idx)
            if alias is not None:
                alias_idx = self.module.pool.add_name(alias)
                self.emit_op(op.IMPORT_AS)
                self.emit_u16(name_idx)
                self.emit_u16(alias_idx)

    def gen_ExportStmt(self, node):
        self.set_line(node.line)

        from AstLOOM import Identifier

        if isinstance(node.inner, Identifier):
            name_idx = self.module.pool.add_name(node.inner.name)
            self.emit_op(op.EXPORT_SYMBOL)
            self.emit_u16(name_idx)
            return

        self.gen(node.inner)

        name = getattr(node.inner, "name", None)
        if name is not None:
            name_idx = self.module.pool.add_name(name)
            self.emit_op(op.EXPORT_SYMBOL)
            self.emit_u16(name_idx)

    def gen_ModuleDecl(self, node):
        self.set_line(node.line)
        name_idx = self.module.pool.add_name(node.name)
        self.emit_op(op.ENTER_NAMESPACE)
        self.emit_u16(name_idx)

        if node.body is not None:
            self.gen(node.body)

        self.emit_op(op.EXIT_NAMESPACE)

    def gen_NamespaceDecl(self, node):
        self.set_line(node.line)
        name_idx = self.module.pool.add_name(node.name)
        self.emit_op(op.ENTER_NAMESPACE)
        self.emit_u16(name_idx)

        if node.body is not None:
            self.gen(node.body)

        self.emit_op(op.EXIT_NAMESPACE)
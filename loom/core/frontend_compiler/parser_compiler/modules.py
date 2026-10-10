"""Module-system parsing for LPL"""

from AstLOOM import (
    PackageDecl,
    ImportStmt,
    ExportStmt,
    ModuleDecl,
    NamespaceDecl,
    Identifier,
)

class ModuleMixin:

    def parse_package_decl(self):
        kw = self.ts.expect('PACKAGE')
        path = self._parse_module_path()
        self.ts.expect('SEMICOLON')
        return PackageDecl(kw.line, kw.col, name="::".join(path))

    def parse_import(self):
        kw = self.ts.expect('IMPORT')
        path = self._parse_module_path()

        alias = None
        if self.ts.at('AS'):
            self.ts.next()
            alias = self.ts.expect('ID').value

        self.ts.expect('SEMICOLON')
        return ImportStmt(
            kw.line, kw.col,
            path=path,
            alias=alias,
        )

    def parse_from_import(self):
        kw = self.ts.expect('FROM')
        path = self._parse_module_path()

        self.ts.expect('IMPORT')

        if self.ts.at('MUL'):
            self.ts.next()
            self.ts.expect('SEMICOLON')
            return ImportStmt(
                kw.line, kw.col,
                from_path=path,
                names=None,
                star=True)

        names = [self._parse_import_name()]
        while self.ts.at('COMMA'):
            self.ts.next()
            names.append(self._parse_import_name())

        self.ts.expect('SEMICOLON')
        return ImportStmt(
            kw.line, kw.col,
            from_path=path,
            names=names,
            star=False)

    def _parse_import_name(self):
        name = self.ts.expect('ID').value
        alias = None
        if self.ts.at('AS'):
            self.ts.next()
            alias = self.ts.expect('ID').value
        return (name, alias)

    def parse_export(self):
        kw = self.ts.expect('EXPORT')

        t = self.ts.peek()

        if t.type in ('FUNCTION', 'CLASS', 'INTERFACE', 'STRUCT', 'RECORD',
                      'VAR', 'CONST', 'MODULE', 'NAMESPACE', 'ABSTRACT',
                      'ASYNC', 'AT'):
            inner = self.parse_stmt()
            return ExportStmt(kw.line, kw.col, inner)

        if t.type == 'ID':
            ident = self.ts.next()
            self.ts.expect('SEMICOLON')
            return ExportStmt(
                kw.line, kw.col,
                Identifier(ident.line, ident.col, ident.value))

        raise self.error(
            f"expected declaration or identifier after 'export', "
            f"got {t.type} ({t.value!r})", t)

    def parse_module_decl(self):
        kw = self.ts.expect('MODULE')
        name = self.ts.expect('ID').value
        body = self.parse_block()
        return ModuleDecl(kw.line, kw.col, name, body)

    def parse_namespace_decl(self):
        kw = self.ts.expect('NAMESPACE')
        name = self.ts.expect('ID').value
        body = self.parse_block()
        return NamespaceDecl(kw.line, kw.col, name, body)
        
    def _parse_module_path(self):
        path = [self.ts.expect('ID').value]
        while self.ts.at('DOUBLE_COLON'):
            self.ts.next()
            path.append(self.ts.expect('ID').value)
        return path
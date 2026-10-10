"""Parser for LOOM programming language"""

from parser_compiler.carcass        import TokenStream, ParserBase
from parser_compiler.expr           import ExprMixin
from parser_compiler.stmt           import StmtMixin
from parser_compiler.forloop        import ForMixin
from parser_compiler.func           import FuncMixin
from parser_compiler.oop            import OOPMixin
from parser_compiler.pattern        import PatternMixin
from parser_compiler.error_handling import TryMixin
from parser_compiler.modules        import ModuleMixin
from parser_compiler.concurrency    import ConcurrencyMixin
from parser_compiler.misc           import MiscMixin


class Parser(
    ExprMixin,
    StmtMixin,
    ForMixin,
    FuncMixin,
    OOPMixin,
    PatternMixin,
    TryMixin,
    ModuleMixin,
    ConcurrencyMixin,
    MiscMixin,
    ParserBase,
):
    
    def parse_program(self):
        from AstLOOM import Program
        first = self.ts.peek()
        items = []
        while not self.ts.at_eof():
            items.append(self.parse_top_level_item())
        return Program(line=first.line, col=first.col, items=items)

    def parse_top_level_item(self):
        return self.parse_stmt()

__all__ = ["Parser", "TokenStream", "ParserBase"]
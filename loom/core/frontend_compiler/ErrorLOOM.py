"""Errors for LOOM programming language."""

class LoomError(Exception):
    phase = "loom"
    kind  = "error"

    def __init__(self, message, line=None, col=None, filename=None):
        self.message  = message
        self.line     = line
        self.col      = col
        self.filename = filename
        super().__init__(message)

    def _location(self):
        parts = []
        if self.filename:
            parts.append(str(self.filename))
        if self.line is not None:
            if self.col is not None:
                parts.append(f"{self.line}:{self.col}")
            else:
                parts.append(str(self.line))
        return ":".join(parts) if parts else None

    def __str__(self):
        loc = self._location()
        head = f"{self.phase} {self.kind}"
        if loc:
            return f"{loc}: {head}: {self.message}"
        return f"{head}: {self.message}"

    @classmethod
    def from_token(cls, message, token, filename=None):
        return cls(message, token.line, token.col, filename)

    @classmethod
    def from_node(cls, message, node, filename=None):
        return cls(message,
                   getattr(node, "line", None),
                   getattr(node, "col", None),
                   filename)

class LexError(LoomError):
    phase = "lexer"

class ParseError(LoomError):
    phase = "parser"

class UnexpectedToken(ParseError):
    kind = "error"

    def __init__(self, expected, got, line=None, col=None, filename=None):
        if isinstance(expected, (list, tuple, set)):
            expected = " or ".join(str(e) for e in expected)
        msg = f"expected {expected}, got {got.type} ({got.value!r})"
        super().__init__(msg, got.line, got.col, filename)
        self.expected = expected
        self.got      = got

class UnexpectedEOF(ParseError):
    kind = "error"

    def __init__(self, expected, line=None, col=None, filename=None):
        if isinstance(expected, (list, tuple, set)):
            expected = " or ".join(str(e) for e in expected)
        msg = f"unexpected end of file, expected {expected}"
        super().__init__(msg, line, col, filename)
        self.expected = expected

class SemanticError(LoomError):
    phase = "semantic"

class CodegenError(LoomError):
    phase = "codegen"

class VMError(LoomError):
    phase = "vm"
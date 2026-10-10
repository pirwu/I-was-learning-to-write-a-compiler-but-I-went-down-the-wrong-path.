"""Carcass for Parser LOOM programming language"""

from ErrorLOOM import (
    LoomError,
    ParseError,
    UnexpectedToken,
    UnexpectedEOF,
)

class TokenStream:

    def __init__(self, tokens, filename=None):
        if not tokens:
            raise ValueError("TokenStream requires a non-empty token list "
                             "(lexer must append EOF)")
        self.tokens = tokens
        self.pos = 0
        self.filename = filename

    def peek(self, offset=0):
        i = self.pos + offset
        if i >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[i]

    def at(self, *types):
        return self.peek().type in types

    def at_eof(self):
        return self.peek().type == 'EOF'

    def next(self):
        tok = self.peek()
        if tok.type != 'EOF':
            self.pos += 1
        return tok

    def expect(self, type_):
        tok = self.peek()
        if tok.type == 'EOF':
            raise UnexpectedEOF(type_, tok.line, tok.col, self.filename)
        if tok.type != type_:
            raise UnexpectedToken(type_, tok, self.filename)
        return self.next()

    def expect_id(self):
        return self.expect('ID').value

    def error(self, message, token=None):
        token = token or self.peek()
        return ParseError(message, token.line, token.col, self.filename)

class ParserBase:

    def __init__(self, tokens, filename=None):
        self.ts = TokenStream(tokens, filename)
        self.filename = filename

    def error(self, message, token=None):
        return self.ts.error(message, token)

    def _expect_semicolon(self):
        return self.ts.expect('SEMICOLON')

    def _expect_ident(self):
        return self.ts.expect_id()

    def _at_type_keyword(self):
        return self.ts.at('INT', 'DOUBLE', 'STR', 'CHAR', 'BOOL', 'VOID')
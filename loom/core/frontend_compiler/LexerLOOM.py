"""Lexer for LOOM programming language"""

import re
from collections import namedtuple
from TokensLOOM import TOKENS, KEYWORDS, IGNORED
from ErrorLOOM import LexError

Token = namedtuple('Token', ['type', 'value', 'line', 'col'])

class Lexer:
    def __init__(self, text):
        self.text = text
        parts = []
        for name, pattern in IGNORED:
            parts.append(f'(?P<{name}>{pattern})')
        for name, pattern in TOKENS:
            parts.append(f'(?P<{name}>{pattern})')
        self.master_re = re.compile('|'.join(parts))

    def tokenize(self):
        text = self.text
        n = len(text)
        pos = 0
        line = 1
        line_start = 0  # индекс начала текущей строки

        while pos < n:
            m = self.master_re.match(text, pos)
            if not m:
                col = pos - line_start + 1
                raise LexError(f"unexpected character {text[pos]!r}", line, col)

            kind = m.lastgroup
            value = m.group()
            col = m.start() - line_start + 1

            if kind not in ('WS', 'LINE_COMMENT', 'BLOCK_COMMENT'):
                yield self._make_token(kind, value, line, col)

            nl_count = value.count('\n')
            if nl_count:
                line += nl_count
                # позиция последнего \n в value -> начало следующей строки
                line_start = m.end() - (len(value) - value.rfind('\n') - 1)

            pos = m.end()

        yield Token('EOF', '<end>', line, pos - line_start + 1)

    def _make_token(self, kind, value, line, col):
        # ключевые слова
        if kind == 'ID' and value in KEYWORDS:
            kind = KEYWORDS[value]

        # приведение литералов
        elif kind == 'LITERAL_INT':
            value = int(value)
        elif kind == 'LITERAL_DOUBLE':
            value = float(value)
        elif kind == 'LITERAL_STR':
            value = value[1:-1]
        elif kind == 'LITERAL_CHAR':
            value = value[1:-1]

        return Token(kind, value, line, col)


def lex(code):
    return Lexer(code).tokenize()
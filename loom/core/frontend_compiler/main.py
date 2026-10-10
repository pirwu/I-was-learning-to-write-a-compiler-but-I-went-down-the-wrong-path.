"""
LOOM programming language — command line entry point.

Usage:
    main.py -help | -h
    main.py -version | -v
    main.py <file.loom> -lexer   | -l
    main.py <file.loom> -parser  | -p
    main.py <file.loom> -resolve | -r
    main.py <file> -codegen | -c       compile to .lbc bytecode file

Exit codes:
    0  success
    1  user error (bad args, missing file)
    2  compilation error (lexer, parser, semantic, codegen, vm)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from LexerLOOM import lex
from ErrorLOOM import LoomError

VERSION = "0.0.1"
LANG = "LOOM"

HELP_TEXT = f"""{LANG} compiler v{VERSION}

Usage:
  main.py -help | -h                 show this message
  main.py -version | -v              show version
  main.py <file> -lexer   | -l       tokenize and print tokens
  main.py <file> -parser  | -p       parse and print AST
  main.py <file> -resolve | -r       parse, resolve, print resolved AST
  main.py <file> -codegen | -c       compile to .lbc bytecode file

Examples:
  main.py example.loom -lexer
  main.py example.loom -parser
  main.py example.loom -resolve

Exit codes:
  0  success
  1  bad arguments / file not found
  2  compilation error
"""


def print_help():
    print(HELP_TEXT, end="")

def print_version():
    print(f"{LANG} v{VERSION}")

class UsageError(Exception):
    pass

ACTIONS = {
    "-lexer":   "lexer",
    "-l":       "lexer",
    "-tokens":  "lexer",
    "-t":       "lexer",
    "-parser":  "parser",
    "-p":       "parser",
    "-resolve": "resolve",
    "-r":       "resolve",
    "-codegen": "codegen",
    "-c":       "codegen",
}

def parse_args(argv):
    if not argv:
        raise UsageError("no arguments given")

    first = argv[0]

    if first in ("-help", "-h", "--help"):
        return {"mode": "help", "file": None, "out": None}

    if first in ("-version", "-v", "--version"):
        return {"mode": "version", "file": None, "out": None}

    filename = first
    rest = argv[1:]

    if not rest:
        raise UsageError(f"expected action after '{filename}'")

    action = rest[0]
    if action not in ACTIONS:
        raise UsageError(f"unknown action '{action}'")

    mode = ACTIONS[action]

    out_path = None
    if mode == "codegen":
        if len(rest) < 2:
            base, _ = os.path.splitext(filename)
            out_path = base + ".lbc"
        else:
            out_path = rest[1]

    return {"mode": mode, "file": filename, "out": out_path}

def read_source(path):
    if not os.path.exists(path):
        raise UsageError(f"file not found: {path}")
    if not os.path.isfile(path):
        raise UsageError(f"not a file: {path}")
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return f.read()
    except OSError as e:
        raise UsageError(f"cannot read '{path}': {e}")

def _tokenize(source, filename):
    return list(lex(source))

def _parse(tokens, filename):
    from parser import Parser
    return Parser(tokens, filename=filename).parse_program()

def _resolve(ast, filename):
    from ResolverLOOM import Resolver
    return Resolver().resolve(ast)
    
def _codegen(ast, filename):
    from CodegenLOOM import Codegen
    return Codegen().generate(ast)
    
def run_lexer(source, filename):
    tokens = _tokenize(source, filename)
    for tok in tokens:
        print(tok)
    print(f"# {len(tokens)} tokens")

def run_parser(source, filename):
    tokens = _tokenize(source, filename)
    ast = _parse(tokens, filename)
    print(ast)

def run_resolve(source, filename):
    tokens = _tokenize(source, filename)
    ast = _parse(tokens, filename)
    ast = _resolve(ast, filename)
    print(ast)

def run_codegen(source, filename, out_path):
    tokens = _tokenize(source, filename)
    ast = _parse(tokens, filename)
    ast = _resolve(ast, filename)
    module = _codegen(ast, filename)

    from Codegen_COMPILER.serializer import Serializer
    Serializer(module).write(out_path)

    print(f"wrote {out_path}")
    print(f"  functions : {len(module.functions.functions)}")
    print(f"  classes   : {len(module.classes.classes)}")
    print(f"  globals   : {len(module.globals.globals)}")
    print(f"  constants : {len(module.pool.entries)}")

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    try:
        args = parse_args(argv)
    except UsageError as e:
        print(f"error: {e}", file=sys.stderr)
        print_help()
        sys.exit(1)

    mode = args["mode"]

    if mode == "help":
        print_help()
        sys.exit(0)

    if mode == "version":
        print_version()
        sys.exit(0)

    filename = args["file"]

    try:
        source = read_source(filename)
    except UsageError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if mode == "lexer":
            run_lexer(source, filename)
        elif mode == "parser":
            run_parser(source, filename)
        elif mode == "resolve":
            run_resolve(source, filename)
        elif mode == "codegen":
            run_codegen(source, filename, args["out"])
        else:
            print(f"error: unknown mode {mode}", file=sys.stderr)
            sys.exit(1)

    except LoomError as e:
        if e.filename is None:
            e.filename = filename
        print(str(e), file=sys.stderr)
        sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()
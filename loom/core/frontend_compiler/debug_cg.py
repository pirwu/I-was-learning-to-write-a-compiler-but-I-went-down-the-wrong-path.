import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from LexerLOOM import lex
from parser import Parser
from ResolverLOOM import Resolver
from CodegenLOOM import Codegen

src = open("test.loom", encoding="utf-8-sig").read()
ast = Parser(list(lex(src)), "test.loom").parse_program()
ast = Resolver().resolve(ast)
module = Codegen().generate(ast)

print("=== module state after Codegen.generate() ===")
print("functions count :", len(module.functions.functions))
print("globals count   :", len(module.globals.globals))
print("classes count   :", len(module.classes.classes))
print("pool entries    :", len(module.pool.entries))
print("pool content    :", module.pool.entries)
print("program.globals :", ast.globals)

for i, fn in enumerate(module.functions.functions):
    print(f"  function[{i}] = {fn.name!r}  bytecode={len(fn.bytecode)}")

# now construct Serializer manually and check
from Codegen_COMPILER.serializer import Serializer
print()
print("=== before Serializer() ===")
print("pool entries    :", len(module.pool.entries))
s = Serializer(module)
print("=== after Serializer() ===")
print("pool entries    :", len(module.pool.entries))
print("pool content    :", module.pool.entries)
print("bytes           :", len(s.to_bytes()))
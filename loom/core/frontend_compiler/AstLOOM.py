"""AST for the LOOM programming language."""

from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class Node:
    line: int = 0
    col: int = 0

@dataclass
class Stmt(Node):
    pass

@dataclass
class Expr(Node):
    pass

@dataclass
class TypeNode(Node):
    pass

@dataclass
class UpvalueDesc(Node):
    is_local: bool = False
    index: int = -1
    name: str = ""

@dataclass
class Program(Node):
    items: list = field(default_factory=list)
    globals: list = field(default_factory=list)
    locals_count: int = 0

@dataclass
class PackageDecl(Stmt):
    name: str = ""

@dataclass
class ImportStmt(Stmt):
    path: list = field(default_factory=list)
    alias: Optional[str] = None
    from_path: Optional[list] = None
    names: Optional[list] = None
    star: bool = False

@dataclass
class ExportStmt(Stmt):
    inner: Any = None

@dataclass
class BaseType(TypeNode):
    name: str = ""

@dataclass
class OptionalType(TypeNode):
    inner: Any = None

@dataclass
class ArrayType(TypeNode):
    elem: Any = None
    size: Any = None

@dataclass
class FunctionType(TypeNode):
    params: list = field(default_factory=list)
    ret: Any = None

@dataclass
class GenericType(TypeNode):
    base: str = ""
    args: list = field(default_factory=list)

@dataclass
class VarDecl(Stmt):
    kind: str = "var"
    name: str = ""
    type_: Any = None
    init: Any = None
    slot: int = -1
    global_index: int = -1

@dataclass
class Block(Stmt):
    stmts: list = field(default_factory=list)

@dataclass
class EmptyStmt(Stmt):
    pass

@dataclass
class ExprStmt(Stmt):
    expr: Any = None

@dataclass
class If(Stmt):
    cond: Any = None
    then: Any = None
    elifs: list = field(default_factory=list)
    else_: Any = None

@dataclass
class CaseClause(Node):
    value: Any = None
    body: list = field(default_factory=list)

@dataclass
class DefaultClause(Node):
    body: list = field(default_factory=list)

@dataclass
class Switch(Stmt):
    subject: Any = None
    cases: list = field(default_factory=list)
    default: Any = None

@dataclass
class MatchArm(Node):
    pattern: Any = None
    guard: Any = None
    body: Any = None

@dataclass
class Match(Stmt):
    subject: Any = None
    arms: list = field(default_factory=list)

@dataclass
class While(Stmt):
    cond: Any = None
    body: Any = None

@dataclass
class DoWhile(Stmt):
    body: Any = None
    cond: Any = None

@dataclass
class ForIn(Stmt):
    var: str = ""
    var_slot: int = -1
    iterable: Any = None
    body: Any = None

@dataclass
class ForCStyle(Stmt):
    init: Any = None
    cond: Any = None
    step: Any = None
    body: Any = None

@dataclass
class RangeExpr(Expr):
    start: Any = None
    end: Any = None
    step: Any = None
    inclusive: bool = False

@dataclass
class RangeCall(Expr):
    args: list = field(default_factory=list)

@dataclass
class EnumerateExpr(Expr):
    inner: Any = None

@dataclass
class ZipExpr(Expr):
    parts: list = field(default_factory=list)

@dataclass
class ReversedExpr(Expr):
    inner: Any = None

@dataclass
class ExceptClause(Node):
    exc_type: Any = None
    alias: Optional[str] = None
    body: Any = None

@dataclass
class Try(Stmt):
    body: Any = None
    excepts: list = field(default_factory=list)
    finally_: Any = None

@dataclass
class Return(Stmt):
    value: Any = None

@dataclass
class Yield(Stmt):
    value: Any = None

@dataclass
class Break(Stmt):
    pass

@dataclass
class Continue(Stmt):
    pass

@dataclass
class Goto(Stmt):
    label: str = ""

@dataclass
class Assert(Stmt):
    cond: Any = None
    message: Any = None

@dataclass
class Raise(Stmt):
    value: Any = None

@dataclass
class Throw(Stmt):
    value: Any = None

@dataclass
class Param(Node):
    name: str = ""
    type_: Any = None
    default: Any = None
    slot: int = -1

@dataclass
class FuncDecl(Stmt):
    name: str = ""
    params: list = field(default_factory=list)
    ret_type: Any = None
    body: Any = None
    is_async: bool = False
    is_static: bool = False
    decorators: list = field(default_factory=list)
    slot: int = -1
    global_index: int = -1
    frame_size: int = 0
    upvalues: list = field(default_factory=list)

@dataclass
class LambdaExpr(Expr):
    params: list = field(default_factory=list)
    ret_type: Any = None
    body: Any = None
    frame_size: int = 0
    upvalues: list = field(default_factory=list)

@dataclass
class FuncBuiltin(Expr):
    name: str = ""
    func: Any = None
    iterable: Any = None

@dataclass
class ClassMember(Node):
    access: Optional[str] = None
    is_static: bool = False
    is_override: bool = False
    inner: Any = None

@dataclass
class Constructor(Node):
    params: list = field(default_factory=list)
    body: Any = None
    frame_size: int = 0
    upvalues: list = field(default_factory=list)

@dataclass
class Destructor(Node):
    body: Any = None
    frame_size: int = 0
    upvalues: list = field(default_factory=list)

@dataclass
class ClassDecl(Stmt):
    name: str = ""
    extends: Any = None
    implements: list = field(default_factory=list)
    members: list = field(default_factory=list)
    is_abstract: bool = False
    decorators: list = field(default_factory=list)
    slot: int = -1
    global_index: int = -1

@dataclass
class InterfaceDecl(Stmt):
    name: str = ""
    members: list = field(default_factory=list)
    slot: int = -1
    global_index: int = -1

@dataclass
class StructDecl(Stmt):
    name: str = ""
    members: list = field(default_factory=list)
    slot: int = -1
    global_index: int = -1

@dataclass
class RecordDecl(Stmt):
    name: str = ""
    params: list = field(default_factory=list)
    slot: int = -1
    global_index: int = -1

@dataclass
class ModuleDecl(Stmt):
    name: str = ""
    body: Any = None
    slot: int = -1
    global_index: int = -1

@dataclass
class NamespaceDecl(Stmt):
    name: str = ""
    body: Any = None
    slot: int = -1
    global_index: int = -1

@dataclass
class AsyncStmt(Stmt):
    body: Any = None

@dataclass
class AwaitExpr(Expr):
    value: Any = None

@dataclass
class ThreadDecl(Stmt):
    name: str = ""
    params: list = field(default_factory=list)
    body: Any = None
    frame_size: int = 0
    upvalues: list = field(default_factory=list)

@dataclass
class ProcessDecl(Stmt):
    name: str = ""
    params: list = field(default_factory=list)
    body: Any = None
    frame_size: int = 0
    upvalues: list = field(default_factory=list)

@dataclass
class CoroutineDecl(Stmt):
    name: str = ""
    params: list = field(default_factory=list)
    body: Any = None
    frame_size: int = 0
    upvalues: list = field(default_factory=list)

@dataclass
class SyncBlock(Stmt):
    body: Any = None

@dataclass
class MutexDecl(Stmt):
    name: str = ""

@dataclass
class SemaphoreDecl(Stmt):
    name: str = ""
    init: Any = None

@dataclass
class LockStmt(Stmt):
    lock: Any = None
    body: Any = None

@dataclass
class Assign(Expr):
    op: str = "="
    target: Any = None
    value: Any = None

@dataclass
class Ternary(Expr):
    cond: Any = None
    then: Any = None
    else_: Any = None

@dataclass
class Binary(Expr):
    op: str = ""
    left: Any = None
    right: Any = None

@dataclass
class Unary(Expr):
    op: str = ""
    operand: Any = None

@dataclass
class PreIncDec(Expr):
    op: str = ""
    operand: Any = None

@dataclass
class PostIncDec(Expr):
    op: str = ""
    operand: Any = None

@dataclass
class Call(Expr):
    callee: Any = None
    args: list = field(default_factory=list)

@dataclass
class Index(Expr):
    obj: Any = None
    index: Any = None

@dataclass
class Member(Expr):
    obj: Any = None
    name: str = ""

@dataclass
class Literal(Expr):
    value: Any = None
    lit_type: str = ""

@dataclass
class Identifier(Expr):
    name: str = ""
    binding: str = ""
    slot: int = -1
    upvalue_index: int = -1

@dataclass
class ArrayLiteral(Expr):
    items: list = field(default_factory=list)

@dataclass
class DictLiteral(Expr):
    entries: list = field(default_factory=list)

@dataclass
class NewExpr(Expr):
    type_name: str = ""
    args: list = field(default_factory=list)

@dataclass
class ConsoleCall(Expr):
    method: str = ""
    args: list = field(default_factory=list)

@dataclass
class InputCall(Expr):
    prompt: Any = None

@dataclass
class ThisExpr(Expr):
    pass

@dataclass
class SuperExpr(Expr):
    method: Optional[str] = None

@dataclass
class PatternLiteral(Node):
    value: Any = None
    lit_type: str = ""

@dataclass
class PatternIdent(Node):
    name: str = ""

@dataclass
class PatternWildcard(Node):
    pass

@dataclass
class PatternOr(Node):
    parts: list = field(default_factory=list)

@dataclass
class PatternCall(Node):
    name: str = ""
    args: list = field(default_factory=list)

@dataclass
class Decorator(Node):
    name: str = ""
    args: list = field(default_factory=list)
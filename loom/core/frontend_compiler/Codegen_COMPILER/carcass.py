"""Code generator for LPL."""

import struct

from ErrorLOOM import CodegenError

CONST_INT    = 0x01
CONST_DOUBLE = 0x02
CONST_STR    = 0x03
CONST_CHAR   = 0x04
CONST_NAME   = 0x05

class ConstantPool:

    def __init__(self):
        self.entries = []
        self._index = {}

    def _add(self, tag, value):
        key = (tag, value)
        idx = self._index.get(key)
        if idx is not None:
            return idx
        idx = len(self.entries)
        self.entries.append((tag, value))
        self._index[key] = idx
        return idx

    def add_int(self, value):
        return self._add(CONST_INT, int(value))

    def add_double(self, value):
        return self._add(CONST_DOUBLE, float(value))

    def add_str(self, value):
        return self._add(CONST_STR, str(value))

    def add_char(self, value):
        return self._add(CONST_CHAR, ord(value) if value else 0)

    def add_name(self, value):
        return self._add(CONST_NAME, str(value))
        
    def lookup_name(self, value):
        idx = self._index.get((CONST_NAME, value))
        if idx is None:
            raise RuntimeError(
                f"name {value!r} was not registered in the constant pool — "
                f"call Serializer._register_names() first")
        return idx

class FunctionBuffer:

    def __init__(self, name, arity, locals_count, upvalues):
        self.name = name
        self.arity = arity
        self.locals_count = locals_count
        self.upvalues = list(upvalues or [])
        self.bytecode = bytearray()
        self.line_table = []
        self.max_stack = 0
        self._current_line = 0

    def emit_op(self, opcode):
        self.bytecode.append(opcode & 0xFF)

    def emit_u8(self, value):
        self.bytecode.append(value & 0xFF)

    def emit_u16(self, value):
        self.bytecode.extend((value & 0xFFFF).to_bytes(2, 'big'))

    def emit_i16(self, value):
        self.bytecode.extend(int(value).to_bytes(2, 'big', signed=True))

    def emit_u32(self, value):
        self.bytecode.extend((value & 0xFFFFFFFF).to_bytes(4, 'big'))

    def emit_i64(self, value):
        self.bytecode.extend(int(value).to_bytes(8, 'big', signed=True))

    def emit_f64(self, value):
        self.bytecode.extend(struct.pack('>d', float(value)))

    def set_line(self, line):
        if line == self._current_line:
            return
        self._current_line = line
        offset = len(self.bytecode)
        if self.line_table and self.line_table[-1][0] == offset:
            self.line_table[-1] = (offset, line)
        else:
            self.line_table.append((offset, line))

    def patch_i16(self, at_offset, value):
        self.bytecode[at_offset:at_offset + 2] = \
            int(value).to_bytes(2, 'big', signed=True)

    def here(self):
        return len(self.bytecode)

class FunctionTable:
    def __init__(self):
        self.functions = []

    def add(self, buffer):
        idx = len(self.functions)
        self.functions.append(buffer)
        return idx

class ClassEntry:
    def __init__(self, name, super_name, flags, fields, methods):
        self.name = name
        self.super_name = super_name
        self.flags = flags
        self.fields = list(fields)
        self.methods = list(methods)

class ClassTable:
    def __init__(self):
        self.classes = []

    def add(self, entry):
        idx = len(self.classes)
        self.classes.append(entry)
        return idx

class GlobalTable:
    def __init__(self):
        self.globals = []

    def add(self, name):
        idx = len(self.globals)
        self.globals.append(name)
        return idx

class ModuleModel:
    def __init__(self):
        self.pool = ConstantPool()
        self.functions = FunctionTable()
        self.classes = ClassTable()
        self.globals = GlobalTable()
        self.entry_index = 0
        self.flags = 0x01
        
class LoopContext:

    def __init__(self, continue_target=None):
        self.continue_target = continue_target
        self.break_patches = []

    def add_break_patch(self, at_offset):
        self.break_patches.append(at_offset)

class CodegenBase:

    def __init__(self, program=None):
        self.module = ModuleModel()
        self.current_func = None
        self.loop_stack = []
        self.func_stack = []
        self._program = program

    def error(self, message, node=None):
        if node is None:
            return CodegenError(message)
        return CodegenError(message, node.line, node.col)

    def emit_op(self, op):
        self.current_func.emit_op(op)

    def emit_u8(self, v):
        self.current_func.emit_u8(v)

    def emit_u16(self, v):
        self.current_func.emit_u16(v)

    def emit_i16(self, v):
        self.current_func.emit_i16(v)

    def emit_u32(self, v):
        self.current_func.emit_u32(v)

    def emit_i64(self, v):
        self.current_func.emit_i64(v)

    def emit_f64(self, v):
        self.current_func.emit_f64(v)

    def here(self):
        return self.current_func.here()

    def set_line(self, line):
        if line and self.current_func is not None:
            self.current_func.set_line(line)

    def emit_jump(self, opcode):
        self.emit_op(opcode)
        at = self.here()
        self.emit_i16(0)
        return at

    def patch_jump(self, at_offset):
        target = self.here()
        rel = target - (at_offset + 2)
        self.current_func.patch_i16(at_offset, rel)

    def patch_jump_to(self, at_offset, target):
        rel = target - (at_offset + 2)
        self.current_func.patch_i16(at_offset, rel)

    def push_function(self, buffer):
        idx = self.module.functions.add(buffer)
        self.func_stack.append(self.current_func)
        self.current_func = buffer
        return idx

    def pop_function(self):
        self.current_func = self.func_stack.pop()
        
    def push_loop(self, ctx):
        self.loop_stack.append(ctx)

    def pop_loop(self):
        return self.loop_stack.pop()

    def current_loop(self):
        if not self.loop_stack:
            return None
        return self.loop_stack[-1]
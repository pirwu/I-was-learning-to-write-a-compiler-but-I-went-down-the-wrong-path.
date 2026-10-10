"""LOOM bytecode disassembler."""

import sys
import struct

MAGIC = b"LOOM"

CONST_INT    = 0x01
CONST_DOUBLE = 0x02
CONST_STR    = 0x03
CONST_CHAR   = 0x04
CONST_NAME   = 0x05

TAG_NAMES = {
    CONST_INT:    "INT",
    CONST_DOUBLE: "DOUBLE",
    CONST_STR:    "STR",
    CONST_CHAR:   "CHAR",
    CONST_NAME:   "NAME",
}

OPCODES = {
    0x00: ("NOP",            None),
    0x01: ("PUSH_CONST",     "pool_name_u16"),
    0x02: ("PUSH_INT",       "i64"),
    0x03: ("PUSH_DOUBLE",    "f64"),
    0x04: ("PUSH_STR",       "pool_str_u16"),
    0x05: ("PUSH_CHAR",      "u8"),
    0x06: ("PUSH_TRUE",      None),
    0x07: ("PUSH_FALSE",     None),
    0x08: ("PUSH_NULL",      None),
    0x09: ("POP",            None),
    0x0A: ("DUP",            None),
    0x0B: ("DUP2",           None),
    0x0C: ("SWAP",           None),
    0x0D: ("ROT3",           None),
    0x0E: ("OVER",           None),
    0x0F: ("POP_N",          "u8"),

    0x10: ("LOAD_LOCAL",     "local_u8"),
    0x11: ("STORE_LOCAL",    "local_u8"),
    0x12: ("LOAD_GLOBAL",    "global_u16"),
    0x13: ("STORE_GLOBAL",   "global_u16"),
    0x14: ("LOAD_UPVALUE",   "u16"),
    0x15: ("STORE_UPVALUE",  "u16"),
    0x16: ("LOAD_ATTR",      "pool_name_u16"),
    0x17: ("STORE_ATTR",     "pool_name_u16"),
    0x18: ("LOAD_SELF",      None),
    0x19: ("LOAD_INDEX",     None),
    0x1A: ("STORE_INDEX",    None),
    0x1B: ("LOAD_SUPER",     None),
    0x1C: ("LOAD_MODULE",    "pool_name_u16"),
    0x1D: ("LOAD_NAMESPACE", "pool_name_u16"),
    0x1E: ("DECLARE_VAR",    "pool_name_u16"),
    0x1F: ("DECLARE_CONST",  "pool_name_u16"),

    0x20: ("ADD",            None),
    0x21: ("SUB",            None),
    0x22: ("MUL",            None),
    0x23: ("DIV",            None),
    0x24: ("IDIV",           None),
    0x25: ("MOD",            None),
    0x26: ("POW",            None),
    0x27: ("NEG",            None),
    0x28: ("INC_LOCAL",      "local_u8"),
    0x29: ("DEC_LOCAL",      "local_u8"),
    0x2A: ("INC_OP",         None),
    0x2B: ("DEC_OP",         None),
    0x2C: ("CONCAT",         None),

    0x30: ("BIT_AND",        None),
    0x31: ("BIT_OR",         None),
    0x32: ("BIT_XOR",        None),
    0x33: ("BIT_NOT",        None),
    0x34: ("LSHIFT",         None),
    0x35: ("RSHIFT",         None),

    0x40: ("CMP_EQ",         None),
    0x41: ("CMP_NEQ",        None),
    0x42: ("CMP_LT",         None),
    0x43: ("CMP_GT",         None),
    0x44: ("CMP_LE",         None),
    0x45: ("CMP_GE",         None),
    0x46: ("LOGIC_AND",      None),
    0x47: ("LOGIC_OR",       None),
    0x48: ("LOGIC_NOT",      None),
    0x49: ("CMP_IS",         None),
    0x4A: ("INSTANCE_OF",    "pool_name_u16"),
    0x4B: ("TYPE_CHECK",     "u16"),
    0x4C: ("TYPEOF",         None),

    0x50: ("JUMP",            "i16"),
    0x51: ("JUMP_IF_TRUE",    "i16"),
    0x52: ("JUMP_IF_FALSE",   "i16"),
    0x53: ("JUMP_IF_NULL",    "i16"),
    0x54: ("JUMP_IF_NOT_NULL","i16"),
    0x55: ("SETUP_LOOP",      "i16"),
    0x56: ("POP_LOOP",        None),
    0x57: ("BREAK",           None),
    0x58: ("CONTINUE",        None),
    0x59: ("GOTO",            "u16"),

    0x60: ("CALL",            "u8"),
    0x61: ("CALL_METHOD",     "u16_u8"),
    0x62: ("CALL_STATIC",     "u16_u8"),
    0x63: ("CALL_SUPER",      "u16_u8"),
    0x64: ("RETURN",          None),
    0x65: ("RETURN_VOID",     None),
    0x66: ("YIELD",           None),
    0x67: ("YIELD_FROM",      None),
    0x68: ("TAIL_CALL",       "u8"),

    0x70: ("NEW_OBJECT",      "pool_name_u16"),
    0x71: ("NEW_ARRAY",       "u16"),
    0x72: ("NEW_DICT",        "u16"),
    0x73: ("NEW_STRUCT",      "pool_name_u16"),
    0x74: ("NEW_RECORD",      "pool_name_u16"),
    0x75: ("DEFINE_CLASS",    "pool_name_u16"),
    0x76: ("DEFINE_METHOD",   "u16_u16"),
    0x77: ("DEFINE_FIELD",    "u16_u16"),
    0x78: ("DEFINE_INTERFACE","pool_name_u16"),
    0x79: ("IMPLEMENT_IFACE", "u16_u16"),
    0x7A: ("EXTENDS_CLASS",   "u16_u16"),
    0x7B: ("INVOKE_CTOR",     "u8"),
    0x7C: ("INVOKE_DTOR",     None),
    0x7D: ("SET_ACCESS",      "u8"),
    0x7E: ("SET_STATIC",      None),
    0x7F: ("SET_ABSTRACT",    None),
    0x80: ("SET_OVERRIDE",    None),
    0x81: ("CAST",            "pool_name_u16"),
    0x82: ("UNBOX",           "u8"),
    0x83: ("BOX",             "u8"),

    0x90: ("BUILD_RANGE",     "u8"),
    0x91: ("BUILD_RANGE_INCL","u8"),
    0x92: ("GET_ITER",        None),
    0x93: ("ITER_NEXT",       "i16"),
    0x94: ("ITER_CLOSE",      None),
    0x95: ("BUILD_ENUMERATE", None),
    0x96: ("BUILD_ZIP",       "u8"),
    0x97: ("BUILD_REVERSED",  None),
    0x98: ("UNPACK",          "u8"),

    0xA0: ("CONSOLE_WRITE",   None),
    0xA1: ("CONSOLE_WRITELN", None),
    0xA2: ("INPUT_READ",      "u8"),
    0xA3: ("MAP_CALL",        "u8"),
    0xA4: ("FILTER_CALL",     "u8"),
    0xA5: ("REDUCE_CALL",     "u8"),
    0xA6: ("ASSERT_CHECK",    None),
    0xA7: ("PRINT_FMT",       "u8"),

    0xB0: ("SETUP_TRY",       "i16"),
    0xB1: ("POP_TRY",         None),
    0xB2: ("THROW",           None),
    0xB3: ("RAISE",           "pool_name_u16"),
    0xB4: ("SETUP_EXCEPT",    "i16"),
    0xB5: ("POP_EXCEPT",      None),
    0xB6: ("SETUP_FINALLY",   "i16"),
    0xB7: ("POP_FINALLY",     None),
    0xB8: ("PUSH_EXCEPTION",  None),
    0xB9: ("MATCH_EXCEPTION", "pool_name_u16"),

    0xC0: ("SPAWN_THREAD",    "u8"),
    0xC1: ("SPAWN_PROCESS",   "u8"),
    0xC2: ("SPAWN_COROUTINE", "u8"),
    0xC3: ("AWAIT",           None),
    0xC4: ("ASYNC_ENTER",     None),
    0xC5: ("ASYNC_EXIT",      None),
    0xC6: ("MUTEX_CREATE",    "u16"),
    0xC7: ("MUTEX_LOCK",      None),
    0xC8: ("MUTEX_UNLOCK",    None),
    0xC9: ("SEMAPHORE_CREATE","u16_u8"),
    0xCA: ("SEMAPHORE_ACQUIRE", None),
    0xCB: ("SEMAPHORE_RELEASE", None),
    0xCC: ("SYNC_ENTER",      None),
    0xCD: ("SYNC_EXIT",       None),
    0xCE: ("LOCK_ENTER",      None),
    0xCF: ("LOCK_EXIT",       None),

    0xD0: ("IMPORT_MODULE",   "pool_name_u16"),
    0xD1: ("IMPORT_FROM",     "u16_u16"),
    0xD2: ("IMPORT_ALL",      "pool_name_u16"),
    0xD3: ("IMPORT_AS",       "u16_u16"),
    0xD4: ("EXPORT_SYMBOL",   "pool_name_u16"),
    0xD5: ("LOAD_PACKAGE",    "pool_name_u16"),
    0xD6: ("ENTER_NAMESPACE", "pool_name_u16"),
    0xD7: ("EXIT_NAMESPACE",  None),
    0xD8: ("RESOLVE_DCOLON",  "pool_name_u16"),

    0xE0: ("MAKE_CLOSURE",    "func_ref_u16_u8"),
    0xE1: ("MAKE_LAMBDA",     "func_ref_u16_u8"),
    0xE2: ("CAPTURE_LOCAL",   "local_u8"),
    0xE3: ("CAPTURE_UPVALUE", "u16"),
    0xE4: ("APPLY_DECORATOR", "pool_name_u16"),

    0xF0: ("MATCH_START",     None),
    0xF1: ("MATCH_LITERAL",   "pool_name_u16"),
    0xF2: ("MATCH_BIND",      "local_u8"),
    0xF3: ("MATCH_GUARD",     "i16"),
    0xF4: ("MATCH_END",       None),
    0xF5: ("MATCH_DESTRUCT",  "u8"),

    0xF6: ("HALT",            None),
    0xF7: ("LINE_INFO",       "u32"),
    0xF8: ("DEBUG_BREAK",     None),
    0xF9: ("META",            "pool_name_u16"),
}

class Reader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def u8(self):
        v = self.data[self.pos]
        self.pos += 1
        return v

    def u16(self):
        v = int.from_bytes(self.data[self.pos:self.pos+2], 'big')
        self.pos += 2
        return v

    def i16(self):
        v = int.from_bytes(self.data[self.pos:self.pos+2], 'big', signed=True)
        self.pos += 2
        return v

    def u32(self):
        v = int.from_bytes(self.data[self.pos:self.pos+4], 'big')
        self.pos += 4
        return v

    def i64(self):
        v = int.from_bytes(self.data[self.pos:self.pos+8], 'big', signed=True)
        self.pos += 8
        return v

    def f64(self):
        v = struct.unpack('>d', self.data[self.pos:self.pos+8])[0]
        self.pos += 8
        return v

    def bytes(self, n):
        v = self.data[self.pos:self.pos+n]
        self.pos += n
        return v

    def eof(self):
        return self.pos >= len(self.data)

class DisasmError(Exception):
    pass

class Disassembler:

    def __init__(self, data):
        self.r = Reader(data)
        self.pool = []
        self.functions = []
        self.classes = []
        self.globals = []

    def run(self):
        self._header()
        self._constant_pool()
        self._functions()
        self._classes()
        self._globals()
        self._sanity_check()
        self._dump()

    def _header(self):
        magic = self.r.bytes(4)
        if magic != MAGIC:
            raise DisasmError(f"bad magic: {magic!r} (expected {MAGIC!r})")
        self.version_major = self.r.u8()
        self.version_minor = self.r.u8()
        self.flags = self.r.u8()
        self.entry_point = self.r.u32()
        self.r.bytes(5)

    def _constant_pool(self):
        n = self.r.u32()
        for _ in range(n):
            tag = self.r.u8()
            if tag == CONST_INT:
                self.pool.append((tag, self.r.i64()))
            elif tag == CONST_DOUBLE:
                self.pool.append((tag, self.r.f64()))
            elif tag == CONST_STR:
                length = self.r.u32()
                self.pool.append((tag, self.r.bytes(length).decode('utf-8')))
            elif tag == CONST_CHAR:
                self.pool.append((tag, self.r.u32()))
            elif tag == CONST_NAME:
                length = self.r.u32()
                self.pool.append((tag, self.r.bytes(length).decode('utf-8')))
            else:
                raise DisasmError(
                    f"unknown constant tag 0x{tag:02x} "
                    f"at pool index {len(self.pool)}")
                    
    def _functions(self):
        n = self.r.u32()
        for _ in range(n):
            name_idx = self.r.u32()
            arity = self.r.u8()
            locals_count = self.r.u8()
            max_stack = self.r.u16()
            upvalues_count = self.r.u16()
            bytecode_len = self.r.u32()
            bytecode = self.r.bytes(bytecode_len)

            upvalues = []
            for _ in range(upvalues_count):
                is_local = self.r.u8()
                index = self.r.u8()
                upvalues.append((is_local, index))

            line_count = self.r.u32()
            line_table = []
            for _ in range(line_count):
                offset = self.r.u32()
                line = self.r.u32()
                line_table.append((offset, line))

            self.functions.append({
                "name_idx": name_idx,
                "arity": arity,
                "locals_count": locals_count,
                "max_stack": max_stack,
                "upvalues": upvalues,
                "bytecode": bytecode,
                "line_table": line_table,
            })

    def _classes(self):
        n = self.r.u32()
        for _ in range(n):
            name_idx = self.r.u32()
            super_idx = self.r.u32()
            flags = self.r.u8()
            fields_count = self.r.u16()
            fields = [self.r.u32() for _ in range(fields_count)]
            methods_count = self.r.u32()
            methods = []
            for _ in range(methods_count):
                m_name = self.r.u32()
                m_func = self.r.u32()
                methods.append((m_name, m_func))
            self.classes.append({
                "name_idx": name_idx,
                "super_idx": super_idx,
                "flags": flags,
                "fields": fields,
                "methods": methods,
            })

    def _globals(self):
        n = self.r.u32()
        for _ in range(n):
            self.globals.append(self.r.u32())

    def _sanity_check(self):
        pool_size = len(self.pool)
        bad = []

        for i, fn in enumerate(self.functions):
            if fn["name_idx"] >= pool_size:
                bad.append(f"function[{i}].name_idx={fn['name_idx']}")

        for i, cls in enumerate(self.classes):
            if cls["name_idx"] >= pool_size:
                bad.append(f"class[{i}].name_idx={cls['name_idx']}")
            if cls["super_idx"] != 0xFFFFFFFF and cls["super_idx"] >= pool_size:
                bad.append(f"class[{i}].super_idx={cls['super_idx']}")
            for f in cls["fields"]:
                if f >= pool_size:
                    bad.append(f"class[{i}].field_idx={f}")
            for mn, _ in cls["methods"]:
                if mn >= pool_size:
                    bad.append(f"class[{i}].method_name_idx={mn}")

        for i, g in enumerate(self.globals):
            if g >= pool_size:
                bad.append(f"global[{i}]={g}")

        if bad:
            raise DisasmError(
                f"constant pool has only {pool_size} entries, but the file "
                f"references indices outside it:\n  " +
                "\n  ".join(bad) +
                "\nThis usually means Serializer wrote the pool before "
                "all names were registered. Call _register_names() before "
                "writing the pool."
            )
            
    def _func_name(self, idx):
        if 0 <= idx < len(self.functions):
            return self._pool_str(self.functions[idx]["name_idx"])
        return f"<func#{idx}?>"

    def _pool_str(self, idx):
        if idx < 0 or idx >= len(self.pool):
            return f"<pool#{idx}?>"
        tag, value = self.pool[idx]
        if tag in (CONST_STR, CONST_NAME):
            return f'"{value}"'
        if tag == CONST_CHAR:
            try:
                return f"'{chr(value)}'"
            except ValueError:
                return f"<char {value}>"
        return str(value)

    def _global_name(self, idx):
        if idx < len(self.globals):
            return self._pool_str(self.globals[idx])
        return f"<global#{idx}?>"

    def _dump(self):
        print("=== LOOM bytecode ===")
        print(f"version   : {self.version_major}.{self.version_minor}")
        print(f"flags     : 0x{self.flags:02x}")
        print(f"entry     : function #{self.entry_point}")
        print()

        print(f"Constant pool ({len(self.pool)}):")
        for i, (tag, value) in enumerate(self.pool):
            tag_name = TAG_NAMES.get(tag, f"TAG{tag}")
            if tag in (CONST_STR, CONST_NAME):
                print(f"  [{i:3}] {tag_name:<7} \"{value}\"")
            elif tag == CONST_CHAR:
                try:
                    print(f"  [{i:3}] {tag_name:<7} '{chr(value)}'")
                except ValueError:
                    print(f"  [{i:3}] {tag_name:<7} {value}")
            else:
                print(f"  [{i:3}] {tag_name:<7} {value}")
        print()

        print(f"Function table ({len(self.functions)}):")
        for i, fn in enumerate(self.functions):
            name = self._pool_str(fn["name_idx"])
            print(f"  [{i}] {name}  arity={fn['arity']}  "
                  f"locals={fn['locals_count']}  "
                  f"upvalues={len(fn['upvalues'])}  "
                  f"bytecode={len(fn['bytecode'])} bytes")
            self._disasm_bytecode(fn["bytecode"])
            if fn["upvalues"]:
                print(f"     upvalues:")
                for is_local, index in fn["upvalues"]:
                    kind = "local" if is_local else "upvalue"
                    print(f"       {kind}[{index}]")
            if fn["line_table"]:
                print(f"     line table:")
                for offset, line in fn["line_table"]:
                    print(f"       {offset:04x} -> line {line}")
            print()

        print(f"Class table ({len(self.classes)}):")
        for i, c in enumerate(self.classes):
            name = self._pool_str(c["name_idx"])
            super_name = ("none" if c["super_idx"] == 0xFFFFFFFF
                          else self._pool_str(c["super_idx"]))
            print(f"  [{i}] {name}  extends={super_name}  "
                  f"flags=0x{c['flags']:02x}")
            for f in c["fields"]:
                print(f"       field  {self._pool_str(f)}")
            for mn, mf in c["methods"]:
                print(f"       method {self._pool_str(mn)} -> func#{mf}")
        print()

        print(f"Global table ({len(self.globals)}):")
        for i, idx in enumerate(self.globals):
            print(f"  [{i}] {self._pool_str(idx)}")

    def _disasm_bytecode(self, bytecode):
        ip = 0
        while ip < len(bytecode):
            start = ip
            op = bytecode[ip]
            ip += 1
            entry = OPCODES.get(op)
            if entry is None:
                print(f"     {start:04x}  <unknown 0x{op:02x}>")
                continue
            name, argtype = entry

            text, ip, comment = self._decode_operand(argtype, bytecode, ip)

            line = f"     {start:04x}  {name:<18}{text}"
            if comment:
                line += f"   ; {comment}"
            print(line)

    def _decode_operand(self, argtype, bytecode, ip):
        if argtype is None:
            return "", ip, ""
            
        if argtype == "u16_u16":
            a = int.from_bytes(bytecode[ip:ip+2], 'big')
            b = int.from_bytes(bytecode[ip+2:ip+4], 'big')
            return f" {a} {b}", ip + 4, f"{self._pool_str(a)}, {self._pool_str(b)}"

        if argtype == "u8":
            v = bytecode[ip]
            return f" {v}", ip + 1, ""

        if argtype == "local_u8":
            v = bytecode[ip]
            return f" {v}", ip + 1, f"local[{v}]"

        if argtype == "u16":
            v = int.from_bytes(bytecode[ip:ip+2], 'big')
            return f" {v}", ip + 2, ""

        if argtype == "u32":
            v = int.from_bytes(bytecode[ip:ip+4], 'big')
            return f" {v}", ip + 4, ""

        if argtype == "i16":
            v = int.from_bytes(bytecode[ip:ip+2], 'big', signed=True)
            target = ip + 2 + v
            return f" {v:+d} -> {target:04x}", ip + 2, ""

        if argtype == "i64":
            v = int.from_bytes(bytecode[ip:ip+8], 'big', signed=True)
            return f" {v}", ip + 8, ""

        if argtype == "f64":
            v = struct.unpack('>d', bytecode[ip:ip+8])[0]
            return f" {v}", ip + 8, ""

        if argtype == "pool_name_u16":
            v = int.from_bytes(bytecode[ip:ip+2], 'big')
            return f" {v}", ip + 2, self._pool_str(v)

        if argtype == "pool_str_u16":
            v = int.from_bytes(bytecode[ip:ip+2], 'big')
            return f" {v}", ip + 2, self._pool_str(v)

        if argtype == "global_u16":
            v = int.from_bytes(bytecode[ip:ip+2], 'big')
            return f" {v}", ip + 2, self._global_name(v)

        if argtype == "u16_u8":
            a = int.from_bytes(bytecode[ip:ip+2], 'big')
            b = bytecode[ip+2]
            return f" {a} {b}", ip + 3, f"{self._pool_str(a)}, argc={b}"
            
        if argtype == "func_ref_u16_u8":
            a = int.from_bytes(bytecode[ip:ip+2], 'big')
            b = bytecode[ip+2]
            fname = self._func_name(a)
            return f" {a} {b}", ip + 3, f"{fname}, upvalues={b}"

        return f" <{argtype}?>", ip, ""

    def _decode_operand_OLD(self, argtype, bytecode, ip):
        pass

def main():
    if len(sys.argv) < 2:
        print("usage: python DisasmLOOM.py <file.lbc>")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "rb") as f:
        data = f.read()

    try:
        Disassembler(data).run()
    except DisasmError as e:
        print(f"disasm error: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
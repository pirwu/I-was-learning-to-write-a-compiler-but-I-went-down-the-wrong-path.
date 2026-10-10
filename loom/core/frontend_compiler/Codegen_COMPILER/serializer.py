"""Serializer for LPL"""

import struct

from Codegen_COMPILER.carcass import (
    CONST_INT, CONST_DOUBLE, CONST_STR, CONST_CHAR, CONST_NAME,
)

MAGIC = b"LOOM"
VERSION_MAJOR = 1
VERSION_MINOR = 0

class Serializer:

    def __init__(self, module):
        self.module = module
        self._register_names()

    def _register_names(self):
        pool = self.module.pool

        for buf in self.module.functions.functions:
            pool.add_name(buf.name)

        for cls in self.module.classes.classes:
            pool.add_name(cls.name)
            if cls.super_name is not None:
                pool.add_name(cls.super_name)
            for field_name in cls.fields:
                pool.add_name(field_name)
            for m_name, _ in cls.methods:
                pool.add_name(m_name)

        for name in self.module.globals.globals:
            pool.add_name(name)

    def write(self, path):
        data = self.to_bytes()
        with open(path, 'wb') as f:
            f.write(data)

    def to_bytes(self):
        out = bytearray()
        out += self._header()
        out += self._constant_pool()
        out += self._function_table()
        out += self._class_table()
        out += self._global_table()
        return bytes(out)

    def _header(self):
        out = bytearray()
        out += MAGIC
        out.append(VERSION_MAJOR)
        out.append(VERSION_MINOR)
        out.append(self.module.flags & 0xFF)
        out += self.module.entry_index.to_bytes(4, 'big')
        out += b'\x00' * 5
        assert len(out) == 16
        return out

    def _constant_pool(self):
        out = bytearray()
        pool = self.module.pool
        out += len(pool.entries).to_bytes(4, 'big')
        for tag, value in pool.entries:
            out.append(tag)
            if tag == CONST_INT:
                out += int(value).to_bytes(8, 'big', signed=True)
            elif tag == CONST_DOUBLE:
                out += struct.pack('>d', float(value))
            elif tag == CONST_STR or tag == CONST_NAME:
                data = value.encode('utf-8')
                out += len(data).to_bytes(4, 'big')
                out += data
            elif tag == CONST_CHAR:
                out += int(value).to_bytes(4, 'big')
            else:
                raise ValueError(f"unknown constant tag: {tag}")
        return out

    def _function_table(self):
        out = bytearray()
        funcs = self.module.functions.functions
        out += len(funcs).to_bytes(4, 'big')
        for buf in funcs:
            name_idx = self.module.pool.lookup_name(buf.name)
            out += name_idx.to_bytes(4, 'big')
            out.append(buf.arity & 0xFF)
            out.append(buf.locals_count & 0xFF)
            out += (buf.max_stack & 0xFFFF).to_bytes(2, 'big')
            out += (len(buf.upvalues) & 0xFFFF).to_bytes(2, 'big')
            out += len(buf.bytecode).to_bytes(4, 'big')
            out += bytes(buf.bytecode)

            for uv in buf.upvalues:
                out.append(1 if uv.is_local else 0)
                out.append((uv.index if uv.index >= 0 else 0) & 0xFF)

            out += len(buf.line_table).to_bytes(4, 'big')
            for offset, line in buf.line_table:
                out += offset.to_bytes(4, 'big')
                out += line.to_bytes(4, 'big')

        return out

    def _class_table(self):
        out = bytearray()
        classes = self.module.classes.classes
        out += len(classes).to_bytes(4, 'big')
        for cls in classes:
            name_idx = self.module.pool.lookup_name(cls.name)
            out += name_idx.to_bytes(4, 'big')

            if cls.super_name is None:
                out += (0xFFFFFFFF).to_bytes(4, 'big')
            else:
                super_idx = self.module.pool.lookup_name(cls.super_name)
                out += super_idx.to_bytes(4, 'big')

            out.append(cls.flags & 0xFF)
            out += len(cls.fields).to_bytes(2, 'big')

            for field_name in cls.fields:
                fidx = self.module.pool.lookup_name(field_name)
                out += fidx.to_bytes(4, 'big')

            out += len(cls.methods).to_bytes(4, 'big')
            for m_name, m_func_idx in cls.methods:
                midx = self.module.pool.lookup_name(m_name)
                out += midx.to_bytes(4, 'big')
                out += m_func_idx.to_bytes(4, 'big')

        return out

    def _global_table(self):
        out = bytearray()
        globals_ = self.module.globals.globals
        out += len(globals_).to_bytes(4, 'big')
        for name in globals_:
            nidx = self.module.pool.lookup_name(name)
            out += nidx.to_bytes(4, 'big')
        return out
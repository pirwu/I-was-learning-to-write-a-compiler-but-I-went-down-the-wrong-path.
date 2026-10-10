"""LVM opcodes"""

# --- 0x00 stack & constants ---
NOP         = 0x00
PUSH_CONST  = 0x01
PUSH_INT    = 0x02
PUSH_DOUBLE = 0x03
PUSH_STR    = 0x04
PUSH_CHAR   = 0x05
PUSH_TRUE   = 0x06
PUSH_FALSE  = 0x07
PUSH_NULL   = 0x08
POP         = 0x09
DUP         = 0x0A
DUP2        = 0x0B
SWAP        = 0x0C
ROT3        = 0x0D
OVER        = 0x0E
POP_N       = 0x0F

# --- 0x10 variables ---
LOAD_LOCAL    = 0x10
STORE_LOCAL   = 0x11
LOAD_GLOBAL   = 0x12
STORE_GLOBAL  = 0x13
LOAD_UPVALUE  = 0x14
STORE_UPVALUE = 0x15
LOAD_ATTR     = 0x16
STORE_ATTR    = 0x17
LOAD_SELF     = 0x18
LOAD_INDEX    = 0x19
STORE_INDEX   = 0x1A
LOAD_SUPER    = 0x1B
LOAD_MODULE   = 0x1C
LOAD_NAMESPACE = 0x1D
DECLARE_VAR   = 0x1E
DECLARE_CONST = 0x1F

# --- 0x20 arithmetic ---
ADD       = 0x20
SUB       = 0x21
MUL       = 0x22
DIV       = 0x23
IDIV      = 0x24
MOD       = 0x25
POW       = 0x26
NEG       = 0x27
INC_LOCAL = 0x28
DEC_LOCAL = 0x29
INC_OP    = 0x2A
DEC_OP    = 0x2B
CONCAT    = 0x2C

# --- 0x30 bitwise ---
BIT_AND = 0x30
BIT_OR  = 0x31
BIT_XOR = 0x32
BIT_NOT = 0x33
LSHIFT  = 0x34
RSHIFT  = 0x35

# --- 0x40 comparison / logic ---
CMP_EQ    = 0x40
CMP_NEQ   = 0x41
CMP_LT    = 0x42
CMP_GT    = 0x43
CMP_LE    = 0x44
CMP_GE    = 0x45
LOGIC_AND = 0x46
LOGIC_OR  = 0x47
LOGIC_NOT = 0x48
CMP_IS    = 0x49
INSTANCE_OF = 0x4A
TYPE_CHECK  = 0x4B
TYPEOF      = 0x4C

# --- 0x50 control flow ---
JUMP             = 0x50
JUMP_IF_TRUE     = 0x51
JUMP_IF_FALSE    = 0x52
JUMP_IF_NULL     = 0x53
JUMP_IF_NOT_NULL = 0x54
SETUP_LOOP       = 0x55
POP_LOOP         = 0x56
BREAK            = 0x57
CONTINUE         = 0x58
GOTO             = 0x59

# --- 0x60 calls / returns ---
CALL        = 0x60
CALL_METHOD = 0x61
CALL_STATIC = 0x62
CALL_SUPER  = 0x63
RETURN      = 0x64
RETURN_VOID = 0x65
YIELD       = 0x66
YIELD_FROM  = 0x67
TAIL_CALL   = 0x68

# --- 0x70 OOP ---
NEW_OBJECT      = 0x70
NEW_ARRAY       = 0x71
NEW_DICT        = 0x72
NEW_STRUCT      = 0x73
NEW_RECORD      = 0x74
DEFINE_CLASS    = 0x75
DEFINE_METHOD   = 0x76
DEFINE_FIELD    = 0x77
DEFINE_INTERFACE = 0x78
IMPLEMENT_IFACE = 0x79
EXTENDS_CLASS   = 0x7A
INVOKE_CTOR     = 0x7B
INVOKE_DTOR     = 0x7C
SET_ACCESS      = 0x7D
SET_STATIC      = 0x7E
SET_ABSTRACT    = 0x7F
SET_OVERRIDE    = 0x80
CAST            = 0x81
UNBOX           = 0x82
BOX             = 0x83

# --- 0x90 iterators ---
BUILD_RANGE      = 0x90
BUILD_RANGE_INCL = 0x91
GET_ITER         = 0x92
ITER_NEXT        = 0x93
ITER_CLOSE       = 0x94
BUILD_ENUMERATE  = 0x95
BUILD_ZIP        = 0x96
BUILD_REVERSED   = 0x97
UNPACK           = 0x98

# --- 0xA0 I/O & built-ins ---
CONSOLE_WRITE    = 0xA0
CONSOLE_WRITELN  = 0xA1
INPUT_READ       = 0xA2
MAP_CALL         = 0xA3
FILTER_CALL      = 0xA4
REDUCE_CALL      = 0xA5
ASSERT_CHECK     = 0xA6
PRINT_FMT        = 0xA7

# --- 0xB0 error handling ---
SETUP_TRY       = 0xB0
POP_TRY         = 0xB1
THROW           = 0xB2
RAISE           = 0xB3
SETUP_EXCEPT    = 0xB4
POP_EXCEPT      = 0xB5
SETUP_FINALLY   = 0xB6
POP_FINALLY     = 0xB7
PUSH_EXCEPTION  = 0xB8
MATCH_EXCEPTION = 0xB9

# --- 0xC0 concurrency ---
SPAWN_THREAD      = 0xC0
SPAWN_PROCESS     = 0xC1
SPAWN_COROUTINE   = 0xC2
AWAIT             = 0xC3
ASYNC_ENTER       = 0xC4
ASYNC_EXIT        = 0xC5
MUTEX_CREATE      = 0xC6
MUTEX_LOCK        = 0xC7
MUTEX_UNLOCK      = 0xC8
SEMAPHORE_CREATE  = 0xC9
SEMAPHORE_ACQUIRE = 0xCA
SEMAPHORE_RELEASE = 0xCB
SYNC_ENTER        = 0xCC
SYNC_EXIT         = 0xCD
LOCK_ENTER        = 0xCE
LOCK_EXIT         = 0xCF

# --- 0xD0 modules ---
IMPORT_MODULE   = 0xD0
IMPORT_FROM     = 0xD1
IMPORT_ALL      = 0xD2
IMPORT_AS       = 0xD3
EXPORT_SYMBOL   = 0xD4
LOAD_PACKAGE    = 0xD5
ENTER_NAMESPACE = 0xD6
EXIT_NAMESPACE  = 0xD7
RESOLVE_DCOLON  = 0xD8

# --- 0xE0 closures ---
MAKE_CLOSURE     = 0xE0
MAKE_LAMBDA      = 0xE1
CAPTURE_LOCAL    = 0xE2
CAPTURE_UPVALUE  = 0xE3
APPLY_DECORATOR  = 0xE4

# --- 0xF0 pattern matching ---
MATCH_START     = 0xF0
MATCH_LITERAL   = 0xF1
MATCH_BIND      = 0xF2
MATCH_GUARD     = 0xF3
MATCH_END       = 0xF4
MATCH_DESTRUCT  = 0xF5

# --- 0xF6 special / debug ---
HALT         = 0xF6
LINE_INFO    = 0xF7
DEBUG_BREAK  = 0xF8
META         = 0xF9
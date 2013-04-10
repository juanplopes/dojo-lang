# -*- coding:utf8 -*-
import functools, types, opcode, sys

BINARY_OPS = {
    '&': 'BINARY_AND',
    '|': 'BINARY_OR',
    '^': 'BINARY_XOR',
    '<<': 'BINARY_LSHIFT',
    '>>': 'BINARY_RSHIFT',
    '+': 'BINARY_ADD',
    '-': 'BINARY_SUBTRACT',
    '*': 'BINARY_MULTIPLY',
    '/': 'BINARY_TRUE_DIVIDE',
    '//': 'BINARY_FLOOR_DIVIDE',
    '**': 'BINARY_POWER',
    '%': 'BINARY_MODULO',
}

UNARY_OPS = {
    '+': 'UNARY_POSITIVE',
    '-': 'UNARY_NEGATIVE',
    'not': 'UNARY_NOT',
    '~': 'UNARY_INVERT',
}   

BOOLEAN_OPS = {
    'and': 'JUMP_IF_FALSE_OR_POP',
    'or': 'JUMP_IF_TRUE_OR_POP',
}

CO_GENERATOR = 0x0020

COMPOSE = lambda f, g: lambda *args, **kwargs: g(f(*args, **kwargs))

def dojo_emit(program, filename):
    code = CodeGenerator(
        codename='<root>',
        filename=filename,
        lineno=1,
        cellvars=program.cell,
        freevars=program.free)

    code.emit(program.body)
    return code.assemble()  

class CodeGenerator:
    def __init__(self, codename, filename, lineno, argnames=(), cellvars=(), freevars=()):
        self.argcount = len(argnames)
        self.consts = {}
        self.names = {}
        self.varnames = {name:i for i,name in enumerate(argnames)}
        self.cellvars = {name:i for i,name in enumerate(cellvars)}
        self.freevars = {name:i for i,name in enumerate(freevars)}
        self.code = []
        self.line = []
        self.filename = filename
        self.codename = codename
        self.lineno = lineno
        self.flags = 0

    def emit(self, e):
        emitter = getattr(self, 'emit_' + type(e).__name__)
        emitter(e)

    def emit_ListLiteral(self, e):
        for expr in e.exprs:
            self.emit(expr)
        self.emit_op(e.line, 'BUILD_LIST', len(e.exprs))

    def emit_DictLiteral(self, e):
        self.emit_op(e.line, 'BUILD_MAP', 0)
        for key, value in e.items:
            self.emit_op(key.line, 'DUP_TOP')
            self.emit(value)
            self.emit_op(value.line, 'ROT_TWO')
            self.emit(key)
            self.emit_op(value.line, 'STORE_SUBSCR')
    
    def emit_Literal(self, e):
        self.emit_op(e.line, 'LOAD_CONST', self.const(e.value))

    def emit_GetVariable(self, e):
        self.emit_var(e.line, 'LOAD', e.var)

    def emit_SetVariable(self, e):
        self.emit(e.expr)
        self.emit_op(e.line, 'DUP_TOP')
        self.emit_var(e.line, 'STORE', e.var)

    def emit_var(self, line, op, var):
        suffix, number = { 
            'local': ('_FAST', self.varname),
            'exported': ('_DEREF', self.deref),
            'closure': ('_DEREF', self.deref),
            'global': ('_GLOBAL', self.name)
        }[var.scope]

        self.emit_op(line, op + suffix, number(var.name))

    def emit_GetSubscript(self, e):
        self.emit(e.target)
        self.emit(e.index)
        self.emit_op(e.line, 'BINARY_SUBSCR')

    def emit_SetSubscript(self, e):
        self.emit(e.expr)
        self.emit_op(e.line, 'DUP_TOP')
        self.emit(e.target)
        self.emit(e.index)
        self.emit_op(e.line, 'STORE_SUBSCR')

    def emit_GetAttribute(self, e):
        self.emit(e.target)
        self.emit_op(e.line, 'LOAD_ATTR', self.name(e.name))

    def emit_SetAttribute(self, e):
        self.emit(e.value)
        self.emit(e.target)
        self.emit_op(e.line, 'STORE_ATTR', self.name(e.name))

    def emit_Slice(self, e):
        self.emit(e.start)
        self.emit(e.end)
        self.emit_op(e.line, 'BUILD_SLICE', 2)

    def emit_Return(self, e):
        self.emit(e.expr)
        self.emit_op(e.line, 'RETURN_VALUE')

    def emit_Yield(self, e):
        self.emit(e.expr)
        self.emit_op(e.line, 'YIELD_VALUE')
        self.flags |= CO_GENERATOR
        
    def emit_args(self, e):
        for arg in e.args:
            self.emit(arg)
        for key, arg in e.kwargs:
            self.emit_op(None, 'LOAD_CONST', self.const(key))
            self.emit(arg)
        
    def emit_PartialCall(self, e):
        self.emit_op(None, 'LOAD_CONST', self.const(functools.partial))
        self.emit(e.method)
        self.emit_args(e)
        self.emit_op(e.line, 'CALL_FUNCTION', self.two(len(e.args)+1, len(e.kwargs)))

    def emit_Composition(self, e):
        self.emit_op(None, 'LOAD_CONST', self.const(COMPOSE))
        self.emit(e.lhs)
        self.emit(e.rhs)
        self.emit_op(e.line, 'CALL_FUNCTION', self.two(2, 0))

    def emit_Call(self, e):
        self.emit(e.method)
        self.emit_args(e)
        self.emit_op(e.line, 'CALL_FUNCTION', self.two(len(e.args), len(e.kwargs)))

    def emit_PipeForward(self, e):
        self.emit(e.method)
        self.emit(e.arg)
        self.emit_op(e.line, 'CALL_FUNCTION', self.two(1, 0))

    def emit_BinaryOp(self, e):
        self.emit(e.lhs)
        self.emit(e.rhs)
        self.emit_op(e.line, BINARY_OPS[e.op])

    def emit_CompareOp(self, e):
        self.emit(e.lhs)
        self.emit(e.rhs)
        self.emit_op(e.line, 'COMPARE_OP', opcode.cmp_op.index(e.op))

    def emit_UnaryOp(self, e):
        self.emit(e.expr)
        self.emit_op(e.line, UNARY_OPS[e.op])

    def emit_BooleanOp(self, e):
        self.emit(e.lhs)
        patch = self.patch_point(e.line)
        self.emit(e.rhs)
        self.patch_op(patch, BOOLEAN_OPS[e.op], len(self.code))

    def emit_Function(self, e):
        gen = CodeGenerator(codename=e.name, 
                                  filename=self.filename,
                                  lineno = 1,
                                  argnames = e.args, 
                                  cellvars = e.cell,
                                  freevars = e.free)

        gen.emit(e.body)
        code = gen.assemble()

        if e.free:
            for var in e.free:
                self.emit_op(e.line, 'LOAD_CLOSURE', self.deref(var))
            self.emit_op(e.line, 'BUILD_TUPLE', len(e.free))
            self.emit_op(e.line, 'LOAD_CONST', self.const(code))
            self.emit_op(e.line, 'MAKE_CLOSURE', 0)
        else:
            self.emit_op(e.line, 'LOAD_CONST', self.const(code))
            self.emit_op(e.line, 'MAKE_FUNCTION', 0)

    def emit_If(self, e):
        self.emit(e.test)
        patch1 = self.patch_point(e.then_body.line)
        self.emit(e.then_body)
        patch2 = self.patch_point(e.else_body.line)
        self.patch_op(patch1, 'POP_JUMP_IF_FALSE', len(self.code))
        self.emit(e.else_body)
        self.patch_op(patch2, 'JUMP_ABSOLUTE', len(self.code))

    def emit_Import(self, e):
        self.emit_op(e.line, 'LOAD_CONST', self.const(-1))
        self.emit_op(e.line, 'LOAD_CONST', self.const(tuple(e.items)))
        self.emit_op(e.line, 'IMPORT_NAME', self.name(e.name))
        self.emit_op(e.line, 'DUP_TOP')
        
        if e.items:
            for item in e.items:
                self.emit_op(e.line, 'IMPORT_FROM', self.name(item))
                self.emit_op(e.line, 'STORE_GLOBAL', self.name(item))
        else:
            self.emit_op(e.line, 'STORE_GLOBAL', self.name(e.name))

    def emit_Block(self, e):
        if len(e.exprs):
            self.emit(e.exprs[0])

            for expr in e.exprs[1:]:
                self.emit_op(None, 'POP_TOP')
                self.emit(expr)
        else:
            self.emit_op(e.line, 'LOAD_CONST', self.const(None))

    def two(self, arg1, arg2):
        return arg2<<8 | arg1

    def emit_op(self, line, op, arg1=None):
        self.code.append(opcode.opmap[op])
        self.line.append(line)
        if arg1 != None:
            self.code.append(arg1&0xFF)
            self.line.append(None)
            self.code.append((arg1>>8)&0xFF)
            self.line.append(None)

    def patch_point(self, line):
        self.code += [0] * 6
        self.line += [line] + [None]*6
        return len(self.code)-6

    def patch_op(self, begin, op, arg):
        self.code[begin] = opcode.opmap['EXTENDED_ARG']
        self.code[begin+1] = (arg>>16)&0xFF
        self.code[begin+2] = (arg>>24)&0xFF
        self.code[begin+3] = opcode.opmap[op]
        self.code[begin+4] = (arg>>0)&0xFF
        self.code[begin+5] = (arg>>8)&0xFF

    def make_new(self, m, value):
        if value not in m:
            m[value] = len(m)
        return m[value]
        
    def const(self, value):
        return self.make_new(self.consts, value)

    def name(self, name):
        return self.make_new(self.names, name)

    def varname(self, name):
        return self.make_new(self.varnames, name)

    def deref(self, name):
        if name in self.cellvars:
            return self.cellvars[name]
        return self.freevars[name] + len(self.cellvars)

    def make_lnotab(self):
        current_line = self.lineno
        current_offset = 0
        lnotab = []
        
        for i, line in enumerate(self.line):
            if line is None: continue
            delta_line = line - current_line
            if delta_line <= 0: continue
            delta_offset = i - current_offset
            if delta_offset <= 0: continue
            
            current_line = line
            current_offset = i
            
            while delta_offset > 255:
                lnotab.append(255)
                lnotab.append(0)
                delta_offset -= 255
            while delta_line > 255:
                lnotab.append(delta_offset)
                lnotab.append(255)
                delta_line -= 255
                delta_offset = 0
            lnotab.append(delta_offset)
            lnotab.append(delta_line)
            
        return lnotab

    def assemble(self):
        make_tuple = lambda m: tuple(map(lambda x:x[0], sorted(m.items(), key=lambda x:x[1])))
        consts = make_tuple(self.consts)
        names = make_tuple(self.names)
        varnames = make_tuple(self.varnames)
        freevars = make_tuple(self.freevars)
        cellvars = make_tuple(self.cellvars)
        lnotab = self.make_lnotab()

        if sys.version_info >= (3, 0):
            return types.CodeType(self.argcount,
                            0,
                            len(self.varnames),
                            1000, 
                            self.flags, 
                            bytes(self.code + [opcode.opmap['RETURN_VALUE']]), 
                            consts, 
                            names, 
                            varnames, 
                            self.filename, 
                            self.codename or '<anonymous>', 
                            self.lineno, 
                            bytes(lnotab),
                            freevars,
                            cellvars)
        else:
            return types.CodeType(self.argcount,
                            len(self.varnames),
                            1000, 
                            self.flags, 
                            ''.join([chr(b) for b in self.code]) + chr(opcode.opmap['RETURN_VALUE']), 
                            consts, 
                            names, 
                            varnames, 
                            self.filename, 
                            self.codename or '<anonymous>', 
                            self.lineno, 
                            ''.join([chr(b) for b in lnotab]),
                            freevars,
                            cellvars)
    

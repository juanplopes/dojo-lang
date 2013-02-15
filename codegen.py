# -*- coding:utf8 -*-
import functools, types, opcode

BINARY_OPS = {
    '&': 'BINARY_AND',
    '|': 'BINARY_OR',
    '^': 'BINARY_XOR',
    '<<': 'BINARY_LSHIFT',
    '>>': 'BINARY_RSHIFT',
    '+': 'BINARY_ADD',
    '-': 'BINARY_SUBTRACT',
    '*': 'BINARY_MULTIPLY',
    '/': 'BINARY_DIVIDE',
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

def compose(f, g, unpack=False):
    def newfunc(*args, **kwargs):
        return g(f(*args, **kwargs))
      
    newfunc.func = g
    return newfunc

class CodeGenerator:
    def __init__(self, filename='<string>', lineno=1, argnames=(), root=True):
        self.argcount = len(argnames)
        self.consts = {}
        self.names = {}
        self.varnames = {name:i for i,name in enumerate(argnames)}
        self.code = []
        self.filename = filename
        self.lineno = lineno
        self.root = root

    def emit(self, e):
        emitter = getattr(self, 'emit_' + type(e).__name__)
        emitter(e)

    def emit_ListLiteral(self, e):
        for expr in e.exprs:
            self.emit(expr)
        self.emit_op('BUILD_LIST', len(e.exprs))

    def emit_DictLiteral(self, e):
        self.emit_op('BUILD_MAP', 0)
        for key, value in e.items:
            self.emit_op('DUP_TOP')
            self.emit(value)
            self.emit_op('ROT_TWO')
            self.emit(key)
            self.emit_op('STORE_SUBSCR')
    
    def emit_RangeLiteral(self, e):
        self.emit_op('LOAD_CONST', self.const(xrange))
        self.emit(e.begin)
        self.emit(e.end)
        if e.step:
            self.emit(e.step)
            self.emit_op('CALL_FUNCTION', 3, 0)
        else:
            self.emit_op('CALL_FUNCTION', 2)
    
    def emit_Literal(self, e):
        self.emit_op('LOAD_CONST', self.const(e.value))

    def emit_VariableGet(self, e):
        idx = self.varname(e.name)
        if idx != None:
            self.emit_op('LOAD_FAST', idx)        
        else:
            self.emit_op('LOAD_NAME', self.name(e.name))

    def emit_VariableSet(self, e):
        self.emit(e.expr)
        self.emit_op('DUP_TOP')
        idx = self.varname(e.name)
        if idx:
            self.emit_op('STORE_FAST', idx)        
        else:
            self.emit_op('STORE_NAME', self.name(e.name))

    def emit_ItemGet(self, e):
        self.emit(e.target)
        self.emit(e.index)
        self.emit_op('BINARY_SUBSCR')

    def emit_ItemSet(self, e):
        self.emit(e.expr)
        self.emit_op('DUP_TOP')
        self.emit(e.target)
        self.emit(e.index)
        self.emit_op('STORE_SUBSCR')

    def emit_Slice(self, e):
        self.emit(e.start)
        self.emit(e.end)
        self.emit(e.step)
        self.emit_op('BUILD_SLICE', 3)

    def emit_Return(self, e):
        self.emit(e.expr)
        self.emit_op('RETURN_VALUE')

    def emit_PartialCall(self, e):
        self.emit_op('LOAD_CONST', self.const(functools.partial))
        self.emit(e.method)
        for arg in e.args:
            self.emit(arg)
        self.emit_op('CALL_FUNCTION', len(e.args)+1, 0)

    def emit_Composition(self, e):
        self.emit_op('LOAD_CONST', self.const(compose))
        self.emit(e.lhs)
        self.emit(e.rhs)
        self.emit_op('CALL_FUNCTION', 2, 0)

    def emit_Call(self, e):
        self.emit(e.method)
        for arg in e.args:
            self.emit(arg)
        self.emit_op('CALL_FUNCTION', len(e.args), 0)

    def emit_PipeForward(self, e):
        self.emit(e.method)
        self.emit(e.arg)
        self.emit_op('CALL_FUNCTION', 1, 0)

    def emit_BinaryOp(self, e):
        self.emit(e.lhs)
        self.emit(e.rhs)
        self.emit_op(BINARY_OPS[e.op])

    def emit_CompareOp(self, e):
        self.emit(e.lhs)
        self.emit(e.rhs)
        self.emit_op('COMPARE_OP', opcode.cmp_op.index(e.op))

    def emit_UnaryOp(self, e):
        self.emit(e.expr)
        self.emit_op(UNARY_OPS[e.op])

    def emit_BooleanOp(self, e):
        self.emit(e.lhs)
        critical = self.emit_op('NOP', 0)
        self.emit(e.rhs)
        self.patch_op(critical, BOOLEAN_OPS[e.op], len(self.code))

    def emit_Function(self, e):
        body_code = CodeGenerator(argnames = e.args)
        body_code.emit(e.body)
        self.emit_op('LOAD_CONST', self.const(body_code.assemble()))
        self.emit_op('MAKE_FUNCTION', 0)

    def emit_MemberGet(self, e):
        self.emit(e.target)
        self.emit_op('LOAD_ATTR', self.name(e.name))

    def emit_MemberSet(self, e):
        self.emit(e.value)
        self.emit(e.target)
        self.emit_op('STORE_ATTR', self.name(e.name))

    def emit_Import(self, e):
        self.emit_op('LOAD_CONST', self.const(-1))
        self.emit_op('LOAD_CONST', self.const(tuple(e.items)))
        self.emit_op('IMPORT_NAME', self.name(e.name))
        self.emit_op('DUP_TOP')
        
        if '*' in e.items:
            self.emit_op('IMPORT_STAR')
        elif e.items:
            for item in e.items:
                self.emit_op('IMPORT_FROM', self.name(item))
                self.emit_op('STORE_NAME', self.name(item))
        else:
            self.emit_op('STORE_NAME', self.name(e.name))

    def emit_Block(self, e):
        if len(e.exprs):
            self.emit(e.exprs[0])

            for expr in e.exprs[1:]:
                self.emit_op('POP_TOP')
                self.emit(expr)
        else:
            self.emit_op('LOAD_CONST', self.const(None))

    def emit_op(self, op, arg1=None, arg2=None):
        begin = len(self.code)
        self.code.append(opcode.opmap[op])
        if arg1 != None:
            self.code.append(arg1&0xFF)
            self.code.append((arg2 if arg2 else arg1>>8)&0xFF)
        return begin

    def patch_op(self, begin, op, arg1=None, arg2=None):
        self.code[begin] = opcode.opmap[op]
        if arg1 != None:
            self.code[begin+1] = arg1&0xFF
            self.code[begin+2] = (arg2 if arg2 else arg1>>8)&0xFF

    def make_new(self, m, value):
        if value not in m:
            m[value] = len(m)
        return m[value]
        
    def const(self, value):
        return self.make_new(self.consts, value)

    def varname(self, name, write=False):
        if write:
            return self.make_new(self.varnames, name)
        else:
            return self.varnames.get(name)

    def name(self, name):
        return self.make_new(self.names, name)

    def assemble(self):
        make_tuple = lambda m: tuple(map(lambda x:x[0], sorted(m.items(), key=lambda x:x[1])))
        consts = make_tuple(self.consts)
        names = make_tuple(self.names)
        varnames = make_tuple(self.varnames)
        code = ''.join([chr(b) for b in self.code]) + chr(opcode.opmap['RETURN_VALUE'])
        return types.CodeType(self.argcount, 
                        len(self.varnames), 
                        1000, 
                        0, 
                        code, 
                        consts, 
                        names, 
                        varnames, 
                        self.filename, 
                        self.filename, 
                        self.lineno, 
                        '')
    
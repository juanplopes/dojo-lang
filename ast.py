# -*- coding:utf8 -*-
from types import CodeType
from opcode import opmap, cmp_op

class CodeBuilder:
    def __init__(self, filename='<string>', lineno=1, argnames=(), root=True):
        self.argcount = len(argnames)
        self.consts = {}
        self.names = {}
        self.varnames = {name:i for i,name in enumerate(argnames)}
        self.code = []
        self.filename = filename
        self.lineno = lineno
        self.root = root

    def emit(self, op, arg1=None, arg2=None):
        self.code.append(opmap[op])
        if arg1 != None:
            self.code.append(arg1&0xFF)
            self.code.append((arg2 if arg2 else arg1>>8)&0xFF)

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

    def push(self):
        return CodeBuilder(self.filename, self.lineno, (), False)

    def build(self):
        make_tuple = lambda m: tuple(map(lambda x:x[0], sorted(m.items(), key=lambda x:x[1])))
        consts = make_tuple(self.consts)
        names = make_tuple(self.names)
        varnames = make_tuple(self.varnames)
        code = ''.join([chr(b) for b in self.code]) + chr(opmap['RETURN_VALUE'])
        return CodeType(self.argcount, 
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

class Expression(object):
    def to_code(self):
        builder = CodeBuilder()
        self.emit(builder)
        return builder.build()

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class ListLiteral(Expression):
    def __init__(self, exprs):
        self.exprs = exprs

    def emit(self, code):
        for expr in self.exprs:
            expr.emit(code)
        code.emit('BUILD_LIST', len(self.exprs))

class DictLiteral(Expression):
    def __init__(self, items):
        self.items = items

    def emit(self, code):
        code.emit('BUILD_MAP', 0)
        for key, value in self.items:
            code.emit('DUP_TOP')
            value.emit(code)
            code.emit('ROT_TWO')
            key.emit(code)
            code.emit('STORE_SUBSCR')


class RangeLiteral(object):
    def __init__(self, begin, end, step):
        self.begin = begin
        self.end = end
        self.step = step

    def __call__(self, scope):
        if self.step:
            return xrange(self.begin(scope), self.end(scope), self.step(scope))
        else:
            return xrange(self.begin(scope), self.end(scope))

class Literal(Expression):
    def __init__(self, value):
        self.value = value

    def emit(self, code):
        code.emit('LOAD_CONST', code.const(self.value))

class VariableGet(Expression):
    def __init__(self, name):
        self.name = name

    def emit(self, code):
        idx = code.varname(self.name)
        if idx!=None:
            code.emit('LOAD_FAST', idx)        
        else:
            code.emit('LOAD_NAME', code.name(self.name))
        
    def to_assignment(self, expr):
        return VariableSet(self.name, expr)

class VariableSet(Expression):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

    def emit(self, code):
        self.expr.emit(code)
        code.emit('DUP_TOP')
        idx = code.varname(self.name)
        if idx:
            code.emit('STORE_FAST', idx)        
        else:
            code.emit('STORE_NAME', code.name(self.name))

class MemberGet(object):
    def __init__(self, target, name):
        self.target = target
        self.name = name

    def __call__(self, scope):
        return getattr(self.target(scope), self.name)

    def to_assignment(self, expr):
        return MemberSet(self.target, self.name, expr)

class MemberSet(object):
    def __init__(self, target, name, value):
        self.target = target
        self.name = name
        self.value = value

    def __call__(self, scope):
        return setattr(self.target(scope), self.name, self.value(scope))
    
class ItemGet(object):
    def __init__(self, target, index):
        self.target = target
        self.index = index

    def __call__(self, scope):
        return self.target(scope).__getitem__(self.index(scope))

    def to_assignment(self, expr):
        return ItemSet(self.target, self.index, expr)


class ItemSet(object):
    def __init__(self, target, index, expr):
        self.target = target
        self.index = index
        self.expr = expr

    def __call__(self, scope):
        return self.target(scope).__setitem__(self.index(scope), self.expr(scope))

class Slice(object):
    def __init__(self, start, end, step):
        self.start = start
        self.end = end
        self.step = step

    def __call__(self, scope):
        return slice(self.start(scope), self.end(scope), self.step(scope))

class Return(Expression):
    def __init__(self, expr):
        self.expr = expr

    def emit(self, code):
        self.expr.emit(code)
        code.emit('RETURN_VALUE')
    
class Call(object):
    def __init__(self, method, args):
        self.method = method
        self.args = args

    def emit(self, code):
        self.method.emit(code)
        for arg in self.args:
            arg.emit(code)
        code.emit('CALL_FUNCTION', len(self.args), 0)
    
class PipeForward(object):
    def __init__(self, arg, method):
        self.arg = arg
        self.method = method

    def __call__(self, scope):
        return self.method(scope)(self.arg(scope))

class Composition(object):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __call__(self, scope):
        def y(*args):
            return self.rhs(scope)(self.lhs(scope)(*args))
        return y

class PartialCall(object):
    def __init__(self, method, args):
        self.method = method
        self.args = args

    def __call__(self, scope):
        pre=tuple(arg(scope) for arg in self.args)
        def y(*args):
            return self.method(scope)(*(pre+args))
        return y

class Binary(Expression):
    OPS = {
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

    def __init__(self, op, lhs, rhs):
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

    def emit(self, code):
        self.lhs.emit(code)
        self.rhs.emit(code)
        code.emit(Binary.OPS[self.op])
    
class Compare(Expression):
    def __init__(self, op, lhs, rhs):
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

    def emit(self, code):
        self.lhs.emit(code)
        self.rhs.emit(code)
        code.emit('COMPARE_OP', cmp_op.index(self.op))
    
class And(object):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __call__(self, scope):
        return self.lhs(scope) and self.rhs(scope)
        
class Or(object):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __call__(self, scope):
        return self.lhs(scope) or self.rhs(scope)
    
class UnaryExpression(Expression):
    OPS = {
        '+': 'UNARY_POSITIVE',
        '-': 'UNARY_NEGATIVE',
        'not': 'UNARY_NOT',
        '~': 'UNARY_INVERT',
    }    

    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

    def emit(self, code):
        self.expr.emit(code)
        code.emit(UnaryExpression.OPS[self.op])

class Function(Expression):
    def __init__(self, args, body):
        self.args = args
        self.body = body

    def emit(self, code):
        body_code = CodeBuilder(argnames = self.args)
        self.body.emit(body_code)
        code.emit('LOAD_CONST', code.const(body_code.build()))
        code.emit('MAKE_FUNCTION', 0)

class ModuleImport(object):
    def __init__(self, name, items):
        self.name = name
        self.items = items

    def __call__(self, scope):
        module = __import__(self.name, globals(), locals(), self.items)
        if len(self.items):
            for item in self.items:
                scope.put(item, getattr(module, item))
        else:
            scope.put(self.name, module)
        
        return module
        

class Block(Expression):
    def __init__(self, exprs):
        self.exprs = exprs

    def emit(self, code):
        exprs = self.exprs
        
        if len(exprs):
            exprs[0].emit(code)

            for expr in exprs[1:]:
                code.emit('POP_TOP')
                expr.emit(code)
        else:
            code.emit('LOAD_CONST', code.const(None))

    def __call__(self, globals = None, locals = None):
        return eval(self.to_code(), globals, locals)


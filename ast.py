# -*- coding:utf8 -*-
from types import CodeType
from opcode import opmap

class CodeBuilder:
    def __init__(self):
        self.consts = {}
        self.code = []

    def emit(self, op, arg=None):
        self.code.append(opmap[op])
        if arg != None:
            self.code.append(arg&0xFF)
            self.code.append((arg>>8)&0xFF)

    def const(self, value):
        if value not in self.consts:
            self.consts[value] = len(self.consts)
        return self.consts[value]

    def build(self):
        consts = tuple(map(lambda x:x[0], sorted(self.consts.items(), key=lambda x:x[1])))
        code = ''.join([chr(b) for b in self.code]) + chr(opmap['RETURN_VALUE'])
        #print consts, map(ord, code)
        return CodeType(0, 0, 1, 0, code, consts, (), (), 'test', 'test', 1, '')

class Expression(object):
    def to_code(self):
        builder = CodeBuilder()
        self.emit(builder)
        return builder.build()

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class ListLiteral(object):
    def __init__(self, exprs):
        self.exprs = exprs

    def __call__(self, scope):
        return [expr(scope) for expr in self.exprs]

class DictLiteral(object):
    def __init__(self, items):
        self.items = items

    def __call__(self, scope):
        return {key(scope):value(scope) for key, value in self.items}


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

class VariableGet(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, scope):
        return scope.get(self.name)
        
    def to_assignment(self, expr):
        return VariableSet(self.name, expr)

class VariableSet(object):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

    def __call__(self, scope):
        value = self.expr(scope)
        scope.put(self.name, value)
        return value

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

class Return(object):
    def __init__(self, expr):
        self.expr = expr

    def __call__(self, scope):
        raise ReturnException(self.expr(scope))

    
class Call(object):
    def __init__(self, method, args):
        self.method = method
        self.args = args

    def __call__(self, scope):
        return self.method(scope)(*[arg(scope) for arg in self.args])
    
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

class BinaryExpression(Expression):
    OPS = {
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
        code.emit(BinaryExpression.OPS[self.op])
    
class AndExpression(object):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __call__(self, scope):
        return self.lhs(scope) and self.rhs(scope)
        
class OrExpression(object):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __call__(self, scope):
        return self.lhs(scope) or self.rhs(scope)
    
class UnaryExpression(object):
    OPS = {
        '+': 'UNARY_POSITIVE',
        '-': 'UNARY_NEGATIVE',
    }    

    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

    def emit(self, code):
        self.expr.emit(code)
        code.emit(UnaryExpression.OPS[self.op])

class Function(object):
    def __init__(self, args, body):
        self.args = args
        self.body = body

    def __call__(self, scope):
        def y(*args):
            my_scope = scope.push()
            for name, value in izip(self.args, args):
                my_scope.put(name, value)
            try:
                return self.body(my_scope)            
            except ReturnException as e:
                return e.value
        return y

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



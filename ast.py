# -*- coding:utf8 -*-

class LexicalContext(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.variables = {}

    def ensure(self, name, scope):
        var = Variable(self, name, scope)
        self.variables[name] = var
        return var
      
    def request(self, name, level=0):
        if name in self.variables:
            var = self.variables[name]
            if var.scope =='local' and level > 0: 
                var.scope = 'exported'
            return var

        if self.parent:
            var = self.parent.request(name, level+1)
            if var.scope in ('exported', 'closure'):
                return self.ensure(var.name, 'closure')
            else:
                return Variable(self, var.name, var.scope)

        return Variable(self, name, 'global')

    def assign(self, name):
        var = self.request(name)
        if var.scope == 'global':
            var = Variable(self, name, 'local')
            self.variables[name] = var
            return var
        return var

    def push(self, args):
        ctx = LexicalContext(self)
        for arg in args:
            ctx.ensure(arg, 'local')
        return ctx

    def varnames(self, of_type):
        return [var.name for var in self.variables.values() if var.scope == of_type]

class Variable(object):
    def __init__(self, context, name, scope):
        self.context = context
        self.name = name
        self.scope = scope

    def to_assignment(self):
        return self.context.assign(self.name)

class Program(object):
    def __init__(self, body, cell, free):
        self.body = body
        self.cell = cell
        self.free = free

class Block(object):
    def __init__(self, exprs=[]):
        self.exprs = exprs

class Literal(object):
    def __init__(self, value):
        self.value = value

class ListLiteral(object):
    def __init__(self, exprs):
        self.exprs = exprs

class DictLiteral(object):
    def __init__(self, items):
        self.items = items

class RangeLiteral(object):
    def __init__(self, begin, end, step):
        self.begin = begin
        self.end = end
        self.step = step

class GetVariable(object):
    def __init__(self, var):
        self.var = var
                
    def to_assignment(self, expr):
        return SetVariable(self.var.to_assignment(), expr)

class SetVariable(object):
    def __init__(self, var, expr):
        self.var = var
        self.expr = expr

class GetAttribute(object):
    def __init__(self, target, name):
        self.target = target
        self.name = name

    def to_assignment(self, expr):
        return SetAttribute(self.target, self.name, expr)

class SetAttribute(object):
    def __init__(self, target, name, value):
        self.target = target
        self.name = name
        self.value = value
    
class GetSubscript(object):
    def __init__(self, target, index):
        self.target = target
        self.index = index

    def to_assignment(self, expr):
        return SetSubscript(self.target, self.index, expr)

class SetSubscript(object):
    def __init__(self, target, index, expr):
        self.target = target
        self.index = index
        self.expr = expr

class Slice(object):
    def __init__(self, start, end, step):
        self.start = start
        self.end = end
        self.step = step

class Return(object):
    def __init__(self, expr):
        self.expr = expr
   
class Yield(object):
    def __init__(self, expr):
        self.expr = expr
    
class Call(object):
    def __init__(self, method, args):
        self.method = method
        self.args = args
    
class PipeForward(object):
    def __init__(self, arg, method):
        self.arg = arg
        self.method = method

class Composition(object):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

class PartialCall(object):
    def __init__(self, method, args):
        self.method = method
        self.args = args

class BinaryOp(object):
    def __init__(self, op, lhs, rhs):
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

class CompareOp(object):
    def __init__(self, op, lhs, rhs):
        self.op = op
        self.lhs = lhs
        self.rhs = rhs
    
class BooleanOp(object):
    def __init__(self, op, lhs, rhs):
        self.op = op
        self.lhs = lhs
        self.rhs = rhs
    
class UnaryOp(object):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

class If(object):
    def __init__(self, test, then_body, else_body):
        self.test = test
        self.then_body = then_body
        self.else_body = else_body

class Function(object):
    def __init__(self, name, args, body, cell, free):
        self.name = name
        self.args = args
        self.body = body
        self.cell = cell
        self.free = free

class Import(object):
    def __init__(self, name, items):
        self.name = name
        self.items = items

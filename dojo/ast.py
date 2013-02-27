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
    def __init__(self, line, body, cell, free):
        self.line = line
        self.body = body
        self.cell = cell
        self.free = free

class Block(object):
    def __init__(self, line, exprs=[]):
        self.line = line
        self.exprs = exprs


class Literal(object):
    def __init__(self, line, value):
        self.line = line
        self.value = value


class ListLiteral(object):
    def __init__(self, line, exprs):
        self.line = line
        self.exprs = exprs


class DictLiteral(object):
    def __init__(self, line, items):
        self.line = line
        self.items = items


class GetVariable(object):
    def __init__(self, line, var):
        self.line = line
        self.var = var

    def to_assignment(self, expr):
        return SetVariable(self.line, self.var.to_assignment(), expr)

class SetVariable(object):
    def __init__(self, line, var, expr):
        self.line = line
        self.var = var
        self.expr = expr


class GetAttribute(object):
    def __init__(self, line, target, name):
        self.line = line
        self.target = target
        self.name = name

    def to_assignment(self, expr):
        return SetAttribute(self.line, self.target, self.name, expr)

class SetAttribute(object):
    def __init__(self, line, target, name, value):
        self.line = line
        self.target = target
        self.name = name
        self.value = value


class GetSubscript(object):
    def __init__(self, line, target, index):
        self.line = line
        self.target = target
        self.index = index

    def to_assignment(self, expr):
        return SetSubscript(self.line, self.target, self.index, expr)

class SetSubscript(object):
    def __init__(self, line, target, index, expr):
        self.line = line
        self.target = target
        self.index = index
        self.expr = expr


class Slice(object):
    def __init__(self, line, start, end):
        self.line = line
        self.start = start
        self.end = end


class Return(object):
    def __init__(self, line, expr):
        self.line = line
        self.expr = expr


class Yield(object):
    def __init__(self, line, expr):
        self.line = line
        self.expr = expr


class Call(object):
    def __init__(self, line, method, args):
        self.line = line
        self.method = method
        self.args = args


class PipeForward(object):
    def __init__(self, line, arg, method):
        self.line = line
        self.arg = arg
        self.method = method


class Composition(object):
    def __init__(self, line, lhs, rhs):
        self.line = line
        self.lhs = lhs
        self.rhs = rhs


class PartialCall(object):
    def __init__(self, line, method, args):
        self.line = line
        self.method = method
        self.args = args


class BinaryOp(object):
    def __init__(self, line, op, lhs, rhs):
        self.line = line
        self.op = op
        self.lhs = lhs
        self.rhs = rhs


class CompareOp(object):
    def __init__(self, line, op, lhs, rhs):
        self.line = line
        self.op = op
        self.lhs = lhs
        self.rhs = rhs


class BooleanOp(object):
    def __init__(self, line, op, lhs, rhs):
        self.line = line
        self.op = op
        self.lhs = lhs
        self.rhs = rhs


class UnaryOp(object):
    def __init__(self, line, op, expr):
        self.line = line
        self.op = op
        self.expr = expr


class If(object):
    def __init__(self, line, test, then_body, else_body):
        self.line = line
        self.test = test
        self.then_body = then_body
        self.else_body = else_body


class Function(object):
    def __init__(self, line, name, args, body, cell, free):
        self.line = line
        self.name = name
        self.args = args
        self.body = body
        self.cell = cell
        self.free = free


class Import(object):
    def __init__(self, line, name, items):
        self.line = line
        self.name = name
        self.items = items

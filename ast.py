# -*- coding:utf8 -*-

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
    def __init__(self, name):
        self.name = name
        
    def to_assignment(self, expr):
        return SetVariable(self.name, expr)

class SetVariable(object):
    def __init__(self, name, expr):
        self.name = name
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
    def __init__(self, name, args, body):
        self.name = name
        self.args = args
        self.body = body

class Import(object):
    def __init__(self, name, items):
        self.name = name
        self.items = items

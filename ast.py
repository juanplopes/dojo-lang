# -*- coding:utf8 -*-

class Block(object):
    def __init__(self, exprs):
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

    def __call__(self, scope):
        if self.step:
            return xrange(self.begin(scope), self.end(scope), self.step(scope))
        else:
            return xrange(self.begin(scope), self.end(scope))

class VariableGet(object):
    def __init__(self, name):
        self.name = name
        
    def to_assignment(self, expr):
        return VariableSet(self.name, expr)

class VariableSet(object):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

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
    
class Call(object):
    def __init__(self, method, args):
        self.method = method
        self.args = args
    
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
    
class AndAlso(object):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __call__(self, scope):
        return self.lhs(scope) and self.rhs(scope)
        
class OrElse(object):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __call__(self, scope):
        return self.lhs(scope) or self.rhs(scope)
    
class UnaryOp(object):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

class Function(object):
    def __init__(self, args, body):
        self.args = args
        self.body = body

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
        



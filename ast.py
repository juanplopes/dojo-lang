# -*- coding:utf8 -*-
import types

class Scope(object):
    def __init__(self, data=None, parent=None):
        self.parent = parent
        self.data = data or {}

    def get(self, name):
        if name in self.data: return self.data[name]
        if self.parent: return self.parent.get(name)
        return None
       
    def put(self, name, value):
        self.data[name] = value

    def push(self):
        return Scope(parent=self)

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class ListLiteral(object):
    def __init__(self, exprs):
        self.exprs = exprs

    def __call__(self, scope):
        return [expr(scope) for expr in self.exprs]

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

class Literal(object):
    def __init__(self, value):
        self.value = value

    def __call__(self, scope):
        return self.value

class VariableGet(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, scope):
        return scope.get(self.name)

class VariableSet(object):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

    def __call__(self, scope):
        value = self.expr(scope)
        scope.put(self.name, value)
        return value

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
    

class BinaryExpression(object):
    def __init__(self, op, lhs, rhs):
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

    def __call__(self, scope):
        return self.op(self.lhs(scope), self.rhs(scope))
    
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
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

    def __call__(self, scope):
        return self.op(self.expr(scope))

class Function(object):
    def __init__(self, args, body):
        self.args = args
        self.body = body

    def __call__(self, scope):
        def y(*args):
            my_scope = scope.push()
            for name, value in zip(self.args, args):
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
                scope.put(item, module.__getattribute__(item))
        else:
            scope.put(self.name, module)
        
        return module
        

class Program(object):
    def __init__(self, exprs):
        self.exprs = exprs

    def __call__(self, scope = None):
        result = None
        scope = scope or Scope()
        try:
            for expr in self.exprs:
                result = expr(scope)
            return result
        except ReturnException as e:
            return e.value


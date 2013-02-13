# -*- coding:utf8 -*-

class Scope(object):
    def __init__(self, data=None, parent=None):
        self.parent = parent
        self.data = data or {}

    def get(self, name):
        if name in self.data: return self.data[name]
        if self.parent: return self.parent.get(name)
        raise NameError("name '{}' is not defined".format(name))
       
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
        def y(*args):
            return self.method(scope)(*([arg(scope) for arg in self.args]+list(args)))
        return y

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
                scope.put(item, getattr(module, item))
        else:
            scope.put(self.name, module)
        
        return module
        

class Block(object):
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


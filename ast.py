class Scope(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.data = {}

    def get(self, name):
        if name in self.data: return self.data[name]
        if self.parent: return self.parent.get(name)
        return None
        
    def put(self, name, value):
        self.data[name] = value
        
    def push(self):
        return Scope(self)

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
        return scope.put(self.name, self.expr(scope))

    
class MethodCall(object):
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
    
class UnaryExpression(object):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

    def __call__(self, scope):
        return self.op(self.expr(scope))

class Program(object):
    def __init__(self, exprs):
        self.exprs = exprs

    def __call__(self, scope = None):
        result = None
        for expr in self.exprs:
            result = expr(scope or Scope())
        return result


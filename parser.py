# -*- coding:utf8 -*-
from __future__ import print_function
from ast import *
from scanner import *
        
def parse(expression):
    tokens = Scanner(expression, 
                     '+', '-', '*', '/', '**', '%', '(', ')', '[', ']', '{', '}',
                     'return', '==', '!=', ',', '=', '@', ';', ':', '..',
                     '<', '<=', '>', '>=', '~', 'and', 'or', 'not', 'import',
                     '<<', '>>', '&', '|', '^', '|>', '=>', 'in', 'not in', '.',
                     INTEGER = r'[0-9]+', 
                     FLOAT = r'[0-9]*\.[0-9]+', 
                     IDENTIFIER = r'[a-zA-Z][a-zA-Z0-9]*',
                     STRING = '|'.join([r'("([^\\"]|\\.)*")',r"('([^\\']|\\.)*')"]),
                     EOF = r'$')

    def _binary(higher, ops):
        def walk():
            e = higher()        
            while tokens.maybe(*ops, stop_on_lf=True):
                e = BinaryExpression(ops[tokens.next(*ops).name], e, higher())
            return e
        return walk

    def _raw(higher, ops):
        def walk():
            e = higher()
            while tokens.maybe(*ops):
                e = ops[tokens.next(*ops).name](e, higher())
            return e
        return walk

    def _unary(higher, ops):
        def walk():
            if tokens.maybe(*ops):
                return UnaryExpression(ops[tokens.next(*ops).name], walk())
            return higher()
        return walk
    
    def _list_of(what, until):
        args = []
        if not tokens.maybe(until):
            args.append(what())
            while tokens.next_if(',') and not tokens.maybe(until):
                args.append(what())
        tokens.next(until)
        return args 
 
    def block(until):
        exprs = []
        while tokens.ignore(',', ';') and not tokens.next_if(until):
            exprs.append(expr())
        return Block(exprs)

    def expr():
        return return_expression()

    def return_expression():
        if tokens.next_if('return'):
            return Return(expr())
        return assignment()

    def assignment():
        to = import_expression()
        if hasattr(to, 'to_assignment') and tokens.next_if('='):
            value = expr()
            return to.to_assignment(value)
        return to

    def import_expression():
        if tokens.next_if('import'):
            name = tokens.next('IDENTIFIER').image
            items = []        
            if tokens.next_if('(', stop_on_lf=True):
                items = _list_of(lambda: tokens.next('IDENTIFIER').image, ')')
            return ModuleImport(name, items)
        return function()

    def function():
        if tokens.next_if('@'):
            args = _list_of(lambda: tokens.next('IDENTIFIER').image, ':')
            body = expr()
            return Function(args, body)
        return ops()

    ops = lambda: range_literal()
    ops = _unary(ops, {'-' : lambda x:-x, '~': lambda x: ~x })
    ops = _binary(ops, {'**': lambda x,y:x**y})
    ops = _binary(ops, {'*': lambda x,y:x*y, '/': lambda x,y:x/y, '%': lambda x,y:x%y})
    ops = _binary(ops, {'+': lambda x,y:x+y, '-': lambda x,y:x-y})
    ops = _binary(ops, {'<<': lambda x,y:x<<y, '>>': lambda x,y:x>>y})
    ops = _binary(ops, {'&': lambda x,y:x&y})
    ops = _binary(ops, {'^': lambda x,y:x^y})
    ops = _binary(ops, {'|': lambda x,y:x|y})
    ops = _binary(ops, {'==': lambda x,y: x==y, '!=': lambda x,y: x!=y})
    ops = _binary(ops, {'<': lambda x,y: x<y, '>': lambda x,y: x>y})
    ops = _binary(ops, {'<=': lambda x,y: x<=y, '>=': lambda x,y: x>=y})
    ops = _binary(ops, {'in': lambda x,y: x in y, 'not in': lambda x,y: x not in y})
    ops = _unary(ops, {'not': lambda x: not x})
    ops = _raw(ops, {'and': AndExpression})
    ops = _raw(ops, {'or': OrExpression})
    ops = _raw(ops, {'=>': Composition})
    ops = _raw(ops, {'|>': PipeForward})

    def range_literal():
        begin = call()
        if tokens.next_if('..'):
            end = call()
            step = call() if tokens.next_if(':') else None
            return RangeLiteral(begin, end, step)
        return begin
 
    def call():
        e = member_access()
        while tokens.maybe('(', '{', stop_on_lf=True):
            e = tokens.expect({
                    '(': lambda x: Call(e, _list_of(expr, ')')),
                    '{': lambda x: PartialCall(e, _list_of(expr, '}'))}) 
        return e

    def member_access():
        e = primary()
        if tokens.next_if('.'):
            member = tokens.next('IDENTIFIER')
            return MemberAccess(e, member.image)
        return e

    def primary():
        return tokens.expect({
            'INTEGER': lambda x: Literal(int(x.image)),
            'FLOAT': lambda x: Literal(float(x.image)),
            'STRING': lambda x: Literal(x.image[1:-1].decode('string-escape')),
            'IDENTIFIER': lambda x: VariableGet(x.image),
            '(': lambda x: block(')'),
            '[': lambda x: ListLiteral(_list_of(expr, ']'))}) 
        
    return block('EOF')
    
if __name__ == '__main__':
    import sys, __builtin__
    
    def read(prompt): 
        return raw_input(prompt)

    def write(*messages):
        print(*messages)
    
    with open(sys.argv[1]) as f:
        data = f.read()
        scope = Scope(__builtin__.__dict__)
        scope.put('read', read)
        scope.put('write', write)
        parse(data)(scope)  


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
                     IDENTIFIER = r'[_a-zA-Z][_a-zA-Z0-9]*',
                     STRING = '|'.join([r'("([^\\"]|\\.)*")',r"('([^\\']|\\.)*')"]),
                     EOF = r'$')

    def _binary(higher, *ops):
        def walk():
            e = higher()        
            while tokens.maybe(*ops, stop_on_lf=True):
                e = BinaryExpression(tokens.next(*ops).name, e, higher())
            return e
        return walk

    def _raw(higher, *ops):
        def walk():
            e = higher()
            while tokens.maybe(*ops):
                e = ops[tokens.next(*ops).name](e, higher())
            return e
        return walk

    def _unary(higher, *ops):
        def walk():
            if tokens.maybe(*ops):
                return UnaryExpression(tokens.next(*ops).name, walk())
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
    ops = _unary(ops, '-', '+', '~')
    ops = _binary(ops, '**')
    ops = _binary(ops, '*', '/', '%')
    ops = _binary(ops, '+', '-')
    ops = _binary(ops, '<<', '>>')
    ops = _binary(ops, '&')
    ops = _binary(ops, '^')
    ops = _binary(ops, '|')
    ops = _binary(ops, '==', '!=', '<', '>', '<=', '>=')
    ops = _binary(ops, 'in', 'not in')
    ops = _unary(ops, 'not')
    ops = _raw(ops, 'and')
    ops = _raw(ops, 'or')
    ops = _raw(ops, '=>')
    ops = _raw(ops, '|>')

    def range_literal():
        begin = call()
        if tokens.next_if('..'):
            end = call()
            step = call() if tokens.next_if(':') else None
            return RangeLiteral(begin, end, step)
        return begin
 
    def call():
        e = member_get()
        while tokens.maybe('(', '{', stop_on_lf=True):
            e = tokens.expect({
                    '(': lambda x: Call(e, _list_of(expr, ')')),
                    '{': lambda x: PartialCall(e, _list_of(expr, '}'))}) 
        return e

    def member_get():
        e = item_slice()
        while tokens.next_if('.'):
            member = tokens.next('IDENTIFIER')
            e = MemberGet(e, member.image)
        return e
        
    def item_slice():
        e = primary()

        while tokens.next_if('[', stop_on_lf=True):
            v1, v2, v3 = Literal(None), Literal(None), Literal(None)

            if not tokens.maybe(':'):
                v1 = expr()

            if not tokens.maybe(']'):
                if tokens.next(':') and not tokens.maybe(':', ']'):
                    v2 = expr()
                if tokens.next_if(':') and not tokens.maybe(']'):
                    v3 = expr()
                v1 = Slice(v1, v2, v3)

            tokens.next(']')
            e = ItemGet(e, v1)

        return e

    def _key_value():
        key = expr()
        tokens.next(':')
        value = expr()
        return (key, value)

    def primary():
        return tokens.expect({
            'INTEGER': lambda x: Literal(int(x.image)),
            'FLOAT': lambda x: Literal(float(x.image)),
            'STRING': lambda x: Literal(x.image[1:-1].decode('string-escape')),
            'IDENTIFIER': lambda x: VariableGet(x.image),
            '(': lambda x: block(')'),
            '[': lambda x: ListLiteral(_list_of(expr, ']')),
            '{': lambda x: DictLiteral(_list_of(_key_value, '}')),            
        }) 
        
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


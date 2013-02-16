# -*- coding:utf8 -*-
from ast import *
from scanner import *
from functools import partial
    
SCANNER = Scanner('+', '-', '*', '/', '**', '%', '(', ')', '[', ']', '{', '}',
                  '==', '!=', ',', '=', '@', ';', ':', '..', '|>', '=>', '.', 
                  '<', '<=', '>', '>=', '~', '<<', '>>', '&', '|', '^',
                  'return', 'in', 'not in', 'if', 'else', 'elif', 'and', 'or', 
                  'not', 'import', 'def', 'yield',
                  INTEGER = r'[0-9]+', 
                  FLOAT = r'[0-9]*\.[0-9]+', 
                  IDENTIFIER = r'[_a-zA-Z][_a-zA-Z0-9]*',
                  STRING = '|'.join([r'("([^\\"]|\\.)*")',r"('([^\\']|\\.)*')"]),
                  EOF = r'$')
        
class Parser(TokenStream):
    def __init__(self, source):
        super(Parser, self).__init__(SCANNER, source)

    def program(self):
        return self.block('EOF')

    def block(self, until):
        exprs = []
        while self.ignore(';') and not self.next_if(until):
            exprs.append(self.expr())
            self.expect_lf_or(';', until)
        return Block(exprs)
        
    def _binary(self, higher, clazz, *ops):
        e = higher()        
        while self.maybe(*ops, stop_on_lf=True):
            e = clazz(self.next(*ops).name, e, higher())
        return e

    def _raw(self, higher, ops):
        e = higher()
        while self.maybe(*ops):
            e = ops[self.next(*ops).name](e, higher())
        return e

    def _unary(self, higher, *ops):
        if self.maybe(*ops):
            return UnaryOp(self.next(*ops).name, self._unary(higher, *ops))
        return higher()

    def _list_of(self, what, until):
        args = []
        if not self.maybe(until):
            args.append(what())
            while self.next_if(',') and not self.maybe(until):
                args.append(what())
        self.next(until)
        return args 

    def expr(self):
        return self.if_expression()

    def if_expression(self):
        if self.next_if('if'):
            return self.if_test_and_bodies()
        return self.yield_expression()
    
    def if_test_and_bodies(self):
        test = self.expr()
        self.next(':')
        then_body = self.expr()
        
        if self.next_if('else') and self.next(':'):
            else_body = self.expr()
        elif self.next_if('elif'):
            else_body = self.if_test_and_bodies()
        else:
            else_body = Block()
        
        return If(test, then_body, else_body)

    def yield_expression(self):
        if self.next_if('yield'):
            return Yield(self.expr())
        return self.return_expression()
            
    def return_expression(self):
        if self.next_if('return'):
            return Return(self.expr())
        return self.assignment()

    def assignment(self):
        to = self.import_expression()
        if hasattr(to, 'to_assignment') and self.next_if('='):
            value = self.expr()
            return to.to_assignment(value)
        return to

    def import_expression(self):
        if self.next_if('import'):
            name = self.next('IDENTIFIER').image
            items = []        
            if self.next_if('(', stop_on_lf=True):
                items = self._list_of(lambda: self.next('IDENTIFIER', '*').image, ')')
            return Import(name, items)
        return self.function()

    def function(self):
        if self.next_if('@'):
            args = self._list_of(lambda: self.next('IDENTIFIER').image, ':')
            body = self.expr()
            return Function(None, args, body)

        if self.next_if('def'):
            name = self.next('IDENTIFIER').image
            self.next('(')
            args = self._list_of(lambda: self.next('IDENTIFIER').image, ')')
            self.next(':')
            body = self.expr()
            return Function(name, args, body)
            
        return self.operators()

    OPS = [
        (_raw, {'|>':PipeForward}), 
        (_raw, {'=>':Composition}), 
        (_binary, BooleanOp, 'or'),
        (_binary, BooleanOp, 'and'),
        (_unary, 'not'),
        (_binary, CompareOp, 'in', 'not in'),
        (_binary, CompareOp, '==', '!=', '<', '>', '<=', '>='),
        (_binary, BinaryOp, '|'),
        (_binary, BinaryOp, '^'),
        (_binary, BinaryOp, '&'),
        (_binary, BinaryOp, '<<', '>>'),
        (_binary, BinaryOp, '+', '-'),
        (_binary, BinaryOp, '*', '/', '%'),
        (_binary, BinaryOp, '**'),
        (_unary, '-', '+', '~'),
    ]

    def operators(self):
        current = self.range_literal
        for op in reversed(Parser.OPS):
            current = partial(op[0], self, current, *op[1:])
        return current()

    def range_literal(self):
        begin = self.call()
        if self.next_if('..'):
            end = self.call()
            step = self.call() if self.next_if(':') else None
            return RangeLiteral(begin, end, step)
        return begin

    def call(self):
        e = self.get_attribute()
        while self.maybe('(', '{', stop_on_lf=True):
            e = self.expect({
                    '(': lambda x: Call(e, self._list_of(self.expr, ')')),
                    '{': lambda x: PartialCall(e, self._list_of(self.expr, '}'))}) 
        return e

    def get_attribute(self):
        e = self.get_subscript()
        while self.next_if('.'):
            member = self.next('IDENTIFIER')
            e = GetAttribute(e, member.image)
        return e
        
    def get_subscript(self):
        e = self.primary()

        while self.next_if('[', stop_on_lf=True):
            v1, v2, v3 = Literal(None), Literal(None), Literal(None)

            if not self.maybe(':'):
                v1 = self.expr()

            if not self.maybe(']'):
                if self.next(':') and not self.maybe(':', ']'):
                    v2 = self.expr()
                if self.next_if(':') and not self.maybe(']'):
                    v3 = self.expr()
                v1 = Slice(v1, v2, v3)

            self.next(']')
            e = GetSubscript(e, v1)

        return e

    def _key_value(self):
        key = self.expr()
        self.next(':')
        value = self.expr()
        return (key, value)

    def primary(self):
        return self.expect({
            'INTEGER': lambda x: Literal(int(x.image)),
            'FLOAT': lambda x: Literal(float(x.image)),
            'STRING': lambda x: Literal(x.image[1:-1].decode('string-escape')),
            'IDENTIFIER': lambda x: GetVariable(x.image),
            '(': lambda x: self.block(')'),
            '[': lambda x: ListLiteral(self._list_of(self.expr, ']')),
            '{': lambda x: DictLiteral(self._list_of(self._key_value, '}')),            
        }) 


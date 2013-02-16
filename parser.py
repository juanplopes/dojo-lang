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
        ctx = LexicalContext()
        body = self.block(ctx, 'EOF')
        return Program(body, ctx.varnames('exported'), ctx.varnames('closure'))

    def block(self, ctx, until):
        exprs = []
        while self.ignore(';') and not self.next_if(until):
            exprs.append(self.expr(ctx))
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

    def expr(self, ctx):
        return self.if_expression(ctx)

    def if_expression(self, ctx):
        if self.next_if('if'):
            return self.if_test_and_bodies(ctx)
        return self.yield_expression(ctx)
    
    def if_test_and_bodies(self, ctx):
        test = self.expr(ctx)
        self.next(':')
        then_body = self.expr(ctx)
        
        if self.next_if('else') and self.next(':'):
            else_body = self.expr(ctx)
        elif self.next_if('elif'):
            else_body = self.if_test_and_bodies(ctx)
        else:
            else_body = Block()
        
        return If(test, then_body, else_body)

    def yield_expression(self, ctx):
        if self.next_if('yield'):
            return Yield(self.expr(ctx))
        return self.return_expression(ctx)
            
    def return_expression(self, ctx):
        if self.next_if('return'):
            return Return(self.expr(ctx))
        return self.assignment(ctx)

    def assignment(self, ctx):
        to = self.import_expression(ctx)
        if hasattr(to, 'to_assignment') and self.next_if('='):
            value = self.expr(ctx)
            return to.to_assignment(value)
        return to

    def import_expression(self, ctx):
        if self.next_if('import'):
            name = self.next('IDENTIFIER').image
            items = []        
            if self.next_if('(', stop_on_lf=True):
                items = self._list_of(lambda: self.next('IDENTIFIER').image, ')')
            return Import(name, items)
        return self.function(ctx)

    def function(self, ctx):
        if self.next_if('@'):
            args = self._list_of(lambda: self.next('IDENTIFIER').image, ':')
            return self.function_body(ctx, None, args)
            
        if self.next_if('def'):
            name = self.next('IDENTIFIER').image
            var = ctx.ensure(name, 'local')
            
            self.next('(')
            args = self._list_of(lambda: self.next('IDENTIFIER').image, ')')
            self.next(':')
            return SetVariable(var, self.function_body(ctx, name, args))
            
            
        return self.operators(ctx)

    def function_body(self, ctx, name, args):
        body_ctx = ctx.push(args)
        body = self.expr(body_ctx)
        return Function(name, args, body, 
                        body_ctx.varnames('exported'), 
                        body_ctx.varnames('closure'))

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

    def operators(self, ctx):
        current = partial(self.range_literal, ctx)
        for op in reversed(Parser.OPS):
            current = partial(op[0], self, current, *op[1:])
        return current()

    def range_literal(self, ctx):
        begin = self.call(ctx)
        if self.next_if('..'):
            end = self.call(ctx)
            step = self.call(ctx) if self.next_if(':') else None
            return RangeLiteral(begin, end, step)
        return begin

    def call(self, ctx):
        e = self.get_attribute(ctx)
        while self.maybe('(', '{', stop_on_lf=True):
            e = self.expect({
                    '(': lambda x: Call(e, self._list_of(lambda: self.expr(ctx), ')')),
                    '{': lambda x: PartialCall(e, self._list_of(lambda: self.expr(ctx), '}'))}) 
        return e

    def get_attribute(self, ctx):
        e = self.get_subscript(ctx)
        while self.next_if('.'):
            member = self.next('IDENTIFIER')
            e = GetAttribute(e, member.image)
        return e
        
    def get_subscript(self, ctx):
        e = self.primary(ctx)

        while self.next_if('[', stop_on_lf=True):
            v1, v2, v3 = Literal(None), Literal(None), Literal(None)

            if not self.maybe(':'):
                v1 = self.expr(ctx)

            if not self.maybe(']'):
                if self.next(':') and not self.maybe(':', ']'):
                    v2 = self.expr(ctx)
                if self.next_if(':') and not self.maybe(']'):
                    v3 = self.expr(ctx)
                v1 = Slice(v1, v2, v3)

            self.next(']')
            e = GetSubscript(e, v1)

        return e

    def _key_value(self, ctx):
        key = self.expr(ctx)
        self.next(':')
        value = self.expr(ctx)
        return (key, value)

    def primary(self, ctx):
        return self.expect({
            'INTEGER': lambda x: Literal(int(x.image)),
            'FLOAT': lambda x: Literal(float(x.image)),
            'STRING': lambda x: Literal(x.image[1:-1].decode('string-escape')),
            'IDENTIFIER': lambda x: GetVariable(ctx.request(x.image)),
            '(': lambda x: self.block(ctx, ')'),
            '[': lambda x: ListLiteral(self._list_of(lambda: self.expr(ctx), ']')),
            '{': lambda x: DictLiteral(self._list_of(lambda: self._key_value(ctx), '}')),            
        }) 


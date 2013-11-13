# -*- coding:utf8 -*-
from dojo.ast import *
from dojo.scanner import *
from functools import partial
    
SCANNER = Scanner('+', '-', '*', '/', '//', '**', '%', '(', ')', '[', ']', '{', '}',
                  '==', '!=', ',', '=', '@', ';', ':', '::', '..', '|>', '=>', '.',
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
        return Program(body.line, body, ctx.varnames('exported'), ctx.varnames('closure'))

    def block(self, ctx, until):
        exprs = []
        line = self.line
        while self.ignore(';') and not self.next_if(until):
            exprs.append(self.expr(ctx))
            self.expect_lf_or(';', until)
        return Block(line, exprs)
        
    def _binary(self, higher, clazz, *ops):
        e = higher()
        for op in iter(partial(self.next_if, *ops, stop_on_lf=True), None):
            e = clazz(op.line, op.name, e, higher())
        return e

    def _raw(self, higher, ops):
        e = higher()
        while self.maybe(*ops):
            e = ops[self.next(*ops).name](e.line, e, higher())
        return e

    def _unary(self, higher, *ops):
        op = self.next_if(*ops)
        if op:
            return UnaryOp(op.line, op.name, self._unary(higher, *ops))
        return higher()

    def _list_of(self, what, until = None, *rest):
        args = []
        if not self.maybe(until, *rest):
            args.append(what())
            while self.next_if(',') and not self.maybe(until, *rest):
                args.append(what())
        self.next_if(until)
        return args 

    def expr(self, ctx):
        return self.if_expression(ctx)

    def if_expression(self, ctx):
        if self.next_if('if'):
            return self.if_test_and_bodies(ctx, If)
        return self.yield_expression(ctx)
    
    def if_test_and_bodies(self, ctx, node):
        test = self.expr(ctx)
        self.next(':')
        then_body = self.expr(ctx)
        
        if self.next_if('else') and self.next(':'):
            else_body = self.expr(ctx)
        elif self.next_if('elif'):
            else_body = self.if_test_and_bodies(ctx, If)
        else:
            else_body = Block(test.line)
        
        return node(test.line, test, then_body, else_body)

    def yield_expression(self, ctx):
        op = self.next_if('yield')
        if op:
            return Yield(op.line, self.expr(ctx))
        return self.return_expression(ctx)
            
    def return_expression(self, ctx):
        op = self.next_if('return')
        if op:
            return Return(op.line, self.expr(ctx))
        return self.import_expression(ctx)

    def import_expression_item(self, ctx):
        module = self.next('IDENTIFIER').image
        if self.next_if('(', stop_on_lf=True):
            names = self._list_of(lambda: self.next('IDENTIFIER').image, ')')
            return [module, names]
        return [module, None]

    def import_expression(self, ctx):
        op = self.next_if('import')
        if op:
            items = self._list_of(lambda: self.import_expression_item(ctx))        
            return Import(op.line, items)
            
        return self.pipe_forward(ctx)

    def pipe_forward(self, ctx):
        return self._raw(partial(self.function, ctx), {'|>': PipeForward})

    def function(self, ctx):
        op = self.next_if('/')
        if op:
            args = self._list_of(lambda: self.next('IDENTIFIER').image, '=>')
            return self.function_body(op.line, ctx, None, args, self.function)

        op = self.next_if('def')
        if op:
            name = self.next('IDENTIFIER').image
            var = ctx.ensure(name, 'local')
            
            self.next('(')
            args = self._list_of(lambda: self.next('IDENTIFIER').image, ')')
            self.next(':')
            return SetVariable(op.line, var, self.function_body(op.line, ctx, name, args, self.expr))
            
            
        return self.assignment(ctx)

    def function_body(self, line, ctx, name, args, body_type):
        body_ctx = ctx.push(args)
        body = body_type(body_ctx)
        return Function(line, name, args, body,
                        body_ctx.varnames('exported'), 
                        body_ctx.varnames('closure'))

    def assignment(self, ctx):
        to = self.operators(ctx)
        if hasattr(to, 'to_assignment') and self.next_if('='):
            value = self.expr(ctx)
            return to.to_assignment(value)
        return to

    OPS = [
        (_raw, {'::':Composition}),
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
        (_binary, BinaryOp, '*', '/', '//', '%'),
        (_binary, BinaryOp, '**'),
        (_unary, '-', '+', '~'),
    ]

    def operators(self, ctx):
        current = partial(self.call, ctx)
        for op in reversed(Parser.OPS):
            current = partial(op[0], self, current, *op[1:])
        return current()


    def _named_args(self, ctx):
        self.next('@')
        name = self.next('IDENTIFIER').image
        self.next('=')
        expr = self.expr(ctx)
        return (name, expr)

    def _make_call(self, ctx, clazz, op, target, until):
        args = self._list_of(lambda: self.expr(ctx), until, '@')
        if self.maybe('@'):
            kwargs = self._list_of(lambda: self._named_args(ctx), until)
        else:
            kwargs = ()
        return clazz(op.line, target, args, kwargs)

    def call(self, ctx):
        e = self.get_attribute(ctx)
        for op in iter(partial(self.maybe, '(', '{', stop_on_lf=True), None):
            e = self.expect({
                    '(': lambda x: self._make_call(ctx, Call, op, e, ')'),
                    '{': lambda x: self._make_call(ctx, PartialCall, op, e, '}')})
        return e

    def get_attribute(self, ctx):
        e = self.get_subscript(ctx)
        for op in iter(partial(self.next_if, '.'), None):
            member = self.next('IDENTIFIER')
            e = GetAttribute(op.line, e, member.image)
        return e
        
    def get_subscript(self, ctx):
        e = self.primary(ctx)

        for op in iter(partial(self.next_if, '[', stop_on_lf=True), None):
            v1 = self.expr(ctx) if not self.maybe('..') else Literal(op.line, None)

            if self.next_if('..'):
                v2 = self.expr(ctx) if not self.maybe(']') else Literal(op.line, None)
                v1 = Slice(v1.line, v1, v2)

            self.next(']')
            e = GetSubscript(op.line, e, v1)

        return e

    def _key_value(self, ctx):
        key = self.expr(ctx)
        self.next(':')
        value = self.expr(ctx)
        return (key, value)

    def primary(self, ctx):
        return self.expect({
            'INTEGER': lambda x: Literal(x.line, int(x.image)),
            'FLOAT': lambda x: Literal(x.line, float(x.image)),
            'STRING': lambda x: Literal(x.line, x.image[1:-1].encode('utf-8').decode('unicode-escape')),
            'IDENTIFIER': lambda x: GetVariable(x.line, ctx.request(x.image)) if not self.next_if('=>') else self.function_body(x.line, ctx, None, [x.image], self.assignment),
            '(': lambda x: self.block(ctx, ')'),
            '[': lambda x: ListLiteral(x.line, self._list_of(lambda: self.expr(ctx), ']')),
            '{': lambda x: DictLiteral(x.line, self._list_of(lambda: self._key_value(ctx), '}')),
        }) 


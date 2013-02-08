# -*- coding:utf8 -*-
import re
from ast import *
from scanner import Scanner, Token
        
def parse(expression):
    tokens = Scanner(expression, 
                     '+', '-', '*', '/', '**', '(', ')', ',', '=', '@', ';', ':',
                     'return',
                     INTEGER = '[0-9]+', 
                     FLOAT = '[0-9]*\.[0-9]+', 
                     IDENTIFIER = '[a-zA-Z][a-zA-Z0-9]*', 
                     EOF = '$')
 
    #block ::= expr (('\n'|','|';')+ expr)*
    def block(expected):
        exprs = [expr()]
        while tokens.ignore(',', ';') and not tokens.peek(expected):
            exprs.append(expr())
        return Program(exprs)

    #expr ::= return_expression
    def expr():
        return return_expression()

    def _binary(higher, ops):
        e = higher()        
        while tokens.peek(*ops, stop_on_lf=True):
            e = BinaryExpression(ops[tokens.next(*ops).name], e, higher())
        return e

    def _unary(current, higher, ops):
        if tokens.peek(*ops):
            return UnaryExpression(ops[tokens.next(*ops).name], current())
        return higher()
    
    def _list_of(what, until):
        args = []
        if not tokens.peek(until):
            args.append(what())
            while tokens.maybe(','):
                args.append(what())
        tokens.next(until)
        return args        

    #return_expression ::= ('return' expr) | function
    def return_expression():
        if tokens.maybe('return'):
            return Return(function())
        return function()
        
    #function ::= ('@' _list_of('IDENTIFIER') ':' expr) | adds
    def function():
        if tokens.maybe('@'):
            args = _list_of(lambda: tokens.next('IDENTIFIER').image, ':')
            body = expr()
            return Function(args, body)
        return adds()
     
    #adds ::= muls (('+'|'-') muls)*
    def adds(): 
        return _binary(muls, {'+': lambda x,y:x+y, '-': lambda x,y:x-y})

    #muls ::= pows (('*'|'/') pows)*
    def muls(): 
        return _binary(pows, {'*': lambda x,y:x*y, '/': lambda x,y:x/y})

    #pows ::= negs ('**' negs)*
    def pows(): 
        return _binary(negs, {'**': lambda x,y:x**y})
 
    #negs ::= ('-' negs) | method_call
    def negs():
        return _unary(negs, call, {'-': lambda x:-x })
 
    #method_call ::= primary ('(' _list_of(expr) ')')?
    def call():
        e = primary()
        if tokens.maybe('(', stop_on_lf=True):
            args = _list_of(expr, ')')
            return Call(e, args)
        
        return e

    #primary ::= INTEGER | FLOAT | IDENTIFIER | ('(' block ')')
    def primary():
        return tokens.expect({
            'INTEGER': lambda x: Literal(int(x.image)),
            'FLOAT': lambda x: Literal(float(x.image)),
            'IDENTIFIER': lambda x: VariableSet(x.image, expr()) if tokens.maybe('=') else VariableGet(x.image),
            '(': lambda x: tokens.following(block(')'), ')')}) 
        
 
    return tokens.following(block('EOF'), 'EOF')
    
if __name__ == '__main__':
    import sys, __builtin__
    
    def read(prompt): 
        return raw_input(prompt)

    def write(message):
        print message               
    
    with open(sys.argv[1]) as f:
        data = f.read()
        scope = Scope(__builtin__.__dict__)
        scope.force('read', read)
        scope.force('write', write)
        parse(data)(scope)  


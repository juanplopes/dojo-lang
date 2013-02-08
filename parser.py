# -*- coding:utf8 -*-
import re, sys, json
from ast import *
from scanner import Scanner, Token
        
def parse(expression):
    tokens = Scanner(expression, 
                     '+', '-', '*', '/', '**', '(', ')', ',', '=', '@', ';', ':',
                     NUMBER = '[0-9]+', 
                     IDENTIFIER = '[a-zA-Z][a-zA-Z0-9]*', 
                     NEWLINE = '\\n',
                     EOF = '$')
 
    #block ::= expr (('\n'|','|';')+ expr)*
    def block():
        exprs = [expr()]
        while tokens.at_least_one('NEWLINE', ',', ';') and not tokens.peek('EOF'):
            exprs.append(expr())
        return Program(exprs)

    #expr ::= adds
    def expr():
        return function()

    def _binary(higher, ops):
        e = higher()        
        while tokens.peek(*ops):
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
        if tokens.maybe('('):
            args = _list_of(expr, ')')
            return Call(e, args)
        
        return e

    #primary ::= NUMBER | IDENTIFIER | ('(' expr ')')
    def primary():
        return tokens.expect({
            'NUMBER': lambda x: Literal(int(x.image)),
            'IDENTIFIER': lambda x: VariableSet(x.image, expr()) if tokens.maybe('=') else VariableGet(x.image),
            '(': lambda x: tokens.following(block(), ')')}) 
        
 
    return tokens.following(block(), 'EOF')
    
if __name__ == '__main__':
    print parse(sys.argv[1])(Scope())

# -*- coding:utf8 -*-
import re, sys, json
from ast import *
from scanner import Scanner, Token
        
def parse(expr):
    tokens = Scanner(expr, 
                    NUMBER = '[0-9]+', 
                    IDENTIFIER = '[a-zA-Z][a-zA-Z0-9]*', 
                    ADD = '\+', 
                    SUB = '-', 
                    POW = '\^',
                    MUL = '\*', 
                    DIV = '/',
                    LPAREN = '\(',
                    RPAREN = '\)',
                    COMMA = ',',
                    ATTR = '=',
                    EOF = '$')
    
    def _binary(higher, **ops):
        e = higher()        
        while tokens.peek(*ops):
            e = BinaryExpression(ops[tokens.next(*ops).name], e, higher())
        return e
  
    def _unary(current, higher, **ops):
        if tokens.peek(*ops):
            return UnaryExpression(ops[tokens.next(*ops).name], current())
        return higher()
 
    def program():
        exprs = [adds()]
        while tokens.maybe('COMMA'):
            exprs.append(adds())
        return Program(exprs)
     
    def adds(): 
        return _binary(muls, ADD=lambda x,y:x+y, SUB=lambda x,y:x-y)

    def muls(): 
        return _binary(pows, MUL=lambda x,y:x*y, DIV=lambda x,y:x/y)

    def pows(): 
        return _binary(negs, POW=lambda x,y:x**y)
 
    def negs():
        return _unary(negs, methods, SUB=lambda x:-x)
 
    def methods():
        e = primary()
        if tokens.maybe('LPAREN'):
            args = []
            if not tokens.peek('RPAREN'):
                args.append(primary())
                while tokens.maybe('COMMA'):
                    args.append(primary())
            return tokens.following(MethodCall(e, args), 'RPAREN')
        
        return e
  
    def primary():
        return tokens.expect(
            NUMBER = lambda x: Literal(int(x.image)),
            IDENTIFIER = lambda x: VariableSet(x.image, adds()) if tokens.maybe('ATTR') else VariableGet(x.image),
            LPAREN = lambda x: tokens.following(adds(), 'RPAREN')) 
        
 
    return tokens.following(program(), 'EOF')
    
if __name__ == '__main__':
    print parse(sys.argv[1])(Scope())

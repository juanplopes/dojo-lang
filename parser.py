# -*- coding:utf8 -*-
import re, sys, json
from ast import *
 
TOKENS = {
    'NUMBER': '[0-9]+', 
    'IDENTIFIER': '[a-zA-Z][a-zA-Z0-9]*', 
    'ADD': '\+', 
    'SUB': '-', 
    'POW': '\^',
    'MUL': '\*', 
    'DIV': '/',
    'LPAREN': '\(',
    'RPAREN': '\)',
    'COMMA': ',',
    'ATTR': '=',
    'EOF': '$'
}
 
class Token:
    EOF = lambda p: Token('EOF', '', p)
 
    def __init__(self, name, image, begin, end):
        self.name = name
        self.image = image
        self.begin = begin
        self.end = end
 
class Scanner:
    def __init__(self, expr):
        self.expr = expr
        self.pos = 0
 
    def match(self, name):
        match = re.match('^\s*'+TOKENS[name], self.expr[self.pos:])
        return Token(name, match.group().strip(), self.pos, self.pos+len(match.group())) if match else None
 
    def peek(self, *allowed):
        for match in map(self.match, allowed):
            if match: return match
 
    def next(self, *allowed):
        token = self.peek(*TOKENS)
 
        if not token:
            raise Exception("Cannot understand expression at position {}: '{}'".format( 
                              self.pos, self.expr[self.pos:]))
 
        if token.name not in allowed:
            raise Exception("Unexpected {} at position {}, expected one of: {}".format( 
                              token.name, token.begin, ", ".join(allowed)))
 
        self.pos = token.end
        return token
      
    def maybe(self, *allowed):
        if self.peek(*allowed):
            return self.next(*allowed)
       
    def following(self, value, *allowed):
        self.next(*allowed)
        return value
        
    def expect(self, **actions):
        token = self.next(*actions.keys())
        return actions[token.name](token)
        
def parse(expr):
    tokens = Scanner(expr)
    
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
                while not tokens.peek('RPAREN'):
                    tokens.next('COMMA')
                    args.append(primary())
            return tokens.following(MethodCall(e, args), 'RPAREN')
        
        return e
  
    def primary():
        return tokens.expect(
            NUMBER = lambda x: Literal(int(x.image)),
            IDENTIFIER = lambda x: VariableSet(x.image, adds()) if tokens.maybe('ATTR') else VariableGet(x.image),
            LPAREN = lambda x: tokens.following(adds(), 'RPAREN')) 
        
 
    return Program([tokens.following(program(), 'EOF')])
    
if __name__ == '__main__':
    print parse(sys.argv[1])(Scope())

# -*- coding:utf8 -*-
import re, sys, json
from ast import *
from itertools import chain
 
class Token(object):
    EOF = lambda p: Token('EOF', '', p)
 
    def __init__(self, name, whites, image, begin, line, column):
        self.name = name
        self.image = image
        self.whites = whites
        self.begin = begin
        self.line = line
        self.column = column
        self.raw_len = len(whites) + len(image)
        self.lf = '\n' in whites

class InvalidSyntax(Exception):
    def __init__(self, line, column, expr):
        super(Exception, self).__init__(
            "Invalid syntax at line {} column {}: '{}'"
                .format(line, column, expr))
    
class UnexpectedToken(Exception):
    def __init__(self, token, allowed):
        super(Exception, self).__init__(        
            "Unexpected <{}> at line {} column {}, expected one of: <{}>"
                .format(token.name, token.line, token.column, ", ".join(allowed)))

class Scanner(object):
    def __init__(self, expr, *symbols, **named):
        self.tokens = list(chain(
             ((x, re.compile('^(\s*)({})'.format(re.escape(x)))) for x in symbols),
             ((k, re.compile('^(\s*)({})'.format(v))) for k, v in named.items())))

        self.expr = expr
        self.pos = 0
        self.line = 1
        self.column = 1
 
    def match(self, token):
        name, pattern = token
        match = pattern.match(self.expr[self.pos:])
        if match:
            w, s = match.groups()[:2]
            line = self.line+w.count('\n')
            column = len(w) - w.rfind('\n') - 1 + ('\n' not in w and self.column or 1)
            return Token(name, w, s, self.pos, line, column)
 
    def reducer(self, **opts):
        def y(a, b):
            if not b: return a
            if opts.get('stop_on_lf') and b.lf: return a
            return max(a, b, key=lambda x:x and len(x.image))
        return y

    def peek(self, **opts):
        return reduce(self.reducer(**opts), map(self.match, self.tokens))
 
    def maybe(self, *allowed, **opts):
        token = self.peek(**opts)
        if token and token.name in allowed:
            return token
 
    def next(self, *allowed, **opts):
        token = self.peek(**opts)

        if not token:
            raise InvalidSyntax(self.line, self.column, self.expr[self.pos:self.pos+25])

        if token.name not in allowed:
            raise UnexpectedToken(token, allowed)
 
        self.pos += token.raw_len
        self.line = token.line
        self.column = token.column + len(token.image)
        return token
      
    def next_if(self, *allowed, **opts):
        if self.maybe(*allowed, **opts):
            return self.next(*allowed, **opts)
    
    def ignore(self, *allowed, **opts):
        self.at_least_one(*allowed, **opts)
        return True
       
    def at_least_one(self, *allowed, **opts):
        token = None
        while self.maybe(*allowed, **opts):
            token = self.next(*allowed, **opts)
        return token
    
    def following(self, value, *allowed, **opts):
        self.next(*allowed, **opts)
        return value
        
    def expect(self, actions, **opts):
        token = self.next(*actions.keys(), **opts)
        return actions[token.name](token)

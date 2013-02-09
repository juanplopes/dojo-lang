# -*- coding:utf8 -*-
import re, sys, json
from ast import *
 
class Token(object):
    EOF = lambda p: Token('EOF', '', p)
 
    def __init__(self, name, image, begin, end, lf):
        self.name = name
        self.image = image
        self.begin = begin
        self.end = end
        self.lf = lf
 
class Scanner(object):
    def __init__(self, expr, *symbols, **named):
        self.tokens = {}
        for name, pattern in named.items():
            self.tokens[name] = re.compile('^\s*' + pattern)
        for symbol in symbols:
            self.tokens[symbol] = re.compile('^\s*' + re.escape(symbol))

        self.expr = expr
        self.pos = 0
 
    def match(self, name):
        match = re.match(self.tokens[name], self.expr[self.pos:])
        if match:
            s = match.group()
            return Token(name, s.strip(), self.pos, self.pos+len(s), '\n' in s)
 
    def check(self, matched, **opts):
        if not matched: return None
        if opts.get('stop_on_lf') and matched.lf: return None
        return matched
 
    def peek_in_all(self, **opts):
        token = None
        for matched in map(self.match, self.tokens.keys()):
            if self.check(matched, **opts) and (not token or token.end < matched.end):
                token = matched

        return token
 
    def peek(self, *allowed, **opts):
        token = self.peek_in_all(**opts)
        if token and token.name in allowed:
            return token
 
    def next(self, *allowed, **opts):
        token = self.peek_in_all(**opts)

        if not token:
            raise Exception("Cannot understand expression at position {}: '{}' {}".format( 
                              self.pos, self.expr[self.pos:]))

        if token.name not in allowed:
            raise Exception("Unexpected {} at position {}, expected one of: {}".format( 
                              token.name, token.begin, ", ".join(allowed)))
 
        self.pos = token.end
        return token
      
    def maybe(self, *allowed, **opts):
        if self.peek(*allowed, **opts):
            return self.next(*allowed, **opts)
    
    def ignore(self, *allowed, **opts):
        self.at_least_one(*allowed, **opts)
        return True
       
    def at_least_one(self, *allowed, **opts):
        token = None
        while self.peek(*allowed, **opts):
            token = self.next(*allowed, **opts)
        return token
    
    def following(self, value, *allowed, **opts):
        self.next(*allowed, **opts)
        return value
        
    def expect(self, actions, **opts):
        token = self.next(*actions.keys(), **opts)
        return actions[token.name](token)

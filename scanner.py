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
        self.special = {}
        for symbol in symbols:
            self.special[symbol] = re.compile('^\s*' + re.escape(symbol))
        self.tokens = {}
        for name, pattern in named.items():
            self.tokens[name] = re.compile('^\s*' + pattern)

        self.expr = expr
        self.pos = 0
 
    def match(self, name):
        match = re.match(self.special.get(name) or self.tokens[name], self.expr[self.pos:])
        if match:
            s = match.group()
            return Token(name, s.strip(), self.pos, self.pos+len(s), '\n' in s)
 
    def check(self, matched, **opts):
        if not matched: return None
        if opts.get('stop_on_lf') and matched.lf: return None
        return matched
 
    def peek(self, **opts):
        token = None
        for matched in map(self.match, self.special.keys() + self.tokens.keys()):
            if self.check(matched, **opts) and (not token or token.end < matched.end):
                token = matched

        return token
 
    def maybe(self, *allowed, **opts):
        token = self.peek(**opts)
        if token and token.name in allowed:
            return token
 
    def next(self, *allowed, **opts):
        token = self.peek(**opts)

        if not token:
            raise Exception("Cannot understand expression at position {}: '{}'".format( 
                              self.pos, self.expr[self.pos:]))

        if token.name not in allowed:
            raise Exception("Unexpected <{}> at position {}, expected one of: {}".format( 
                              token.name, token.begin, ", ".join(allowed)))
 
        self.pos = token.end
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

# -*- coding:utf8 -*-
import re, sys, json
from ast import *
 
class Token:
    EOF = lambda p: Token('EOF', '', p)
 
    def __init__(self, name, image, begin, end):
        self.name = name
        self.image = image
        self.begin = begin
        self.end = end
 
class Scanner:
    def __init__(self, tokens, expr):
        self.tokens = tokens
        self.expr = expr
        self.pos = 0
 
    def match(self, name):
        match = re.match('^\s*'+self.tokens[name], self.expr[self.pos:])
        if match:
            return Token(name, match.group().strip(), self.pos, self.pos+len(match.group()))
 
    def peek(self, *allowed):
        token = None
        for matched in map(self.match, allowed):
            if matched and (not token or token.end < matched.end):
                token = matched
        return token
 
    def next(self, *allowed):
        token = self.peek(*self.tokens)
 
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

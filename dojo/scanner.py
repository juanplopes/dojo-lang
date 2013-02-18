# -*- coding:utf8 -*-
import re, sys, json
from itertools import chain

class InvalidSyntax(Exception):
    def __init__(self, line, column, source):
        super(Exception, self).__init__(
            "Invalid syntax at line {} column {}: '{}'"
                .format(line, column, source))
    
class UnexpectedToken(Exception):
    def __init__(self, token, allowed):
        super(Exception, self).__init__(        
            "Unexpected '{}' at line {} column {}, expected one of: {}"
                .format(token.name, token.line, token.column, ", ".join(
                    map(lambda x:"'{}'".format(x), allowed))))
 
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

class Scanner(object):
    def __init__(self, *symbols, **named):
        self.tokens = list(chain(
             ((x, re.compile('^(\s*)({})'.format(re.escape(x).replace('\\ ', '\s+')))) for x in symbols),
             ((k, re.compile('^(\s*)({})'.format(v))) for k, v in named.items())))
        
    def best_of(self, a, b, **opts):
        if not b: return a
        if opts.get('stop_on_lf') and b.lf: return a
        return max(a, b, key=lambda x:x and len(x.image))

    def scan(self, source, pos, line, column, **opts):
        best = None

        for token in self.tokens:
            name, pattern = token
            match = pattern.match(source[pos:])
            if match:
                w, s = match.groups()[:2]
                t_line = line+w.count('\n')
                t_column = (len(w) - w.rfind('\n') - 1) + ('\n' not in w and column or 1)
                best = self.best_of(best, Token(name, w, s, pos, t_line, t_column), **opts)
        
        return best

class TokenStream(object):
    def __init__(self, scanner, source):
        self.scanner = scanner
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1

    def peek(self, **opts):
        return self.scanner.scan(self.source, self.pos, self.line, self.column, **opts)
 
    def maybe(self, *allowed, **opts):
        token = self.peek(**opts)
        if token and token.name in allowed:
            return token
 
    def next(self, *allowed, **opts):
        token = self.peek(**opts)

        if not token:
            raise InvalidSyntax(self.line, self.column, self.source[self.pos:self.pos+25])

        if token.name not in allowed:
            raise UnexpectedToken(token, allowed)
 
        self.pos += token.raw_len
        self.line = token.line
        self.column = token.column + len(token.image)
        return token
      
    def next_if(self, *allowed, **opts):
        if self.maybe(*allowed, **opts):
            return self.next(*allowed, **opts)
    
    def expect_lf_or(self, *allowed, **opts):
        token = self.peek(**opts)
        if not token.lf and token.name not in allowed:
            raise UnexpectedToken(token, ('NEWLINE',) + allowed)
    
    def ignore(self, *allowed, **opts):
        self.at_least_one(*allowed, **opts)
        return True
       
    def at_least_one(self, *allowed, **opts):
        token = None
        while self.maybe(*allowed, **opts):
            token = self.next(*allowed, **opts)
        return token
        
    def expect(self, actions, **opts):
        token = self.next(*actions.keys(), **opts)
        try:
            return actions[token.name](token)
        except KeyError:
            if None not in actions:
                raise
            return actions[None](token)
            

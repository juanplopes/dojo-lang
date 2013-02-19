# -*- coding:utf8 -*-
from __future__ import print_function
from dojo.parser import Parser
from dojo.codegen import dojo_emit

def dojo_compile(source, filename='<string>'):
    ast = Parser(source).program()

    #Here should come the compiler optimizations. Should.

    code = dojo_emit(ast, filename)
    return DojoCallable(code)

class DojoCallable(object):
    def __init__(self, code):
        self.code = code
        
    def __call__(self, globals = None):
        return eval(self.code, globals, {})
    
if __name__ == '__main__':
    import sys
    
    with open(sys.argv[1]) as f:
        compiled = dojo_compile(f.read(), filename=sys.argv[1])
        #dis.dis(compiled.code)
        compiled()
        


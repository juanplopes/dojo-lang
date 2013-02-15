# -*- coding:utf8 -*-
from __future__ import print_function
from parser import Parser
from codegen import CodeGenerator

def dojo_compile(source, filename='<string>'):
    ast = Parser(source).program()

    #Here should come the compiler optimizations. Should.

    code = CodeGenerator(filename=filename)
    code.emit(ast)        
    return DojoCallable(code.assemble())

class DojoCallable(object):
    def __init__(self, code):
        self.code = code
        
    def __call__(self, globals = None, locals = None):
        return eval(self.code, globals, locals)
    
if __name__ == '__main__':
    import sys
    
    def read(prompt): 
        return raw_input(prompt)

    def write(*messages):
        print(*messages)
    
    with open(sys.argv[1]) as f:
        dojo_compile(f.read(), filename=sys.argv[1])()


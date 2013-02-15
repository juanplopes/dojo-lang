# -*- coding:utf8 -*-
from __future__ import print_function
from parser import Parser
from codegen import CodeGenerator

class DojoCompiled(object):
    def __init__(self, code):
        self.code = code
        
    def __call__(self, globals = None, locals = None):
        return eval(self.code, globals, locals)

def dojo_compile(source):
    code = CodeGenerator()
    code.emit(Parser(source).program())        
    return DojoCompiled(code.assemble())
    
if __name__ == '__main__':
    import sys, __builtin__
    
    def read(prompt): 
        return raw_input(prompt)

    def write(*messages):
        print(*messages)
    
    with open(sys.argv[1]) as f:
        data = f.read()
        dojo_compile(data)()


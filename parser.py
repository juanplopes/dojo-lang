# -*- coding:utf8 -*-
import re
from ast import *
from scanner import Scanner, Token
        
def parse(expression):
    tokens = Scanner(expression, 
                     '+', '-', '*', '/', '**', '%', '(', ')', '[', ']',
                     'return', '==', '!=', ',', '=', '@', ';', ':', '..',
                     '<', '<=', '>', '>=', '~', 'and', 'or', 'not', 'import',
                     '<<', '>>', '&', '|', '^', 'in', 'not in',
                     INTEGER = '[0-9]+', 
                     FLOAT = '[0-9]*\.[0-9]+', 
                     IDENTIFIER = '[a-zA-Z][a-zA-Z0-9]*',
                     EOF = '$')
 
    #block ::= expr ((','|';')* expr)*
    def block(until):
        exprs = []
        while tokens.ignore(',', ';') and not tokens.maybe(until):
            exprs.append(expr())
        return Block(exprs)

    #expr ::= return_expression
    def expr():
        return return_expression()

    #return_expression ::= ('return' expr) | import_expression
    def return_expression():
        if tokens.next_if('return'):
            return Return(expr())
        return import_expression()

    #import_expression ::= ('import' IDENTIFIER ('(' _list_of(IDENTIFIER)')')? | function
    def import_expression():
        if tokens.next_if('import'):
            name = tokens.next('IDENTIFIER').image
            items = []        
            if tokens.next_if('(', stop_on_lf=True):
                items = _list_of(lambda: tokens.next('IDENTIFIER').image, ')')
            return ModuleImport(name, items)
        return function()

       
    #function ::= ('@' _list_of(IDENTIFIER) ':' expr) | or_operator
    def function():
        if tokens.next_if('@'):
            args = _list_of(lambda: tokens.next('IDENTIFIER').image, ':')
            body = expr()
            return Function(args, body)
        return or_operator()

    #or_operator ::= and_operator ('or' and_operator)*
    def or_operator():
        return _short_binary(and_operator, {'or': OrExpression})

    #and_operator ::= not_operator ('and' not_operator)*
    def and_operator():
        return _short_binary(not_operator, {'and': AndExpression})

    #not_operator ::= ('not' not_operator) | equalities
    def not_operator():
        return _unary(not_operator, equalities, {
            'not': lambda x: not x})

    #equalities ::= shifts (('=='|'!='|'>'|'>='|'<'|'<=') shifts)*
    def equalities():
        return _binary(shifts, {
            '==': lambda x,y: x==y, 
            '!=': lambda x,y: x!=y,
             '>': lambda x,y: x>y, 
            '>=': lambda x,y: x>=y,
            '<': lambda x,y: x<y, 
            '<=': lambda x,y: x<=y,
            'in': lambda x,y: x in y,
            'not in': lambda x,y: x not in y})

    #shifts ::= adds (('<<'|'>>') adds)*
    def shifts(): 
        return _binary(adds, {'<<': lambda x,y:x<<y, '>>': lambda x,y:x>>y})

    #adds ::= muls (('+'|'-') muls)*
    def adds(): 
        return _binary(muls, {'+': lambda x,y:x+y, '-': lambda x,y:x-y})

    #muls ::= pows (('*'|'/'|'%') pows)*
    def muls(): 
        return _binary(pows, {
            '*': lambda x,y:x*y, 
            '/': lambda x,y:x/y, 
            '%': lambda x,y:x%y})

    #pows ::= negs ('**' negs)*
    def pows(): 
        return _binary(invs, {'**': lambda x,y:x**y})
 
    #invs ::= (('-'|'~') negs) | range_literal
    def invs():
        return _unary(invs, range_literal, {
            '-': lambda x:-x, 
            '~': lambda x: ~x })
 
    #range_literal ::= call ('..' call (':' call)?)?
    def range_literal():
        begin = call()
        if tokens.next_if('..'):
            end = call()
            step = call() if tokens.next_if(':') else None
            return RangeLiteral(begin, end, step)
        return begin
 
    #call ::= primary ('(' _list_of(expr) ')')?
    def call():
        e = primary()
        while tokens.next_if('(', stop_on_lf=True):
            args = _list_of(expr, ')')
            e = Call(e, args)
        
        return e

    #primary ::= INTEGER | FLOAT | IDENTIFIER | ('(' block ')') | '[' _list_of(expr) ']'
    def primary():
        return tokens.expect({
            'INTEGER': lambda x: Literal(int(x.image)),
            'FLOAT': lambda x: Literal(float(x.image)),
            'IDENTIFIER': lambda x: VariableSet(x.image, expr()) if tokens.next_if('=') else VariableGet(x.image),
            '(': lambda x: tokens.following(block(')'), ')'),
            '[': lambda x: ListLiteral(_list_of(expr, ']'))}) 
        
    def _binary(higher, ops):
        e = higher()        
        while tokens.maybe(*ops, stop_on_lf=True):
            e = BinaryExpression(ops[tokens.next(*ops).name], e, higher())
        return e

    def _short_binary(higher, ops):
        e = higher()
        while tokens.maybe(*ops, stop_on_lf=True):
            e = ops[tokens.next(*ops).name](e, higher())
        return e

    def _unary(current, higher, ops):
        if tokens.maybe(*ops):
            return UnaryExpression(ops[tokens.next(*ops).name], current())
        return higher()
    
    def _list_of(what, until):
        args = []
        if not tokens.maybe(until):
            args.append(what())
            while tokens.next_if(',') and not tokens.maybe(until):
                args.append(what())
        tokens.next(until)
        return args   
 
    return tokens.following(block('EOF'), 'EOF')
    
if __name__ == '__main__':
    import sys, __builtin__
    
    def read(prompt): 
        return raw_input(prompt)

    def write(message):
        print message               
    
    with open(sys.argv[1]) as f:
        data = f.read()
        scope = Scope(__builtin__.__dict__)
        scope.put('read', read)
        scope.put('write', write)
        parse(data)(scope)  


# -*- coding:utf8 -*-

import unittest
from parser import parse
from scanner import InvalidSyntax, UnexpectedToken

class ParserTestCase(unittest.TestCase):
    def test_constant(self):
        code = parse('42').to_code()
        self.assertEquals(42, eval(code))
        
    def test_simple_binaries(self):
        self.assertEquals(44, eval(parse('42+2').to_code()))
        self.assertEquals(40, eval(parse('42-2').to_code()))
        self.assertEquals(84, eval(parse('42*2').to_code()))
        self.assertEquals(21, eval(parse('42/2').to_code()))
        self.assertEquals(2, eval(parse('42%4').to_code()))
        self.assertEquals(1024, eval(parse('2**10').to_code()))

    def test_empty_program(self):
        program = parse('   ')
        self.assertEquals(None, eval(program.to_code()))

    def test_empty_expression(self):
        program = parse('()')
        self.assertEquals(None, eval(program.to_code()))

    def test_2_plus_2_with_spaces(self):
        program = parse('2   \t+ \t2')
        self.assertEquals(4, eval(program.to_code()))

    def test_expression_list_ending_in_comma(self):
        program = parse('1+2,3*4,')
        self.assertEquals(12, eval(program.to_code()))
        
    def test_unaries(self):
        self.assertEquals(-2, eval(parse('-2').to_code()))
        self.assertEquals(2, eval(parse('+2').to_code()))

    def test_unaries_ambiguity(self):
        program = parse('4\n-2')
        self.assertEquals(-2, eval(program.to_code()))

'''
    def test_unaries_ambiguity_not(self):
        program = parse('4,-2')
        self.assertEquals(-2, program())

    def test_precedence(self):
        self.assertEquals(14, parse('2+3*4')())

    def test_explicit_precedence(self):
        self.assertEquals(20, parse('(2+3)*4')())

    def test_set_member(self):
        self.assertEquals(4, parse('import _ast(If), i = If(), i.lineno = 2, i.lineno*2')())

    def test_set_variable_is_also_expression(self):
        self.assertEquals(20, parse('a=(2+3)*4,c=b=a')())

    def test_set_variable_on_global_scope_will_change_variables(self):
        scope = Scope()
        self.assertEquals(20, parse('a=(2+3)*4,c=b=a')(scope))
        self.assertEquals(20, scope.get('a'))
        self.assertEquals(20, scope.get('b'))
        self.assertEquals(20, scope.get('c'))

    def test_callable(self):
        scope = Scope({'add':lambda x, y:x+y})
        self.assertEquals(14, parse('2*add(5, 2)')(scope))
        
    def test_double_callable(self):
        scope = Scope({'add':lambda x, y:lambda:x+y})
        self.assertEquals(14, parse('2*add(5, 2)()')(scope))


    def test_callable_ambiguity(self):
        scope = Scope({'add':lambda x, y:x+y})
        self.assertEquals(2, parse('add\n(5, 2)')(scope))

    def test_callable_ambiguity_not(self):
        scope = Scope({'add':lambda x, y:x+y})
        self.assertEquals(2, parse('add,(5, 2)')(scope))

    def test_callable_with_non_primary(self):
        scope = Scope({'add':lambda x, y:x+y})
        self.assertEquals(20, parse('2*add(2+2, 3+3)')(scope))

    def test_call_functions_multiline(self):
        scope = Scope({'add':lambda a,b,c:a+b+c})
        self.assertEquals(18, parse("""add(
            2+2, 
            3+3
            ,4+4)""")(scope))

    def test_call_functions_multiline(self):
        scope = Scope({'add':lambda a,b,c:a+b+c})
        self.assertEquals(18, parse("""add(
            2+2, 
            3+3
            ,4+4)""")(scope))



    def test_multi_expr_program(self):
        self.assertEquals(9, parse('2+3, 4+5')())


    def test_set_variable_and_get_after(self):
        self.assertEquals(5, parse('a=2, a+3')())

    def test_power_one_variable_to_another(self):
        self.assertEquals(1024, parse('a=2, b=10, a**b')())

    def test_define_method_and_use_later(self):
        self.assertEquals(1024, parse('pow=@x,y:x**y, pow(2, 10)')())
        
    def test_define_multiline_functions(self):
        self.assertEquals(1024, parse("""
            test = @x,y:(
                a = y**.5
                x**a
            )
            test(2, 100)
        """)())

    def test_define_multiline_functions_with_parenthesis_below(self):
        self.assertEquals(1024, parse("""
            test = @x,y:
            (
                a = y**.5
                x**a
            )
            test(2, 100)
        """)())

    def test_define_multiline_with_return_functions(self):
        self.assertEquals(1024, parse("""
            test = @x,y:(
                a = y**.5
                return x**a
            )
            test(2, 100)
        """)())

    def test_equality_operator(self):
        self.assertEquals(True, parse('a=2, b=2, a==b')())
        self.assertEquals(False, parse('a=2, b=3, a==b')())


    def test_equality_operator(self):
        self.assertEquals(False, parse('a=2, b=2, a!=b')())
        self.assertEquals(True, parse('a=2, b=3, a!=b')())

    def test_in_not_int(self):
        self.assertEquals(True, parse('2 in [1,2,3]')())
        self.assertEquals(False, parse('4 in [1,2,3]')())

        self.assertEquals(False, parse('2 not in [1,2,3]')())
        self.assertEquals(True, parse('4 not in [1,2,3]')())

        self.assertEquals(False, parse('2 not  \t\n in [1,2,3]')())
        self.assertEquals(True, parse('4 not \t\n in [1,2,3]')())


    def test_comparation_operators(self):
        self.assertEquals(False, parse('a=2, b=3, a>b')())
        self.assertEquals(True, parse('a=2, b=3, a<b')())

        self.assertEquals(False, parse('a=2, b=3, a>=b')())
        self.assertEquals(True, parse('a=2, b=3, a<=b')())

        self.assertEquals(True, parse('a=2, b=2, a>=b')())
        self.assertEquals(True, parse('a=2, b=2, a<=b')())

    def test_and_operator(self):
        counter = [0]
        def function(): 
            counter[0]+=1
            return True

        scope = Scope({'print': function})
        
        self.assertEquals(False, parse('2+2==5 and print()')(scope))
        self.assertEquals(0, counter[0])
        
        self.assertEquals(True, parse('2+2==4 and print()')(scope))
        self.assertEquals(1, counter[0])
        
    def test_or_operator(self):
        counter = [0]
        def function(): 
            counter[0]+=1
            return False

        scope = Scope({'print': function})

        self.assertEquals(False, parse('2+2==5 or print()')(scope))
        self.assertEquals(1, counter[0])
        
        self.assertEquals(True, parse('2+2==4 or print()')(scope))
        self.assertEquals(1, counter[0])

        self.assertEquals(True, parse('2+2==4 or 2+3==5')(scope))
        self.assertEquals(1, counter[0])
        
    def test_not_operator(self):
        self.assertEquals(True, parse('not 2+2==5')())
        self.assertEquals(False, parse('not 2+2==4')())

    def test_binary_invert_operator(self):
        self.assertEquals(-43, parse('~42')())

    def test_binary_shift(self):
        self.assertEquals(42<<2, parse('42<<2')())
        self.assertEquals(42>>2, parse('42>>2')())

    def test_bitwise_ops(self):
        self.assertEquals(8, parse('42&12')())
        self.assertEquals(46, parse('42|12')())
        self.assertEquals(38, parse('42^12')())

    def test_pipe_forward(self):
        scope = Scope({'inc2':lambda a: a+2})
        self.assertEquals(44, parse('42 |> inc2')(scope))

    def test_composition(self):
        scope = Scope({'inc2':lambda a: a+2, 'str': str})
        self.assertEquals('44', parse('42 |> inc2 => str')(scope))

    def test_partial_apply(self):
        scope = Scope({'filter':filter})
        self.assertEquals(range(2, 20, 2), parse('1..20 |> filter{@x:x%2==0}')(scope))

    def test_list_literal(self):
        self.assertEquals([1,2,3,4], parse('[1,2,2+1,2*2]')())
        self.assertEquals([1,2,3,4], parse('[1,2,2+1,2*2,]')())

    def test_dict_literal(self):
        self.assertEquals({}, parse('{}')())
        self.assertEquals({'abc':123, 456:'qwe'}, parse('{"abc":123, 456:"qwe"}')())

    def test_string_literal(self):
        self.assertEquals('"abc', parse("'\"abc'")())
        self.assertEquals("'abc", parse('"\'abc"')())
        
    def test_range_literal(self):
        obj = parse('5..8')()
        it = iter(obj)
        self.assertEquals(5, next(it))
        self.assertEquals(6, next(it))
        self.assertEquals(7, next(it))
        self.assertRaises(StopIteration, next, it)
    
    def test_range_with_step(self):
        obj = parse('5..10:2')()
        it = iter(obj)
        self.assertEquals(5, next(it))
        self.assertEquals(7, next(it))
        self.assertEquals(9, next(it))
        self.assertRaises(StopIteration, next, it)    
        
    def test_import_module(self):
        scope = Scope()
        self.assertEquals(__import__('math'), parse('import math')(scope))
        self.assertEquals(__import__('math'), scope.get('math'))
        
    def test_import_module_items(self):
        scope = Scope()
        math = __import__('math')
        self.assertEquals(math, parse('import math(sqrt, cos, log)')(scope))
        self.assertEquals(math.sqrt, scope.get('sqrt'))
        self.assertEquals(math.cos, scope.get('cos'))
        self.assertEquals(math.log, scope.get('log'))

    def test_import_module_ambiguity(self):
        scope = Scope({'sqrt':1, 'cos':2, 'log':3})
        math = __import__('math')
        self.assertEquals(3, parse('import math\n(sqrt, cos, log)')(scope))

    def test_member_access(self):
        scope = Scope({'str': str, 'map': map})
        self.assertEquals('1,2,3,4', parse('[1,2,3,4] |> map{str} |> ",".join')(scope))

    def test_item_access(self):
        self.assertEquals(3, parse('a=[1,2,3,4], a[2]')())

    def test_item_slice(self):
        self.assertEquals([2,4], parse('a=[1,2,3,4], a[1:4:2]')())
        self.assertEquals([4,3,2], parse('a=[1,2,3,4], a[:0:-1]')())
        self.assertEquals([1,2,3,4], parse('a=[1,2,3,4], a[::]')())
        self.assertEquals([2,4], parse('a=[1,2,3,4], a[1::2]')())
        self.assertEquals([1,3], parse('a=[1,2,3,4], a[::2]')())
        self.assertEquals([2], parse('a=[1,2,3,4], a[1:3:2]')())
        self.assertEquals([3,4], parse('a=[1,2,3,4], a[2:]')())
        self.assertEquals([1,2], parse('a=[1,2,3,4], a[:2]')())
        self.assertEquals([4,3,2,1], parse('a=[1,2,3,4], a[::-1]')())

    def test_item_access_set(self):
        self.assertEquals([1,2,42,4], parse('a=[1,2,3,4], a[2]=42, a')())

    def test_slice_set(self):
        self.assertEquals([1,2,5,6], parse('a=[1,2,3,4], a[2:]=[5,6], a')())


        
class ParserErrorTestCase(unittest.TestCase):
    def test_exception_contains_line_number_on_different_line(self):
        with self.assertRaises(UnexpectedToken) as context:
            parse('2+2\n2+3\n  )')

        self.assertIn('line 3 column 3', context.exception.message)

    def test_exception_contains_line_number_on_same_line(self):
        with self.assertRaises(UnexpectedToken) as context:
            parse('2+2 2+3  )')

        self.assertIn('line 1 column 10', context.exception.message)

    def test_callable_with_missing_comma(self):
        scope = Scope({'add':lambda x, y:x+y})
        self.assertRaises(UnexpectedToken, parse, '2*add(2+2 3+3)')

    def test_multi_expr_program_with_error_in_the_last(self):
        self.assertRaises(UnexpectedToken, parse, '2+3, 4+5, )')

    def test_when_unknown_char(self):
        with self.assertRaises(InvalidSyntax) as context:
            parse('$')

        self.assertIn('line 1 column 1', context.exception.message)
    '''


if __name__ == '__main__':
    unittest.main()

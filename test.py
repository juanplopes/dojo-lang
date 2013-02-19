# -*- coding:utf8 -*-

import unittest
from dojo import dojo_compile, InvalidSyntax, UnexpectedToken

class CompilerTestCase(unittest.TestCase):
    def test_constant(self):
        self.assertEquals(42, dojo_compile('42')())
        
    def test_simple_binaries(self):
        self.assertEquals(44, dojo_compile('42+2')())
        self.assertEquals(40, dojo_compile('42-2')())
        self.assertEquals(84, dojo_compile('42*2')())
        self.assertEquals(21.5, dojo_compile('43/2')())
        self.assertEquals(21, dojo_compile('43//2')())
        self.assertEquals(2, dojo_compile('42%4')())
        self.assertEquals(1024, dojo_compile('2**10')())

    def test_empty_program(self):
        program = dojo_compile('   ')
        self.assertEquals(None, program())

    def test_empty_expression(self):
        program = dojo_compile('()')
        self.assertEquals(None, program())

    def test_2_plus_2_with_spaces(self):
        program = dojo_compile('2   \t+ \t2')
        self.assertEquals(4, program())

    def test_expression_list_ending_in_semicolon(self):
        program = dojo_compile('1+2;3*4;')
        self.assertEquals(12, program())

    def test_multi_expr_program(self):
        self.assertEquals(9, dojo_compile('2+3; 4+5')())

    def test_set_variable_and_get_after(self):
        self.assertEquals(5, dojo_compile('a=2; a+3')())

    def test_power_one_variable_to_another(self):
        self.assertEquals(1024, dojo_compile('a=2; b=10; a**b')())

    def test_unaries(self):
        program = dojo_compile('-2')
        self.assertEquals(-2, program())

    def test_unaries_ambiguity(self):
        program = dojo_compile('4\n-2')
        self.assertEquals(-2, program())

    def test_unaries_ambiguity_not(self):
        program = dojo_compile('4;-2')
        self.assertEquals(-2, program())

    def test_precedence(self):
        self.assertEquals(14, dojo_compile('2+3*4')())

    def test_explicit_precedence(self):
        self.assertEquals(20, dojo_compile('(2+3)*4')())

    def test_get_variable_from_global(self):
        self.assertEquals(5, dojo_compile('a+b')({'a':2,'b':3}))

    def test_local_variable_overrides_global(self):
        self.assertEquals(7, dojo_compile('b=5;a+b')({'a':2,'b':3}))

    def test_set_variable_is_also_expression(self):
        self.assertEquals(20, dojo_compile('a=(2+3)*4;c=b=a')())

    def test_callable(self):
        scope = {'add':lambda x, y:x+y}
        self.assertEquals(14, dojo_compile('2*add(5, 2)')(scope))
        
    def test_with_varargs(self):
        scope = {'add':lambda *x:x}
        self.assertEquals((5,2), dojo_compile('add(5, 2)')(scope))

    def test_null_callable_inside_block(self):
        scope = {'add':lambda:2, 'abc':3}
        self.assertEquals(2, dojo_compile('abc\n(add();add())')(scope))

    def test_double_callable(self):
        scope = {'add':lambda x:lambda y:x+y}
        self.assertEquals(14, dojo_compile('2*add(5)(2)')(scope))

    def test_callable_ambiguity(self):
        scope = {'add':lambda x:x+2}
        self.assertEquals(5, dojo_compile('add\n(5)')(scope))

    def test_callable_ambiguity_not(self):
        scope = {'add':lambda x:x+2}
        self.assertEquals(5, dojo_compile('add;(5)')(scope))

    def test_callable_with_non_primary(self):
        scope = {'add':lambda x, y:x+y}
        self.assertEquals(20, dojo_compile('2*add(2+2, 3+3)')(scope))

    def test_call_functions_multiline(self):
        scope = {'add':lambda a,b,c:a+b+c}
        self.assertEquals(18, dojo_compile("""add(
            2+2, 
            3+3
            ,4+4)""")(scope))

    def test_define_method_without_slash(self):
        self.assertEquals(1024, dojo_compile('pow10=x:x**10; pow10(2)')())

    def test_set_variable_from_inside_closure(self):
        self.assertEquals([1, 2, 3], dojo_compile('seq=/:(x=0; /: x=x+1); s = seq(); [s(), s(), s()]')())

    def test_define_method_and_use_later(self):
        self.assertEquals(1024, dojo_compile('pow2=/x,y:x**y; pow2(2, 10)')())

    def test_define_generator_method(self):
        self.assertEquals([2, 10], dojo_compile('def pow2(x,y):(yield x; yield y); list(pow2(2, 10))')())

    def test_define_named_method_and_use_later(self):
        self.assertEquals(1024, dojo_compile('def pow2(x,y):x**y; pow2(2, 10)')())

    def test_define_multiline_functions(self):
        self.assertEquals(1024, dojo_compile("""
            test = /x,y:(
                a = y**.5
                x**a
            )
            test(2, 100)
        """)())

    def test_define_multiline_functions_with_parenthesis_below(self):
        self.assertEquals(1024, dojo_compile("""
            test = /x,y:
            (
                a = y**.5
                x**a
            )
            test(2, 100)
        """)())

    def test_define_multiline_with_return_functions(self):
        self.assertEquals(1024, dojo_compile("""
            test = /x,y:(
                a = y**.5
                return x**a
            )
            test(2, 100)
        """)())

    def test_define_method_with_closure_and_use_later(self):
        self.assertEquals(1024, dojo_compile('pow=x:y:x**y; pow(2)(10)')())

    def test_recursive_method(self):
        self.assertEquals(55, dojo_compile('def fib(n): n<=2 and 1 or fib(n-1)+ fib(n-2); fib(10)')())


    def test_define_method_and_use_later_accessing_outside_variables(self):
        self.assertEquals(1024, dojo_compile('z=10; pow=/x:x**z; pow(2)')())

    def test_equality_operator(self):
        self.assertEquals(True, dojo_compile('a=2; b=2; a==b')())
        self.assertEquals(False, dojo_compile('a=2; b=3; a==b')())


    def test_inequality_operator(self):
        self.assertEquals(False, dojo_compile('a=2; b=2; a!=b')())
        self.assertEquals(True, dojo_compile('a=2; b=3; a!=b')())

    def test_in_not_int(self):
        self.assertEquals(True, dojo_compile('2 in [1,2,3]')())
        self.assertEquals(False, dojo_compile('4 in [1,2,3]')())

        self.assertEquals(False, dojo_compile('2 not in [1,2,3]')())
        self.assertEquals(True, dojo_compile('4 not in [1,2,3]')())

        self.assertEquals(False, dojo_compile('2 not  \t\n in [1,2,3]')())
        self.assertEquals(True, dojo_compile('4 not \t\n in [1,2,3]')())


    def test_comparation_operators(self):
        self.assertEquals(False, dojo_compile('a=2; b=3; a>b')())
        self.assertEquals(True, dojo_compile('a=2; b=3; a<b')())

        self.assertEquals(False, dojo_compile('a=2; b=3; a>=b')())
        self.assertEquals(True, dojo_compile('a=2; b=3; a<=b')())

        self.assertEquals(True, dojo_compile('a=2; b=2; a>=b')())
        self.assertEquals(True, dojo_compile('a=2; b=2; a<=b')())

    def test_not_operator(self):
        self.assertEquals(True, dojo_compile('not 2+2==5')())
        self.assertEquals(False, dojo_compile('not 2+2==4')())

    def test_binary_invert_operator(self):
        self.assertEquals(-43, dojo_compile('~42')())

    def test_binary_shift(self):
        self.assertEquals(42<<2, dojo_compile('42<<2')())
        self.assertEquals(42>>2, dojo_compile('42>>2')())

    def test_bitwise_ops(self):
        self.assertEquals(8, dojo_compile('42&12')())
        self.assertEquals(46, dojo_compile('42|12')())
        self.assertEquals(38, dojo_compile('42^12')())

    def test_list_literal(self):
        self.assertEquals([1,2,3,4], dojo_compile('[1,2,2+1,2*2]')())
        self.assertEquals([1,2,3,4], dojo_compile('[1,2,2+1,2*2,]')())

    def test_string_literal(self):
        self.assertEquals('"abc', dojo_compile("'\"abc'")())
        self.assertEquals("'abc", dojo_compile('"\'abc"')())

    def test_dict_literal(self):
        self.assertEquals({}, dojo_compile('{}')())
        self.assertEquals({'abc':123, 456:'qwe'}, dojo_compile('{"abc":123, 456:"qwe"}')())

    def test_range_literal(self):
        obj = dojo_compile('5..8')()
        it = iter(obj)
        self.assertEquals(5, next(it))
        self.assertEquals(6, next(it))
        self.assertEquals(7, next(it))
        self.assertRaises(StopIteration, next, it)
    
    def test_range_with_step(self):
        obj = dojo_compile('5..10:2')()
        it = iter(obj)
        self.assertEquals(5, next(it))
        self.assertEquals(7, next(it))
        self.assertEquals(9, next(it))
        self.assertRaises(StopIteration, next, it)    

    def test_pipe_forward(self):
        scope = {'inc2':lambda a: a+2}
        self.assertEquals(44, dojo_compile('42 |> inc2')(scope))

    def test_partial_apply(self):
        scope = {'filter':filter}
        self.assertEquals(list(range(2, 20, 2)), dojo_compile('1..20 |> filter{/x:x%2==0} |> list')(scope))

    def test_composition(self):
        scope = {'inc2':lambda a: a+2, 'str': str}
        self.assertEquals('44', dojo_compile('42 |> inc2 => str')(scope))

    def test_import_module(self):
        math = __import__('math')
        self.assertEquals([math, math], dojo_compile('[import math, math]')())
        
    def test_import_module_items(self):
        math = __import__('math')
        self.assertEquals([math, math.sqrt, math.cos, math.log], dojo_compile('[import math(sqrt, cos, log), sqrt, cos, log]')())

    def test_import_then_call(self):
        self.assertEquals(2.0, dojo_compile('import math(sqrt); test=/x:sqrt(x); test(4)')())

    def test_import_module_ambiguity(self):
        scope = {'sqrt':3}
        math = __import__('math')
        self.assertEquals(3, dojo_compile('import math\n(sqrt)')(scope))

    def test_and_operator(self):
        counter = [0]
        def function(): 
            counter[0]+=1
            return True

        scope = ({'print': function})
        
        self.assertEquals(False, dojo_compile('2+2==5 and print()')(scope))
        self.assertEquals(0, counter[0])
        
        self.assertEquals(True, dojo_compile('2+2==4 and print()')(scope))
        self.assertEquals(1, counter[0])

    def test_if_else(self):
        counter = [0]
        def function(): 
            counter[0]+=1
            return 'abc'

        scope = ({'print': function})
        
        self.assertEquals(None, dojo_compile('if 2+2==5: print()')(scope))
        self.assertEquals(0, counter[0])
        
        self.assertEquals('abc', dojo_compile('if 2+2==4: print()')(scope))
        self.assertEquals(1, counter[0])
        
        self.assertEquals('qwe', dojo_compile('if 2+2==5: print() else: "qwe"')(scope))
        self.assertEquals(1, counter[0])
        
        self.assertEquals('abc', dojo_compile('if 2+2==4: print() else: "qwe"')(scope))
        self.assertEquals(2, counter[0])

    def test_if_else_blocks(self):
        counter = [0]
        def function(): 
            counter[0]+=1
            return 'abc'

        scope = ({'print': function})
        
        self.assertEquals(None, dojo_compile('if 2+2==5: (print();print())')(scope))
        self.assertEquals(0, counter[0])
        
        self.assertEquals('abc', dojo_compile('if 2+2==4: (print();print())')(scope))
        self.assertEquals(2, counter[0])
        
        self.assertEquals('bbb', dojo_compile('if 2+2==5: (print();print()) else: ("qwe";"bbb")')(scope))
        self.assertEquals(2, counter[0])
        
        self.assertEquals('abc', dojo_compile('if 2+2==4: (print();print()) else: ("qwe";"bbb")')(scope))
        self.assertEquals(4, counter[0])

    def test_if_elif_else_blocks(self):
        counter = [0]
        def function(): 
            counter[0]+=1
            return 'abc'

        scope = ({'print': function})
        
        self.assertEquals('abc', dojo_compile('if 2+2==5: (print()) elif 2+2==4: (print(); print()) else: ()')(scope))
        self.assertEquals(2, counter[0])

        self.assertEquals(3, dojo_compile('if 2+2==5: (print()) elif 2+2==6: (print(); print()) else: 3')(scope))
        self.assertEquals(2, counter[0])


    def test_return_if_expression(self):
        self.assertEquals(1, dojo_compile('return if 2+2==4: 1')())

    def test_or_operator(self):
        counter = [0]
        def function(): 
            counter[0]+=1
            return False

        scope = ({'print': function})

        self.assertEquals(False, dojo_compile('2+2==5 or print()')(scope))
        self.assertEquals(1, counter[0])
        
        self.assertEquals(True, dojo_compile('2+2==4 or print()')(scope))
        self.assertEquals(1, counter[0])

        self.assertEquals(True, dojo_compile('2+2==4 or 2+3==5')(scope))
        self.assertEquals(1, counter[0])

    def test_member_access(self):
        scope = ({'str': str, 'map': map})
        self.assertEquals('1,2,3,4', dojo_compile('[1,2,3,4] |> map{str} |> ",".join')(scope))

    def test_set_member(self):
        self.assertEquals(4, dojo_compile('import _ast(If); i = If(); i.lineno = 2; i.lineno*2')())

    def test_item_access(self):
        self.assertEquals(3, dojo_compile('a=[1,2,3,4]; a[2]')())

    def test_item_slice(self):
        self.assertEquals([2,4], dojo_compile('a=[1,2,3,4]; a[1:4:2]')())
        self.assertEquals([4,3,2], dojo_compile('a=[1,2,3,4]; a[:0:-1]')())
        self.assertEquals([1,2,3,4], dojo_compile('a=[1,2,3,4]; a[::]')())
        self.assertEquals([2,4], dojo_compile('a=[1,2,3,4]; a[1::2]')())
        self.assertEquals([1,3], dojo_compile('a=[1,2,3,4]; a[::2]')())
        self.assertEquals([2], dojo_compile('a=[1,2,3,4]; a[1:3:2]')())
        self.assertEquals([3,4], dojo_compile('a=[1,2,3,4]; a[2:]')())
        self.assertEquals([1,2], dojo_compile('a=[1,2,3,4]; a[:2]')())
        self.assertEquals([4,3,2,1], dojo_compile('a=[1,2,3,4]; a[::-1]')())

    def test_item_access_set(self):
        self.assertEquals([1,2,42,4], dojo_compile('a=[1,2,3,4]; a[2]=42; a')())

    def test_slice_set(self):
        self.assertEquals([1,2,5,6], dojo_compile('a=[1,2,3,4]; a[2:]=[5,6]; a')())

class CompilerErrorTestCase(unittest.TestCase):
    def test_exception_contains_line_number_on_different_line(self):
        with self.assertRaises(UnexpectedToken) as context:
            dojo_compile('2+2\n2+3\n  )')

        self.assertIn('line 3 column 3', context.exception.args[0])

    def test_exception_contains_line_number_on_same_line(self):
        with self.assertRaises(UnexpectedToken) as context:
            dojo_compile('2+2; 2+3  )')

        self.assertIn('line 1 column 11', context.exception.args[0])

    def test_cant_have_two_expressions_on_same_line_without_semicolon(self):
        self.assertRaises(UnexpectedToken, dojo_compile, '2+2 3+3')

    def test_callable_with_missing_comma(self):
        scope = ({'add':lambda x, y:x+y})
        self.assertRaises(UnexpectedToken, dojo_compile, '2*add(2+2 3+3)')

    def test_multi_expr_program_with_error_in_the_last(self):
        self.assertRaises(UnexpectedToken, dojo_compile, '2+3; 4+5; )')

    def test_when_unknown_char(self):
        with self.assertRaises(InvalidSyntax) as context:
            dojo_compile('$')

        self.assertIn('line 1 column 1', context.exception.args[0])

if __name__ == '__main__':
    unittest.main(verbosity=2)
    #unittest.TextTestRunner(verbosity=2).run(unittest.TestLoader().loadTestsFromTestCase(ParserTestCase))

# -*- coding:utf8 -*-

import unittest
from parser import parse
from ast import Scope

class ParserTestCase(unittest.TestCase):
    def test_simple_binaries(self):
        self.assertEquals(44, parse('42+2')())
        self.assertEquals(40, parse('42-2')())
        self.assertEquals(84, parse('42*2')())
        self.assertEquals(21, parse('42/2')())
        self.assertEquals(1024, parse('2**10')())

    def test_2_plus_2_with_spaces(self):
        program = parse('2   \t+ \t2')
        self.assertEquals(4, program())

    def test_expression_list_ending_in_comma(self):
        program = parse('1+2,3*4,')
        self.assertEquals(12, program())
        
    def test_unaries(self):
        program = parse('-2')
        self.assertEquals(-2, program())

    def test_unaries_ambiguity(self):
        program = parse('4\n-2')
        self.assertEquals(-2, program())

    def test_unaries_ambiguity_not(self):
        program = parse('4,-2')
        self.assertEquals(-2, program())

    def test_precedence(self):
        self.assertEquals(14, parse('2+3*4')())

    def test_explicit_precedence(self):
        self.assertEquals(20, parse('(2+3)*4')())

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

    def test_callable_ambiguity(self):
        scope = Scope({'add':lambda x, y:x+y})
        self.assertEquals(2, parse('add\n(5, 2)')(scope))

    def test_callable_ambiguity_not(self):
        scope = Scope({'add':lambda x, y:x+y})
        self.assertEquals(2, parse('add,(5, 2)')(scope))


    def test_callable_with_missing_comma(self):
        scope = Scope({'add':lambda x, y:x+y})
        self.assertRaises(Exception, parse, '2*add(2+2 3+3)')

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

    def test_multi_expr_program_with_error_in_the_last(self):
        self.assertRaises(Exception, parse, '2+3, 4+5, )')

    def no_such_thing_as_empty_program(self):
        self.assertRaises(Exception, parse, '')

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


if __name__ == '__main__':
    unittest.main()

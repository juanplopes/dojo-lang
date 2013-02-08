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

    def test_precedence(self):
        self.assertEquals(14, parse('2+3*4')())

    def test_explicit_precedence(self):
        self.assertEquals(20, parse('(2+3)*4')())

    def test_callable(self):
        scope = Scope({'add':lambda x, y:x+y})
        self.assertEquals(14, parse('2*add(5, 2)')(scope))

    def test_callable_with_missing_comma(self):
        scope = Scope({'add':lambda x, y:x+y})
        self.assertRaises(Exception, parse, '2*add(2+2 3+3)')

    def test_callable_with_non_primary(self):
        scope = Scope({'add':lambda x, y:x+y})
        self.assertEquals(20, parse('2*add(2+2, 3+3)')(scope))

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



if __name__ == '__main__':
    unittest.main()

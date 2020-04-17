from __future__ import division
from pyparsing import (Literal, CaselessLiteral, Word, Combine, Group, Optional,
                       ZeroOrMore, Forward, nums, alphas, oneOf, ParseException, alphanums, delimitedList,)
import math
import operator

import numpy as np
from numpy import cos, sin, tan, cosh, sinh, tanh, log, log10, sqrt, exp
from numpy.fft import *

__author__ = 'Paul McGuire'
__version__ = '$Revision: 0.0 $'
__date__ = '$Date: 2009-03-20 $'
__source__ = '''http://pyparsing.wikispaces.com/file/view/fourFn.py
http://pyparsing.wikispaces.com/message/view/home/15549426
'''
__note__ = '''
All I've done is rewrap Paul McGuire's eqn_parser.py as a class, so I can use it
more easily in other places.

https://stackoverflow.com/a/2371789
https://github.com/pyparsing/pyparsing/blob/master/examples/fourFn.py
'''


def cmp(a, b):
    return (a > b) - (a < b)


class NumericStringParser(object):
    """
    Most of this code comes from the eqn_parser.py pyparsing example
    """

    def pushFirst(self, toks):
        self.exprStack.append(toks[0])

    def pushUMinus(self, toks):
        if toks and toks[0] == '-':
            self.exprStack.append('unary -')

    def __init__(self):
        self.variables = {}

        """
        expop   :: '^'
        multop  :: '*' | '/'
        addop   :: '+' | '-'
        integer :: ['+' | '-'] '0'..'9'+
        atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
        factor  :: atom [ expop factor ]*
        term    :: factor [ multop factor ]*
        expr    :: term [ addop term ]*
        """
        point = Literal(".")
        e = CaselessLiteral("E")
        fnumber = Combine(Word("+-" + nums, nums) +
                          Optional(point + Optional(Word(nums))) +
                          Optional(e + Word("+-" + nums, nums)))
        variable = Word(alphas, max=1)  # single letter variable, such as x, z, m, etc.
        ident = Word(alphas, alphas + nums + "_$")
        plus = Literal("+")
        minus = Literal("-")
        mult = Literal("*")
        div = Literal("/")
        lpar = Literal("(").suppress()
        rpar = Literal(")").suppress()
        addop = plus | minus
        multop = mult | div
        expop = Literal("^")
        pi = CaselessLiteral("PI")
        expr = Forward()
        expr_list = delimitedList(Group(expr))
        # add parse action that replaces the function identifier with a (name, number of args) tuple
        fn_call = (ident + lpar - Group(expr_list) + rpar).setParseAction(
            lambda t: t.insert(0, (t.pop(0), len(t[0])))
        )
        atom = (
                addop[...]
                + (
                        (fn_call | pi | e | fnumber | ident).setParseAction(self.pushFirst)
                        | Group(lpar + expr + rpar)
                )
        ).setParseAction(self.pushUMinus)
        # by defining exponentiation as "atom [ ^ factor ]..." instead of
        # "atom [ ^ atom ]...", we get right-to-left exponents, instead of left-to-right
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor << atom + \
        ZeroOrMore((expop + factor).setParseAction(self.pushFirst))
        term = factor + \
               ZeroOrMore((multop + factor).setParseAction(self.pushFirst))
        expr << term + \
        ZeroOrMore((addop + term).setParseAction(self.pushFirst))
        # addop_term = ( addop + term ).setParseAction( self.pushFirst )
        # general_term = term + ZeroOrMore( addop_term ) | OneOrMore( addop_term)
        # expr <<  general_term
        self.bnf = expr
        # map operator symbols to corresponding arithmetic operations
        epsilon = 1e-12
        self.opn = {"+": operator.add,
                    "-": operator.sub,
                    "*": operator.mul,
                    "/": operator.truediv,
                    "^": operator.pow}
        self.fn = {"sin": sin,
                   "cos": cos,
                   "tan": tan,
                   "exp": exp,
                   "fft": fft,
                   "abs": abs,
                   "trunc": lambda a: int(a),
                   "round": round,
                   "sgn": lambda a: abs(a) > epsilon and cmp(a, 0) or 0}

    def evaluateStack(self, s):
        op, num_args = s.pop(), 0
        if isinstance(op, tuple):
            op, num_args = op
        if op == "unary -":
            return -self.evaluateStack(s)
        if op in "+-*/^":
            # note: operands are pushed onto the stack in reverse order
            op2 = self.evaluateStack(s)
            op1 = self.evaluateStack(s)
            return self.opn[op](op1, op2)
        elif op == "PI":
            return math.pi  # 3.1415926535
        elif op == "E":
            return math.e  # 2.718281828
        elif op in self.fn:
            # note: args are pushed onto the stack in reverse order
            args = reversed([self.evaluateStack(s) for _ in range(num_args)])
            return self.fn[op](*args)
        elif op[0].isalpha():
            if op in self.variables:
                return self.variables[op]
            raise Exception("invalid identifier '%s'" % op)
        else:
            # try to evaluate as int first, then as float if int fails
            try:
                return int(op)
            except ValueError:
                return float(op)

    def expr(self, input_string, parseAll=True):
        self.exprStack = []
        try:
            results = self.bnf.parseString(input_string, parseAll)
        except ParseException as err:
            results = ["Parse Failure", input_string, (str(err), err.line, err.column)]

    def eval(self, variables):
        self.variables = variables
        print(self.exprStack)
        val = self.evaluateStack(self.exprStack)
        return val

    # def eval(self, input_string, variables, parseAll=True):
    #     self.exprStack = []
    #     self.variables = variables
    #     try:
    #         results = self.bnf.parseString(input_string, parseAll)
    #     except ParseException as err:
    #         results = ["Parse Failure", input_string, (str(err), err.line, err.column)]
    #
    #     # for i, ob in enumerate(self.exprStack):
    #     #     print(f'idx: {i}, ob: {ob}')
    #     #     if isinstance(ob, str) and ob in variables:
    #     #         self.exprStack[i] = str(variables[ob])
    #
    #     val = self.evaluateStack(self.exprStack)
    #     return val


# ----------------------------------------------------------------------------------------------------------------------

nsp = NumericStringParser()

if __name__ == "__main__":
    # input_string
    input_string = ""
    variables = {"x": 1, "y": 2, "z": np.asarray([1, 2, 3])}
    # Display instructions on how to quit the program
    print("Type in the string to be parsed or 'quit' to exit the program")
    input_string = input("> ")

    while input_string.strip().lower() != "quit":
        nsp.expr(input_string)
        result = nsp.eval(variables)
        print(result)

        # obtain new input string
        input_string = input("> ")

    # if user type 'quit' then say goodbye
    print("Good bye!")

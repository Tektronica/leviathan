from pyparsing import (Literal, Word, Group, Forward,
                       alphas, alphanums, Regex, ParseException,
                       CaselessKeyword, Suppress, delimitedList,)

# Uncomment the line below for readline support on interactive terminal
# import readline

# from fourFn import BNF, exprStack, evaluate_stack
import math
import operator

exprStack = []


def push_first(toks):
    exprStack.append(toks[0])


def push_unary_minus(toks):
    for t in toks:
        if t == "-":
            exprStack.append("unary -")
        else:
            break


bnf = None


def BNF():
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
    global bnf
    if not bnf:
        # use CaselessKeyword for e and pi, to avoid accidentally matching
        # functions that start with 'e' or 'pi' (such as 'exp'); Keyword
        # and CaselessKeyword only match whole words
        e = CaselessKeyword("E")
        pi = CaselessKeyword("PI")
        # fnumber = Combine(Word("+-"+nums, nums) +
        #                    Optional("." + Optional(Word(nums))) +
        #                    Option al(e + Word("+-"+nums, nums)))
        # or use provided pyparsing_common.number, but convert back to str:
        # fnumber = ppc.number().addParseAction(lambda t: str(t[0]))
        fnumber = Regex(r"[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?")
        ident = Word(alphas, alphanums + "_$")

        plus, minus, mult, div = map(Literal, "+-*/")
        lpar, rpar = map(Suppress, "()")
        addop = plus | minus
        multop = mult | div
        expop = Literal("^")

        expr = Forward()
        expr_list = delimitedList(Group(expr))
        # add parse action that replaces the function identifier with a (name, number of args) tuple
        fn_call = (ident + lpar - Group(expr_list) + rpar).setParseAction(
            lambda t: t.insert(0, (t.pop(0), len(t[0])))
        )
        atom = (
                addop[...]
                + (
                        (fn_call | pi | e | fnumber | ident).setParseAction(push_first)
                        | Group(lpar + expr + rpar)
                )
        ).setParseAction(push_unary_minus)

        # by defining exponentiation as "atom [ ^ factor ]..." instead of "atom [ ^ atom ]...", we get right-to-left
        # exponents, instead of left-to-right that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor <<= atom + (expop + factor).setParseAction(push_first)[...]
        term = factor + (multop + factor).setParseAction(push_first)[...]
        expr <<= term + (addop + term).setParseAction(push_first)[...]
        bnf = expr
    return bnf


# map operator symbols to corresponding arithmetic operations
epsilon = 1e-12
opn = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "^": operator.pow,
}

fn = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "exp": math.exp,
    "abs": abs,
    "trunc": lambda a: int(a),
    "round": round,
    "sgn": lambda a: -1 if a < -epsilon else 1 if a > epsilon else 0,
}


def evaluate_stack(s):
    op, num_args = s.pop(), 0
    if isinstance(op, tuple):
        op, num_args = op
    if op == "unary -":
        return -evaluate_stack(s)
    if op in "+-*/^":
        # note: operands are pushed onto the stack in reverse order
        op2 = evaluate_stack(s)
        op1 = evaluate_stack(s)
        return opn[op](op1, op2)
    elif op == "PI":
        return math.pi  # 3.1415926535
    elif op == "E":
        return math.e  # 2.718281828
    elif op in fn:
        # note: args are pushed onto the stack in reverse order
        args = reversed([evaluate_stack(s) for _ in range(num_args)])
        return fn[op](*args)
    elif op[0].isalpha():
        raise Exception("invalid identifier '%s'" % op)
    else:
        # try to evaluate as int first, then as float if int fails
        try:
            return int(op)
        except ValueError:
            return float(op)


# ----------------------------------------------------------------------------------------------------------------------

# Debugging flag can be set to either "debug_flag=True" or "debug_flag=False"
debug_flag = False
variables = {}

arithExpr = BNF()
ident = Word(alphas, alphanums).setName("identifier")
assignment = ident("varname") + "=" + arithExpr
pattern = assignment | arithExpr

if __name__ == "__main__":
    # input_string
    input_string = ""

    # Display instructions on how to quit the program
    print("Type in the string to be parsed or 'quit' to exit the program")
    input_string = input("> ")

    while input_string.strip().lower() != "quit":
        if input_string.strip().lower() == "debug":
            debug_flag = True
            input_string = input("> ")
            continue

        # Reset to an empty exprStack
        del exprStack[:]

        if input_string != "":
            # try parsing the input string
            try:
                L = pattern.parseString(input_string, parseAll=True)
            except ParseException as err:
                L = ["Parse Failure", input_string, (str(err), err.line, err.column)]

            # show result of parsing the input string
            if debug_flag:
                print(input_string, "->", L)
            if len(L) == 0 or L[0] != "Parse Failure":
                if debug_flag:
                    print("exprStack=", exprStack)

                for i, ob in enumerate(exprStack):
                    if isinstance(ob, str) and ob in variables:
                        exprStack[i] = str(variables[ob])

                # calculate result , store a copy in ans , display the result to user
                try:
                    result = evaluate_stack(exprStack)
                except Exception as e:
                    print(str(e))
                else:
                    variables["ans"] = result
                    print(result)

                    # Assign result to a variable if required
                    if L.varname:
                        variables[L.varname] = result
                    if debug_flag:
                        print("variables=", variables)
            else:
                print("Parse Failure")
                err_str, err_line, err_col = L[-1]
                print(err_line)
                print(" " * (err_col - 1) + "^")
                print(err_str)

        # obtain new input string
        input_string = input("> ")

    # if user type 'quit' then say goodbye
    print("Good bye!")
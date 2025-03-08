from collections import deque
import numpy as np
from typing import List, Tuple
from code_detection.astnodes import *

def get_overall_bounds(bounds: List[List[Tuple[int, int]]]):
    min_x = min([min([x for x, y in box]) for box in bounds])
    min_y = min([min([y for x, y in box]) for box in bounds])
    max_x = max([max([x for x, y in box]) for box in bounds])
    max_y = max([max([y for x, y in box]) for box in bounds])

    # Check this later
    return [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]

def parse_statement(tokens: deque):
    statement = None
    next, next_bounds = tokens.popleft()
    if next == "Print":
        statement, tokens = parse_print(tokens, next_bounds)
    elif next == "If":
        statement, tokens = parse_if_statement(tokens, next_bounds)
    elif next == "Return":
        statement, tokens = parse_return(tokens, next_bounds)
    elif next == "For":
        statement, tokens = parse_for(tokens, next_bounds)
    elif next == "While":
        statement, tokens = parse_while(tokens, next_bounds)
    elif next == "Call":
        statement, tokens = parse_call(tokens, next_bounds)
    else:
        statement, tokens = parse_custom_statement(tokens, next, next_bounds)
    
    return statement, tokens

def parse_function(tokens: deque, function_bounds: List[Tuple[int, int]]):
    name, name_bounds = tokens.popleft()
    function_bounds = get_overall_bounds([function_bounds, name_bounds])

    next, next_bounds = tokens.popleft()
    function_bounds = get_overall_bounds([function_bounds, next_bounds])

    if next != "LineBreak":
        raise Exception("Expected LineBreak")
    
    args = ""
    next, next_bounds = tokens.popleft()
    function_bounds = get_overall_bounds([function_bounds, next_bounds])
    if next == "Take":
        next, next_bounds = tokens.popleft()
        while next != "LineBreak":
            args += next
            args += " "
            function_bounds = get_overall_bounds([function_bounds, next_bounds])
            next, next_bounds = tokens.popleft()
    
    args = args.strip().split(",")
    args = [arg.strip() for arg in args]

    next, next_bounds = tokens.popleft()
    function_bounds = get_overall_bounds([function_bounds, next_bounds])
    if next != "Do":
        raise Exception("Expected Do")
    
    statements = []
    next, next_bounds = tokens.popleft()
    function_bounds = get_overall_bounds([function_bounds, next_bounds])
    while next != "End":
        tokens.appendleft((next, next_bounds))
        stmt, tokens = parse_statement(tokens)
        function_bounds = get_overall_bounds([function_bounds, stmt.bounds])
        statements.append(stmt)
        next, next_bounds = tokens.popleft()
    function_bounds = get_overall_bounds([function_bounds, next_bounds])

    next, next_bounds = tokens.popleft()
    if next != "LineBreak":
        raise Exception("Expected LineBreak")

    function = Function(function_bounds, Identifier(name_bounds, name), args, statements)
    print("Parsed function ", function.python_print())

    return function, tokens


def parse_print(tokens: deque, print_bounds: List[Tuple[int, int]]):
    expr, expr_bounds = tokens.popleft()

    next, next_bounds = tokens.popleft()

    while next != "LineBreak" and not tokens.empty():
        expr += " "
        expr += next
        expr_bounds = get_overall_bounds([expr_bounds, next_bounds])
        next, next_bounds = tokens.popleft()

    if next != "LineBreak":
        raise Exception("Expected LineBreak")

    expr = Expr(expr_bounds, expr)

    new_bounds = get_overall_bounds([print_bounds, expr_bounds])

    stmt = PrintStatement(new_bounds, expr)

    print("Parsed print statement ", stmt.python_print())
    
    return stmt, tokens

def parse_return(tokens: deque, return_bounds: List[Tuple[int, int]]):
    expr, expr_bounds = tokens.popleft()

    next, next_bounds = tokens.popleft()

    while next != "LineBreak" and not tokens.empty():
        expr += " "
        expr += next
        expr_bounds = get_overall_bounds([expr_bounds, next_bounds])
        next, next_bounds = tokens.popleft()

    if next != "LineBreak":
        raise Exception("Expected LineBreak")

    expr = Expr(expr_bounds, expr)

    new_bounds = get_overall_bounds([return_bounds, expr_bounds])

    stmt = ReturnStatement(new_bounds, expr)

    print("Parsed return statement ", stmt.python_print())
    
    return stmt, tokens

def parse_condition(tokens: deque):
    condition = ""
    next, next_bounds = tokens.popleft()
    condition_bounds = next_bounds

    while next != "LineBreak":
        if condition != "":
            condition += " "
        condition += next
        condition_bounds = get_overall_bounds([condition_bounds, next_bounds])
        next, next_bounds = tokens.popleft()

    return Expr(condition_bounds, condition), tokens

def parse_statement_block(tokens: deque, end_conditions: List[str]):
    statements = []
    next, next_bounds = tokens.popleft()
    statement_bounds = next_bounds

    while next not in end_conditions:
        tokens.appendleft((next, next_bounds))
        stmt, tokens = parse_statement(tokens)
        statements.append(stmt)
        statement_bounds = get_overall_bounds([statement_bounds, stmt.bounds])
        next, next_bounds = tokens.popleft()

    return statements, statement_bounds, next, next_bounds

def parse_if_statement(tokens: deque, if_bounds: List[Tuple[int, int]]):
    conditions = []
    bodies = []

    next, next_bounds = tokens.popleft()
    if_bounds = get_overall_bounds([if_bounds, next_bounds])

    while next != "End":
        if next != "Else":
            tokens.appendleft((next, next_bounds))
            condition, tokens = parse_condition(tokens)
            conditions.append(condition)
            if_bounds = get_overall_bounds([if_bounds, condition.bounds])

            next, next_bounds = tokens.popleft()
            if next != "Then":
                raise Exception("Expected Then")

        body, body_bounds, next, next_bounds = parse_statement_block(tokens, ["End", "Else If", "Else"])
        bodies.append(body)
        if_bounds = get_overall_bounds([if_bounds, body_bounds])

    if_bounds = get_overall_bounds([if_bounds, next_bounds])
    next, next_bounds = tokens.popleft()
    if next != "LineBreak":
        raise Exception("Expected LineBreak")

    stmt = IfStatement(if_bounds, conditions, bodies)

    print("Parsed if statement ", stmt.python_print())

    return stmt, tokens

def parse_custom_statement(tokens: deque, token: str, statement_bounds: List[Tuple[int, int]]):
    next, next_bounds = tokens.popleft()

    while next != "LineBreak" and next != "Call" and not len(tokens) == 0:
        token += " "
        token += next
        statement_bounds = get_overall_bounds([statement_bounds, next_bounds])
        next, next_bounds = tokens.popleft()

    if next == "Call":
        call_stmt, tokens = parse_call(tokens, statement_bounds)
        statement_bounds = get_overall_bounds([statement_bounds, call_stmt.bounds])

        token = token.strip()
        stmt = AssignCall(statement_bounds, token, call_stmt)

        print("Parsed assign call statement ", stmt.python_print())

        return stmt, tokens
    elif next != "LineBreak":
        raise Exception("Expected LineBreak")
    
    stmt = CustomStatement(statement_bounds, token)

    print("Parsed custom statement ", stmt.python_print())

    return stmt, tokens

def parse_while(tokens: deque, while_bounds):
    condition, tokens = parse_condition(tokens)
    while_bounds = get_overall_bounds([while_bounds, condition.bounds])

    next, next_bounds = tokens.popleft()
    if next != "Do":
        raise Exception("Expected Do")
    while_bounds = get_overall_bounds([while_bounds, next_bounds])

    body, body_bounds, next, next_bounds = parse_statement_block(tokens, ["End"])
    while_bounds = get_overall_bounds([while_bounds, body_bounds])

    next, next_bounds = tokens.popleft()
    if next != "LineBreak":
        raise Exception("Expected LineBreak")

    stmt = WhileStatement(while_bounds, condition, body)

    print("Parsed while statement ", stmt.python_print())

    return stmt, tokens

def parse_for(tokens: deque, for_bounds: List[Tuple[int, int]]):
    count, count_bounds = tokens.popleft()
    for_bounds = get_overall_bounds([for_bounds, count_bounds])

    next, next_bounds = tokens.popleft()
    if next != "From":
        raise Exception("Expected LineBreak")
    for_bounds = get_overall_bounds([for_bounds, next_bounds])

    lower_bound, lower_bound_bounds = tokens.popleft()
    next, next_bounds = tokens.popleft()
    while next != "To":
        lower_bound += " "
        lower_bound += next
        lower_bound_bounds = get_overall_bounds([lower_bound_bounds, next_bounds])
        next, next_bounds = tokens.popleft()
    for_bounds = get_overall_bounds([for_bounds, lower_bound_bounds, next_bounds])

    upper_bound, upper_bound_bounds = tokens.popleft()

    next, next_bounds = tokens.popleft()
    while next != "LineBreak":
        upper_bound += " "
        upper_bound += next
        upper_bound_bounds = get_overall_bounds([upper_bound_bounds, next_bounds])
        next, next_bounds = tokens.popleft()
    for_bounds = get_overall_bounds([for_bounds, next_bounds, upper_bound_bounds])

    next, next_bounds = tokens.popleft()
    if next != "Do":
        raise Exception("Expected Do")
    for_bounds = get_overall_bounds([for_bounds, next_bounds])

    body, body_bounds, next, next_bounds = parse_statement_block(tokens, ["End"])
    for_bounds = get_overall_bounds([for_bounds, body_bounds])

    if next != "End":
        raise Exception("Expected End")
    for_bounds = get_overall_bounds([for_bounds, next_bounds])
    
    next, next_bounds = tokens.popleft()
    if next != "LineBreak":
        raise Exception("Expected LineBreak")

    stmt = ForStatement(for_bounds, Identifier(count_bounds, count), Expr(lower_bound_bounds, lower_bound), Expr(upper_bound_bounds, upper_bound), body)

    print("Parsed for statement ", stmt.python_print())

    return stmt, tokens

def parse_call(tokens: deque, call_bounds: List[Tuple[int, int]]):
    function_name, function_name_bounds = tokens.popleft()
    call_bounds = get_overall_bounds([call_bounds, function_name_bounds])

    next, next_bounds = tokens.popleft()
    if next != "With":
        raise Exception("Expected With")
    call_bounds = get_overall_bounds([call_bounds, next_bounds])

    arguments = ""
    next, next_bounds = tokens.popleft()
    while next != "LineBreak":
        arguments += next
        arguments += " "
        call_bounds = get_overall_bounds([call_bounds, next_bounds])
        next, next_bounds = tokens.popleft()
    call_bounds = get_overall_bounds([call_bounds, next_bounds])

    arguments = arguments.strip().split(",")
    arguments = [arg.strip() for arg in arguments]

    stmt = Call(call_bounds, function_name, arguments)

    print("Parsed call statement ", stmt.python_print())

    return stmt, tokens

def parse_code(tokens: deque):
    program = Program([(0,0), (0,0), (0,0), (0,0)], [], [])

    while len(tokens) > 0:
        token, bounds = tokens.popleft()
        match token:
            case "Function":
                function, tokens = parse_function(tokens, bounds)
                program.add_function(function)
            case "Print":
                stmt, tokens = parse_print(tokens, bounds)
                program.add_statement(stmt)
            case "If":
                stmt, tokens = parse_if_statement(tokens, bounds)
                program.add_statement(stmt)
            case "Return":
                stmt, tokens = parse_return(tokens, bounds)
                program.add_statement(stmt)
            case "For":
                stmt, tokens = parse_for(tokens, bounds)
                program.add_statement(stmt)
            case "While":
                stmt, tokens = parse_while(tokens, bounds)
                program.add_statement(stmt)
            case "Call":
                stmt, tokens = parse_call(tokens, bounds)
                program.add_statement(stmt)
            case _:
                stmt, tokens = parse_custom_statement(tokens, token, bounds)
                program.add_statement(stmt)
    
    return program

def test_python_printing(prog: Program):
    print("\nCode:\n")
    print(prog.python_print())
    return prog.python_print()

def tokens_1():
    tokens = deque()
    tokens.append(("Function", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("foo", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("Take", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("x", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("Do", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("If", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("x == 5", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("Then", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("Print", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("x", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("Else", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("Print", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("y", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("End", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("Return", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("Z", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("End", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))



    tokens.append(("y = 3", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("While", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("y < 5", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("Do", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("Print", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("y", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("y += 1", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("End", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    return tokens

def tokens_2():
    tokens = deque()

    tokens.append(("Function", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("foo", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("Take", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("x, y", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("Do", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("If", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("x == 5", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("Then", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("Print", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("x", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("Else", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("Print", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("y", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("End", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("Return", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("x + y", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("End", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))


    tokens.append(("Call", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("foo", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("With", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("3, 5", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("y = 3", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("x = 1", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("x = ", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("Call", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("foo", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("With", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("x, y", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("Print", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("x", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    return tokens

def tokens_3():
    tokens = deque()

    tokens.append(("For", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("i", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("From", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("1", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("To", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("10", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("Do", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("Print", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("i", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    tokens.append(("End", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    return tokens

def test_parsing():
    
    prog = parse_code(tokens_2())

    return test_python_printing(prog)
    


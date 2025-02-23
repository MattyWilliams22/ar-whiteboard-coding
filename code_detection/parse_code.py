from collections import deque
import numpy as np
from typing import List, Tuple
from code_detection.markers.keywords import get_keyword
from code_detection.astnodes import *

def assemble_code(handwritten_text, bboxs, ids):
    text_map = []

    # Draw bounding boxes and text on the image
    for line in handwritten_text[0]:
        box, prediction = line  # Unpack the bounding box and text
        text, _ = prediction

        startX, startY = int(box[0][0]), int(box[0][1])
        endX, endY = int(box[2][0]), int(box[2][1])

        corners = np.array([[startX, startY], [endX, startY], [endX, endY], [startX, endY]])

        text_map.append((corners, text))

    for i in range(len(bboxs)):
        box = bboxs[i][0]

        corners = np.array([[box[0][0], box[0][1]], [box[1][0], box[1][1]], 
                            [box[2][0], box[2][1]], [box[3][0], box[3][1]]])
        
        text = get_keyword(ids[i][0])

        text_map.append((corners, text))
        
    code = ""
    for corners, text in text_map:
        code += f"{text}\n"

    return code

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
    # elif next == "Return":
    #     statement, tokens = parse_return(tokens, next_bounds)
    # elif next == "For":
    #     statement, tokens = parse_for(tokens, next_bounds)
    # elif next == "While":
    #     statement, tokens = parse_while(tokens, next_bounds)
    # elif next == "Call":
    #     statement, tokens = parse_call(tokens, next_bounds)
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
    
    args = []
    next, next_bounds = tokens.popleft()
    function_bounds = get_overall_bounds([function_bounds, next_bounds])
    if next == "Take":
        next, next_bounds = tokens.popleft()
        while next != "LineBreak":
            args.append(Argument(next_bounds, next))
            function_bounds = get_overall_bounds([function_bounds, next_bounds])
            next, next_bounds = tokens.popleft()

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

    while next != "LineBreak" and not len(tokens) == 0:
        token += " "
        token += next
        statement_bounds = get_overall_bounds([statement_bounds, next_bounds])
        next, next_bounds = tokens.popleft()

    if next != "LineBreak":
        raise Exception("Expected LineBreak")
    
    stmt = CustomStatement(statement_bounds, token)

    print("Parsed custom statement ", stmt.python_print())

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
            # case "Return":
            #     stmt, tokens = parse_return(tokens)
            #     program.add_statement(stmt)
            # case "For":
            #     stmt, tokens = parse_for(tokens)
            #     program.add_statement(stmt)
            # case "While":
            #     stmt, tokens = parse_while(tokens)
            #     program.add_statement(stmt)
            # case "Call":
            #     stmt, tokens = parse_call(tokens)
            #     program.add_statement(stmt)
            case _:
                stmt, tokens = parse_custom_statement(tokens, token, bounds)
                program.add_statement(stmt)
    
    return program

def test_python_printing(prog: Program):
    print(prog.python_print())

def test_parsing():
    tokens = deque()
    tokens.append(("Function", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("foo", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("Take", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("x", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("Do", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("If", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("x = 5", [(0,0), (0,1), (1,1), (1,0)]))
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
    tokens.append(("End", [(0,0), (0,1), (1,1), (1,0)]))
    tokens.append(("LineBreak", [(0,0), (0,1), (1,1), (1,0)]))

    prog = parse_code(tokens)

    test_python_printing(prog)
    


from collections import deque
import numpy as np
from typing import List, Tuple
from code_detection.astnodes import *

def get_overall_bounds(bounds: List[List[Tuple[int, int]]]):
    flat_bounds = []

    for box in bounds:
        # Ensure box is a list or tuple and has at least one valid point
        if isinstance(box, (list, tuple)) and len(box) > 0:
            for point in box:
                if (isinstance(point, (list, tuple)) and len(point) == 2 
                    and all(isinstance(coord, (int, float)) for coord in point)):
                    flat_bounds.append(point)

    if not flat_bounds:
        return [(0, 0), (0, 0), (0, 0), (0, 0)]

    xs, ys = zip(*flat_bounds)
    return [
        (min(xs), min(ys)), 
        (max(xs), min(ys)), 
        (max(xs), max(ys)), 
        (min(xs), max(ys))
    ]


def parse_statement(tokens: deque):
    try:
        next, next_bounds = tokens.popleft()
        if next == "PRINT":
            return parse_print(tokens, next_bounds)
        elif next == "IF":
            return parse_if_statement(tokens, next_bounds)
        elif next == "RETURN":
            return parse_return(tokens, next_bounds)
        elif next == "FOR":
            return parse_for(tokens, next_bounds)
        elif next == "While":
            return parse_while(tokens, next_bounds)
        elif next == "CALL":
            return parse_call(tokens, next_bounds)
        else:
            return parse_custom_statement(tokens, next, next_bounds)
    except Exception as e:
        return None, tokens, next_bounds, str(e)

def parse_function(tokens: deque, function_bounds: List[Tuple[int, int]]):
    try:
        name, name_bounds = tokens.popleft()
        function_bounds = get_overall_bounds([function_bounds, name_bounds])

        next, next_bounds = tokens.popleft()
        function_bounds = get_overall_bounds([function_bounds, next_bounds])
        if next != "LineBreak":
            raise Exception(f"Expected New Line after function name '{name}', instead found '{next}'")

        args = ""
        next, next_bounds = tokens.popleft()
        function_bounds = get_overall_bounds([function_bounds, next_bounds])
        if next == "TAKE":
            next, next_bounds = tokens.popleft()
            while next != "LineBreak":
                args += next + " "
                function_bounds = get_overall_bounds([function_bounds, next_bounds])
                next, next_bounds = tokens.popleft()

        args = [arg.strip() for arg in args.strip().split(",") if arg.strip()]

        next, next_bounds = tokens.popleft()
        function_bounds = get_overall_bounds([function_bounds, next_bounds])
        if next != "DO":
            raise Exception(f"Expected DO block, instead found '{next}'")

        statements = []
        next, next_bounds = tokens.popleft()
        function_bounds = get_overall_bounds([function_bounds, next_bounds])
        while next != "END":
            tokens.appendleft((next, next_bounds))
            stmt, tokens, stmt_bounds, err = parse_statement(tokens)
            if err:
                raise Exception(err)
            function_bounds = get_overall_bounds([function_bounds, stmt_bounds])
            statements.append(stmt)
            next, next_bounds = tokens.popleft()
        function_bounds = get_overall_bounds([function_bounds, next_bounds])

        next, next_bounds = tokens.popleft()
        if next != "LineBreak":
            raise Exception(f"Expected New Line after function body, instead found '{next}'")

        function = Function(function_bounds, Identifier(name_bounds, name), args, statements)
        print("Parsed function ", function.python_print())
        return function, tokens, function_bounds, None
    except Exception as e:
        return None, tokens, function_bounds, str(e)

# --- All parse_* functions below follow same pattern: returning (stmt, tokens, bounds, error_message) ---

def parse_print(tokens: deque, print_bounds):
    try:
        expr, expr_bounds = tokens.popleft()
        toString = False
        if expr == "STR":
            toString = True
            print_bounds = get_overall_bounds([print_bounds, expr_bounds])
            expr, expr_bounds = tokens.popleft()

        next, next_bounds = tokens.popleft()
        while next != "LineBreak":
            expr += " " + next
            expr_bounds = get_overall_bounds([expr_bounds, next_bounds])
            next, next_bounds = tokens.popleft()

        stmt = PrintStatement(get_overall_bounds([print_bounds, expr_bounds]), Expr(expr_bounds, expr), toString)
        print("Parsed print statement ", stmt.python_print())
        return stmt, tokens, stmt.bounds, None
    except Exception as e:
        return None, tokens, print_bounds, str(e)

def parse_return(tokens: deque, return_bounds):
    try:
        expr, expr_bounds = tokens.popleft()
        next, next_bounds = tokens.popleft()
        while next != "LineBreak" and len(tokens) > 0:
            expr += " " + next
            expr_bounds = get_overall_bounds([expr_bounds, next_bounds])
            next, next_bounds = tokens.popleft()

        stmt = ReturnStatement(get_overall_bounds([return_bounds, expr_bounds]), Expr(expr_bounds, expr))
        print("Parsed return statement ", stmt.python_print())
        return stmt, tokens, stmt.bounds, None
    except Exception as e:
        return None, tokens, return_bounds, str(e)

def parse_condition(tokens: deque):
    try:
        condition = ""
        next, next_bounds = tokens.popleft()
        bounds = next_bounds
        while next != "LineBreak":
            condition += " " + next if condition else next
            bounds = get_overall_bounds([bounds, next_bounds])
            next, next_bounds = tokens.popleft()
        return Expr(bounds, condition), tokens, bounds
    except Exception as e:
        return None, tokens, next_bounds

def parse_statement_block(tokens: deque, end_conditions):
    try:
        statements = []
        next, next_bounds = tokens.popleft()
        block_bounds = next_bounds
        while next not in end_conditions:
            tokens.appendleft((next, next_bounds))
            stmt, tokens, stmt_bounds, err = parse_statement(tokens)
            if err:
                raise Exception(err)
            statements.append(stmt)
            block_bounds = get_overall_bounds([block_bounds, stmt_bounds])
            next, next_bounds = tokens.popleft()
        return statements, block_bounds, next, next_bounds, None
    except Exception as e:
        return None, next_bounds, None, None, str(e)

def parse_if_statement(tokens: deque, if_bounds):
    try:
        conditions = []
        bodies = []
        next, next_bounds = tokens.popleft()
        if_bounds = get_overall_bounds([if_bounds, next_bounds])
        while next != "END":
            if next != "ELSE":
                tokens.appendleft((next, next_bounds))
                condition, tokens, cond_bounds = parse_condition(tokens)
                conditions.append(condition)
                if_bounds = get_overall_bounds([if_bounds, cond_bounds])
                next, next_bounds = tokens.popleft()
                if next != "THEN":
                    raise Exception(f"Expected THEN after condition, found '{next}'")

            body, body_bounds, next, next_bounds, err = parse_statement_block(tokens, ["END", "ELSE IF", "ELSE"])
            if err:
                raise Exception(err)
            bodies.append(body)
            if_bounds = get_overall_bounds([if_bounds, body_bounds])

        next, next_bounds = tokens.popleft()
        if next != "LineBreak":
            raise Exception(f"Expected New Line after if statement, found '{next}'")

        stmt = IfStatement(if_bounds, conditions, bodies)
        print("Parsed if statement ", stmt.python_print())
        return stmt, tokens, if_bounds, None
    except Exception as e:
        return None, tokens, if_bounds, str(e)

def parse_custom_statement(tokens: deque, token, statement_bounds):
    try:
        next, next_bounds = tokens.popleft()
        while next != "LineBreak" and next != "CALL" and len(tokens) > 0:
            token += " " + next
            statement_bounds = get_overall_bounds([statement_bounds, next_bounds])
            next, next_bounds = tokens.popleft()

        if next == "CALL":
            call_stmt, tokens, call_bounds, err = parse_call(tokens, statement_bounds)
            if err:
                raise Exception(err)
            statement_bounds = get_overall_bounds([statement_bounds, call_bounds])
            stmt = AssignCall(statement_bounds, token.strip(), call_stmt)
            print("Parsed assign call statement ", stmt.python_print())
            return stmt, tokens, statement_bounds, None
        elif next != "LineBreak":
            raise Exception(f"Expected New Line after statement, found '{next}'")

        stmt = CustomStatement(statement_bounds, token)
        print("Parsed custom statement ", stmt.python_print())
        return stmt, tokens, statement_bounds, None
    except Exception as e:
        return None, tokens, statement_bounds, str(e)

def parse_while(tokens: deque, while_bounds):
    try:
        condition, tokens, cond_bounds = parse_condition(tokens)
        while_bounds = get_overall_bounds([while_bounds, cond_bounds])
        next, next_bounds = tokens.popleft()
        if next != "DO":
            raise Exception(f"Expected DO after condition, found '{next}'")
        while_bounds = get_overall_bounds([while_bounds, next_bounds])
        body, body_bounds, next, next_bounds, err = parse_statement_block(tokens, ["END"])
        if err:
            raise Exception(err)
        next, next_bounds = tokens.popleft()
        if next != "LineBreak":
            raise Exception(f"Expected New Line after while statement, found '{next}'")

        stmt = WhileStatement(while_bounds, condition, body)
        print("Parsed while statement ", stmt.python_print())
        return stmt, tokens, while_bounds, None
    except Exception as e:
        return None, tokens, while_bounds, str(e)

def parse_for(tokens: deque, for_bounds):
    try:
        count, count_bounds = tokens.popleft()
        for_bounds = get_overall_bounds([for_bounds, count_bounds])
        next, next_bounds = tokens.popleft()
        if next != "FROM":
            raise Exception(f"Expected FROM, found '{next}'")

        lower_bound, lower_bounds = tokens.popleft()
        next, next_bounds = tokens.popleft()
        while next != "TO":
            lower_bound += " " + next
            lower_bounds = get_overall_bounds([lower_bounds, next_bounds])
            next, next_bounds = tokens.popleft()

        upper_bound, upper_bounds = tokens.popleft()
        next, next_bounds = tokens.popleft()
        while next != "LineBreak":
            upper_bound += " " + next
            upper_bounds = get_overall_bounds([upper_bounds, next_bounds])
            next, next_bounds = tokens.popleft()

        if next != "DO":
            raise Exception(f"Expected DO, found '{next}'")
        body, body_bounds, next, next_bounds, err = parse_statement_block(tokens, ["END"])
        if err:
            raise Exception(err)

        next, next_bounds = tokens.popleft()
        if next != "LineBreak":
            raise Exception(f"Expected New Line after for loop, found '{next}'")

        stmt = ForStatement(for_bounds, Identifier(count_bounds, count),
                            Expr(lower_bounds, lower_bound),
                            Expr(upper_bounds, upper_bound), body)
        print("Parsed for statement ", stmt.python_print())
        return stmt, tokens, stmt.bounds, None
    except Exception as e:
        return None, tokens, for_bounds, str(e)

def parse_call(tokens: deque, call_bounds):
    try:
        func_name, func_bounds = tokens.popleft()
        call_bounds = get_overall_bounds([call_bounds, func_bounds])
        next, next_bounds = tokens.popleft()
        call_bounds = get_overall_bounds([call_bounds, next_bounds])
        if next != "WITH" and next != "LineBreak":
            raise Exception(f"Expected WITH or New Line after function name, found '{next}'")
        if next == "LineBreak":
            stmt = Call(call_bounds, func_name, [])
            print("Parsed call statement ", stmt.python_print())
            return stmt, tokens, call_bounds, None

        args = ""
        next, next_bounds = tokens.popleft()
        while next != "LineBreak":
            args += next + " "
            call_bounds = get_overall_bounds([call_bounds, next_bounds])
            next, next_bounds = tokens.popleft()

        stmt = Call(call_bounds, func_name, [arg.strip() for arg in args.strip().split(",") if arg.strip()])
        print("Parsed call statement ", stmt.python_print())
        return stmt, tokens, call_bounds, None
    except Exception as e:
        return None, tokens, call_bounds, str(e)

def parse_code(tokens: deque):
    program = Program([(0,0), (0,0), (0,0), (0,0)], [], [])
    while len(tokens) > 0:
        try:
            token, bounds = tokens.popleft()
            if token == "FUNCTION":
                stmt, tokens, stmt_bounds, err = parse_function(tokens, bounds)
            elif token == "PRINT":
                stmt, tokens, stmt_bounds, err = parse_print(tokens, bounds)
            elif token == "IF":
                stmt, tokens, stmt_bounds, err = parse_if_statement(tokens, bounds)
            elif token == "RETURN":
                stmt, tokens, stmt_bounds, err = parse_return(tokens, bounds)
            elif token == "FOR":
                stmt, tokens, stmt_bounds, err = parse_for(tokens, bounds)
            elif token == "WHILE":
                stmt, tokens, stmt_bounds, err = parse_while(tokens, bounds)
            elif token == "CALL":
                stmt, tokens, stmt_bounds, err = parse_call(tokens, bounds)
            else:
                stmt, tokens, stmt_bounds, err = parse_custom_statement(tokens, token, bounds)

            if err:
                return program, err, stmt_bounds
            if isinstance(stmt, Function):
                program.add_function(stmt)
            else:
                program.add_statement(stmt)
        except Exception as e:
            return program, str(e), bounds
    return program, None, None

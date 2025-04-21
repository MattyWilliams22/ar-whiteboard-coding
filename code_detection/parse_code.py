from collections import deque
import numpy as np
from typing import List, Tuple
from code_detection.astnodes import *

def get_overall_bounds(bounds: List[List[Tuple[int, int]]]):
    min_x = min([min([x for x, y in box]) for box in bounds])
    min_y = min([min([y for x, y in box]) for box in bounds])
    max_x = max([max([x for x, y in box]) for box in bounds])
    max_y = max([max([y for x, y in box]) for box in bounds])

    return [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]

def parse_statement(tokens: deque):
    try:
        statement = None
        next, next_bounds = tokens.popleft()
        if next == "PRINT":
            statement, tokens, bounds = parse_print(tokens, next_bounds)
        elif next == "IF":
            statement, tokens, bounds = parse_if_statement(tokens, next_bounds)
        elif next == "RETURN":
            statement, tokens, bounds = parse_return(tokens, next_bounds)
        elif next == "FOR":
            statement, tokens, bounds = parse_for(tokens, next_bounds)
        elif next == "While":
            statement, tokens, bounds = parse_while(tokens, next_bounds)
        elif next == "CALL":
            statement, tokens, bounds = parse_call(tokens, next_bounds)
        else:
            statement, tokens, bounds = parse_custom_statement(tokens, next, next_bounds)
    
        return statement, tokens, bounds
    except Exception as e:
        return None, tokens, next_bounds

def parse_function(tokens: deque, function_bounds: List[Tuple[int, int]]):
    try:
        name, name_bounds = tokens.popleft()
        function_bounds = get_overall_bounds([function_bounds, name_bounds])

        next, next_bounds = tokens.popleft()
        function_bounds = get_overall_bounds([function_bounds, next_bounds])

        if next != "LineBreak":
            raise Exception("Expected New Line")
        
        args = ""
        next, next_bounds = tokens.popleft()
        function_bounds = get_overall_bounds([function_bounds, next_bounds])
        if next == "TAKE":
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
        if next != "DO":
            raise Exception("Expected DO")
        
        statements = []
        next, next_bounds = tokens.popleft()
        function_bounds = get_overall_bounds([function_bounds, next_bounds])
        while next != "END":
            tokens.appendleft((next, next_bounds))
            stmt, tokens, stmt_bounds = parse_statement(tokens)
            function_bounds = get_overall_bounds([function_bounds, stmt_bounds])
            statements.append(stmt)
            next, next_bounds = tokens.popleft()
        function_bounds = get_overall_bounds([function_bounds, next_bounds])

        next, next_bounds = tokens.popleft()
        if next != "LineBreak":
            raise Exception("Expected New Line")

        function = Function(function_bounds, Identifier(name_bounds, name), args, statements)
        print("Parsed function ", function.python_print())

        return function, tokens, function_bounds
    except Exception as e:
        return None, tokens, function_bounds

def parse_print(tokens: deque, print_bounds: List[Tuple[int, int]]):
    try:
        expr, expr_bounds = tokens.popleft()

        toString = False

        if expr == "STR":
            toString = True
            print_bounds = get_overall_bounds([print_bounds, expr_bounds])
            expr, expr_bounds = tokens.popleft()

        next, next_bounds = tokens.popleft()

        while next != "LineBreak":
            expr += " "
            expr += next
            expr_bounds = get_overall_bounds([expr_bounds, next_bounds])
            next, next_bounds = tokens.popleft()

        if next != "LineBreak":
            raise Exception("Expected New Line")

        expr = Expr(expr_bounds, expr)

        new_bounds = get_overall_bounds([print_bounds, expr_bounds])

        stmt = PrintStatement(new_bounds, expr, toString)

        print("Parsed print statement ", stmt.python_print())
        
        return stmt, tokens, new_bounds
    except Exception as e:
        return None, tokens, print_bounds

def parse_return(tokens: deque, return_bounds: List[Tuple[int, int]]):
    try:
        expr, expr_bounds = tokens.popleft()

        next, next_bounds = tokens.popleft()

        while next != "LineBreak" and len(tokens) > 0:
            expr += " "
            expr += next
            expr_bounds = get_overall_bounds([expr_bounds, next_bounds])
            next, next_bounds = tokens.popleft()

        if next != "LineBreak":
            raise Exception("Expected New Line")

        expr = Expr(expr_bounds, expr)

        new_bounds = get_overall_bounds([return_bounds, expr_bounds])

        stmt = ReturnStatement(new_bounds, expr)

        print("Parsed return statement ", stmt.python_print())
        
        return stmt, tokens, new_bounds
    except Exception as e:
        return None, tokens, return_bounds

def parse_condition(tokens: deque):
    try:
        condition = ""
        next, next_bounds = tokens.popleft()
        condition_bounds = next_bounds

        while next != "LineBreak":
            if condition != "":
                condition += " "
            condition += next
            condition_bounds = get_overall_bounds([condition_bounds, next_bounds])
            next, next_bounds = tokens.popleft()

        return Expr(condition_bounds, condition), tokens, condition_bounds
    except Exception as e:
        return None, tokens, next_bounds

def parse_statement_block(tokens: deque, end_conditions: List[str]):
    try:
        statements = []
        next, next_bounds = tokens.popleft()
        statement_bounds = next_bounds

        while next not in end_conditions:
            tokens.appendleft((next, next_bounds))
            stmt, tokens, stmt_bounds = parse_statement(tokens)
            statements.append(stmt)
            statement_bounds = get_overall_bounds([statement_bounds, stmt_bounds])
            next, next_bounds = tokens.popleft()

        return statements, statement_bounds, next, next_bounds, None
    except Exception as e:
        return None, next_bounds, None, None, str(e)

def parse_if_statement(tokens: deque, if_bounds: List[Tuple[int, int]]):
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
                    raise Exception("Expected THEN")

            body, body_bounds, next, next_bounds, err = parse_statement_block(tokens, ["END", "ELSE IF", "ELSE"])
            if err:
                raise Exception(err)
            bodies.append(body)
            if_bounds = get_overall_bounds([if_bounds, body_bounds])

        if_bounds = get_overall_bounds([if_bounds, next_bounds])
        next, next_bounds = tokens.popleft()
        if next != "LineBreak":
            raise Exception("Expected New Line")

        stmt = IfStatement(if_bounds, conditions, bodies)
        print("Parsed if statement ", stmt.python_print())

        return stmt, tokens, if_bounds
    except Exception as e:
        return None, tokens, if_bounds

def parse_custom_statement(tokens: deque, token: str, statement_bounds: List[Tuple[int, int]]):
    try:
        next, next_bounds = tokens.popleft()

        while next != "LineBreak" and next != "CALL" and len(tokens) > 0:
            token += " "
            token += next
            statement_bounds = get_overall_bounds([statement_bounds, next_bounds])
            next, next_bounds = tokens.popleft()

        if next == "CALL":
            call_stmt, tokens, call_bounds = parse_call(tokens, statement_bounds)
            statement_bounds = get_overall_bounds([statement_bounds, call_bounds])

            token = token.strip()
            stmt = AssignCall(statement_bounds, token, call_stmt)

            print("Parsed assign call statement ", stmt.python_print())
            return stmt, tokens, statement_bounds
        elif next != "LineBreak":
            raise Exception("Expected New Line")
        
        stmt = CustomStatement(statement_bounds, token)
        print("Parsed custom statement ", stmt.python_print())
        return stmt, tokens, statement_bounds
    except Exception as e:
        return None, tokens, statement_bounds

def parse_while(tokens: deque, while_bounds):
    try:
        condition, tokens, cond_bounds = parse_condition(tokens)
        while_bounds = get_overall_bounds([while_bounds, cond_bounds])

        next, next_bounds = tokens.popleft()
        if next != "DO":
            raise Exception("Expected DO")
        while_bounds = get_overall_bounds([while_bounds, next_bounds])

        body, body_bounds, next, next_bounds, err = parse_statement_block(tokens, ["END"])
        if err:
            raise Exception(err)
        while_bounds = get_overall_bounds([while_bounds, body_bounds])

        next, next_bounds = tokens.popleft()
        if next != "LineBreak":
            raise Exception("Expected New Line")

        stmt = WhileStatement(while_bounds, condition, body)
        print("Parsed while statement ", stmt.python_print())
        return stmt, tokens, while_bounds
    except Exception as e:
        return None, tokens, while_bounds

def parse_for(tokens: deque, for_bounds: List[Tuple[int, int]]):
    try:
        count, count_bounds = tokens.popleft()
        for_bounds = get_overall_bounds([for_bounds, count_bounds])

        next, next_bounds = tokens.popleft()
        if next != "FROM":
            raise Exception("Expected FROM")
        for_bounds = get_overall_bounds([for_bounds, next_bounds])

        lower_bound, lower_bound_bounds = tokens.popleft()
        next, next_bounds = tokens.popleft()
        while next != "TO":
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
        if next != "DO":
            raise Exception("Expected DO")
        for_bounds = get_overall_bounds([for_bounds, next_bounds])

        body, body_bounds, next, next_bounds, err = parse_statement_block(tokens, ["END"])
        if err:
            raise Exception(err)
        for_bounds = get_overall_bounds([for_bounds, body_bounds])

        if next != "END":
            raise Exception("Expected END")
        for_bounds = get_overall_bounds([for_bounds, next_bounds])
        
        next, next_bounds = tokens.popleft()
        if next != "LineBreak":
            raise Exception("Expected New Line")

        stmt = ForStatement(for_bounds, Identifier(count_bounds, count), 
                           Expr(lower_bound_bounds, lower_bound), 
                           Expr(upper_bound_bounds, upper_bound), body)
        print("Parsed for statement ", stmt.python_print())
        return stmt, tokens, for_bounds
    except Exception as e:
        return None, tokens, for_bounds

def parse_call(tokens: deque, call_bounds: List[Tuple[int, int]]):
    try:
        function_name, function_name_bounds = tokens.popleft()
        call_bounds = get_overall_bounds([call_bounds, function_name_bounds])

        next, next_bounds = tokens.popleft()
        if next != "WITH":
            raise Exception("Expected WITH")
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
        return stmt, tokens, call_bounds
    except Exception as e:
        return None, tokens, call_bounds

def parse_code(tokens: deque):
    program = Program([(0,0), (0,0), (0,0), (0,0)], [], [])
    error_message = None
    error_bounds = None

    while len(tokens) > 0:
        try:
            token, bounds = tokens.popleft()
            match token:
                case "FUNCTION":
                    function, tokens, function_bounds = parse_function(tokens, bounds)
                    if function is None:
                        error_message = "Error in function parsing"
                        error_bounds = function_bounds
                        break
                    program.add_function(function)
                case "PRINT":
                    stmt, tokens, stmt_bounds = parse_print(tokens, bounds)
                    if stmt is None:
                        error_message = "Error in print statement parsing"
                        error_bounds = stmt_bounds
                        break
                    program.add_statement(stmt)
                case "IF":
                    stmt, tokens, stmt_bounds = parse_if_statement(tokens, bounds)
                    if stmt is None:
                        error_message = "Error in if statement parsing"
                        error_bounds = stmt_bounds
                        break
                    program.add_statement(stmt)
                case "RETURN":
                    stmt, tokens, stmt_bounds = parse_return(tokens, bounds)
                    if stmt is None:
                        error_message = "Error in return statement parsing"
                        error_bounds = stmt_bounds
                        break
                    program.add_statement(stmt)
                case "FOR":
                    stmt, tokens, stmt_bounds = parse_for(tokens, bounds)
                    if stmt is None:
                        error_message = "Error in for loop parsing"
                        error_bounds = stmt_bounds
                        break
                    program.add_statement(stmt)
                case "WHILE":
                    stmt, tokens, stmt_bounds = parse_while(tokens, bounds)
                    if stmt is None:
                        error_message = "Error in while loop parsing"
                        error_bounds = stmt_bounds
                        break
                    program.add_statement(stmt)
                case "CALL":
                    stmt, tokens, stmt_bounds = parse_call(tokens, bounds)
                    if stmt is None:
                        error_message = "Error in function call parsing"
                        error_bounds = stmt_bounds
                        break
                    program.add_statement(stmt)
                case _:
                    stmt, tokens, stmt_bounds = parse_custom_statement(tokens, token, bounds)
                    if stmt is None:
                        error_message = "Error in custom statement parsing"
                        error_bounds = stmt_bounds
                        break
                    program.add_statement(stmt)
        except Exception as e:
            error_message = f"General error: {str(e)}"
            error_bounds = bounds if 'bounds' in locals() else [(0,0), (0,0), (0,0), (0,0)]
            break
    
    return program, error_message, error_bounds
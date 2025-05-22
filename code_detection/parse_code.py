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
                if (
                    isinstance(point, (list, tuple))
                    and len(point) == 2
                    and all(isinstance(coord, (int, float)) for coord in point)
                ):
                    flat_bounds.append(point)

    if not flat_bounds:
        return [(0, 0), (0, 0), (0, 0), (0, 0)]

    xs, ys = zip(*flat_bounds)
    return [
        (min(xs), min(ys)),
        (max(xs), min(ys)),
        (max(xs), max(ys)),
        (min(xs), max(ys)),
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
        elif next == "WHILE":
            return parse_while(tokens, next_bounds)
        elif next == "CALL":
            return parse_call(tokens, next_bounds)
        elif next == "IMPORT":
            return parse_import(tokens, next_bounds, "IMPORT")
        elif next == "FROM":
            return parse_import(tokens, next_bounds, "FROM")
        elif next == "TRY":
            return parse_try_statement(tokens, next_bounds)
        elif next == "COMMENT":
            return parse_comment(tokens, next_bounds)
        elif next == "INSERT":
            return parse_insert(tokens, next_bounds)
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
            raise Exception(
                f"Expected New Line after function name '{name}', instead found '{next}'"
            )

        args = ""
        next, next_bounds = tokens.popleft()
        function_bounds = get_overall_bounds([function_bounds, next_bounds])
        if next == "TAKE":
            next, next_bounds = tokens.popleft()
            while next != "LineBreak":
                args += next + " "
                function_bounds = get_overall_bounds([function_bounds, next_bounds])
                next, next_bounds = tokens.popleft()

        next, next_bounds = tokens.popleft()
        function_bounds = get_overall_bounds([function_bounds, next_bounds])
        if next != "DO":
            raise Exception(f"Expected DO block, instead found '{next}'")

        suite, tokens, suite_bounds, err = parse_suite(tokens, ["END"])
        function_bounds = get_overall_bounds([function_bounds, suite_bounds])
        if err:
            return None, tokens, function_bounds, str(err)

        next, next_bounds = tokens.popleft()
        if next != "END":
            raise Exception(f"Expected END after function body, instead found '{next}'")
        function_bounds = get_overall_bounds([function_bounds, next_bounds])
        next, next_bounds = tokens.popleft()
        if next != "LineBreak":
            raise Exception(
                f"Expected New Line after function body, instead found '{next}'"
            )

        function = Function(
            function_bounds, Identifier(name_bounds, name), args.strip(), suite
        )
        print("Parsed function ", function.python_print())
        return function, tokens, function_bounds, None
    except Exception as e:
        return None, tokens, function_bounds, str(e)


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

        stmt = PrintStatement(
            get_overall_bounds([print_bounds, expr_bounds]),
            Expr(expr_bounds, expr),
            toString,
        )
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

        stmt = ReturnStatement(
            get_overall_bounds([return_bounds, expr_bounds]), Expr(expr_bounds, expr)
        )
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
                if next != "ELSE IF":
                    tokens.appendleft((next, next_bounds))
                condition, tokens, cond_bounds = parse_condition(tokens)
                conditions.append(condition)
                if_bounds = get_overall_bounds([if_bounds, cond_bounds])
                next, next_bounds = tokens.popleft()
                if next != "THEN":
                    raise Exception(f"Expected THEN after condition, found '{next}'")

            body, body_bounds, next, next_bounds, err = parse_statement_block(
                tokens, ["END", "ELSE IF", "ELSE"]
            )
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
        while next != "LineBreak" and next != "CALL" and next != "CLASS" and len(tokens) > 0:
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
        if next == "CLASS":
            class_name, class_bounds = tokens.popleft()
            statement_bounds = get_overall_bounds([statement_bounds, class_bounds])
            next, next_bounds = tokens.popleft()
            if next not in ["LineBreak", "WITH"]:
                class_name += next
                class_bounds = get_overall_bounds([class_bounds, next_bounds])
                next, next_bounds = tokens.popleft()
            class_args = ""
            if next == "WITH":
                next, next_bounds = tokens.popleft()
                while next != "LineBreak":
                    class_args += next + " "
                    class_bounds = get_overall_bounds([class_bounds, next_bounds])
                    next, next_bounds = tokens.popleft()
            if next != "LineBreak":
                raise Exception(f"Expected New Line after class assignment, found '{next}'")
            statement_bounds = get_overall_bounds([statement_bounds, class_bounds])
            stmt = AssignClass(statement_bounds, token.strip(), class_name, class_args.strip())
            print("Parsed assign class statement ", stmt.python_print())
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
        body, body_bounds, next, next_bounds, err = parse_statement_block(
            tokens, ["END"]
        )
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

        next, next_bounds = tokens.popleft()
        if next != "DO":
            raise Exception(f"Expected DO, found '{next}'")
        for_bounds = get_overall_bounds([for_bounds, next_bounds])
        body, body_bounds, next, next_bounds, err = parse_statement_block(
            tokens, ["END"]
        )
        if err:
            raise Exception(err)

        next, next_bounds = tokens.popleft()
        if next != "LineBreak":
            raise Exception(f"Expected New Line after for loop, found '{next}'")

        stmt = ForStatement(
            for_bounds,
            Identifier(count_bounds, count),
            Expr(lower_bounds, lower_bound),
            Expr(upper_bounds, upper_bound),
            body,
        )
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
            raise Exception(
                f"Expected WITH or New Line after function name, found '{next}'"
            )
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

        stmt = Call(
            call_bounds,
            func_name,
            args.strip(),
        )
        print("Parsed call statement ", stmt.python_print())
        return stmt, tokens, call_bounds, None
    except Exception as e:
        return None, tokens, call_bounds, str(e)


def parse_import(tokens: deque, import_bounds, import_type):
    try:
        module = None
        alias = None

        if import_type == "FROM":
            module, module_bounds = tokens.popleft()
            import_bounds = get_overall_bounds([import_bounds, module_bounds])
            next, next_bounds = tokens.popleft()
            while next != "IMPORT":
                module += next
                import_bounds = get_overall_bounds([import_bounds, next_bounds])
                next, next_bounds = tokens.popleft()

        imported, imported_bounds = tokens.popleft()
        import_bounds = get_overall_bounds([import_bounds, imported_bounds])
        next, next_bounds = tokens.popleft()
        while next != "LineBreak" and next != "AS":
            imported += next
            import_bounds = get_overall_bounds([import_bounds, next_bounds])
            next, next_bounds = tokens.popleft()

        if next == "AS":
            import_bounds = get_overall_bounds([import_bounds, next_bounds])
            alias, alias_bounds = tokens.popleft()
            import_bounds = get_overall_bounds([import_bounds, alias_bounds])
            next, next_bounds = tokens.popleft()
            while next != "LineBreak":
                alias += next
                import_bounds = get_overall_bounds([import_bounds, next_bounds])
                next, next_bounds = tokens.popleft()

        stmt = ImportStatement(import_bounds, imported, module=module, alias=alias)
        print("Parsed import statement ", stmt.python_print())
        return stmt, tokens, import_bounds, None
    except Exception as e:
        return None, tokens, import_bounds, str(e)


def parse_try_statement(tokens: deque, try_bounds):
    try:
        exception_names = []
        catch_bodies = []
        else_body = None
        finally_body = None

        next, next_bounds = tokens.popleft()
        if next != "LineBreak":
            raise Exception(f"Expected New Line after TRY, found '{next}'")
        try_body, body_bounds, next, next_bounds, err = parse_statement_block(
            tokens, ["CATCH", "ELSE", "FINALLY", "END"]
        )
        if err:
            raise Exception(err)
        try_bounds = get_overall_bounds([try_bounds, body_bounds])

        while next == "CATCH":
            exception_name, exception_bounds = tokens.popleft()
            if exception_name == "LineBreak":
                exception_name = ""
            else:
                try_bounds = get_overall_bounds([try_bounds, exception_bounds])
                next, next_bounds = tokens.popleft()
                while next != "LineBreak":
                    exception_name += " " + next
                    try_bounds = get_overall_bounds([try_bounds, next_bounds])
                    next, next_bounds = tokens.popleft()

            catch_body, catch_body_bounds, next, next_bounds, err = (
                parse_statement_block(tokens, ["CATCH", "ELSE", "FINALLY", "END"])
            )
            if err:
                raise Exception(err)
            try_bounds = get_overall_bounds([try_bounds, catch_body_bounds])
            exception_names.append(exception_name)
            catch_bodies.append(catch_body)

        if next == "ELSE":
            next, next_bounds = tokens.popleft()
            if next != "LineBreak":
                raise Exception(f"Expected New Line after ELSE, found '{next}'")
            else_body, else_body_bounds, next, next_bounds, err = parse_statement_block(
                tokens, ["FINALLY", "END"]
            )
            if err:
                raise Exception(err)
            try_bounds = get_overall_bounds([try_bounds, else_body_bounds])

        if next == "FINALLY":
            next, next_bounds = tokens.popleft()
            if next != "LineBreak":
                raise Exception(f"Expected New Line after FINALLY, found '{next}'")
            finally_body, finally_body_bounds, next, next_bounds, err = (
                parse_statement_block(tokens, ["END"])
            )
            if err:
                raise Exception(err)
            try_bounds = get_overall_bounds([try_bounds, finally_body_bounds])

        if next != "END":
            raise Exception(f"Expected END after try statement, found '{next}'")
        next, next_bounds = tokens.popleft()
        if next != "LineBreak":
            raise Exception(f"Expected New Line after END, found '{next}'")

        stmt = TryStatement(
            try_bounds, try_body, exception_names, catch_bodies, else_body, finally_body
        )
        print("Parsed try statement ", stmt.python_print())
        return stmt, tokens, try_bounds, None
    except Exception as e:
        return None, tokens, try_bounds, str(e)
    
def parse_class(tokens: deque, class_bounds):
    try:
        name, name_bounds = tokens.popleft()
        class_bounds = get_overall_bounds([class_bounds, name_bounds])

        next, next_bounds = tokens.popleft()
        while next != "LineBreak":
            name += next
            class_bounds = get_overall_bounds([class_bounds, next_bounds])
            next, next_bounds = tokens.popleft()

        inherits = ""
        next, next_bounds = tokens.popleft()
        class_bounds = get_overall_bounds([class_bounds, next_bounds])
        if next == "FROM":
            next, next_bounds = tokens.popleft()
            while next != "LineBreak":
                inherits += next + " "
                class_bounds = get_overall_bounds([class_bounds, next_bounds])
                next, next_bounds = tokens.popleft()

        suite, tokens, suite_bounds, err = parse_suite(tokens, ["END"])
        if err:
            return None, tokens, class_bounds, str(err)
        class_bounds = get_overall_bounds([class_bounds, suite_bounds])

        next, next_bounds = tokens.popleft()
        if next != "END":
            raise Exception(f"Expected END after class body, found '{next}'")
        class_bounds = get_overall_bounds([class_bounds, next_bounds])
        next, next_bounds = tokens.popleft()
        if next != "LineBreak":
            raise Exception(
                f"Expected New Line after class body, instead found '{next}'"
            )

        class_node = ClassNode(
            class_bounds, Identifier(name_bounds, name), inherits.strip(), suite
        )
        print("Parsed class ", class_node.python_print())
        return class_node, tokens, class_bounds, None
    except Exception as e:
        return None, tokens, class_bounds, str(e)
    
def parse_comment(tokens: deque, comment_bounds):
    try:
        comment = ""
        next, next_bounds = tokens.popleft()
        comment_bounds = get_overall_bounds([comment_bounds, next_bounds])
        while next != "LineBreak":
            comment += next + " "
            comment_bounds = get_overall_bounds([comment_bounds, next_bounds])
            next, next_bounds = tokens.popleft()

        stmt = Comment(comment_bounds, comment.strip())
        print("Parsed comment ", stmt.python_print())
        return stmt, tokens, comment_bounds, None
    except Exception as e:
        return None, tokens, comment_bounds, str(e)
    
def parse_insert(tokens: deque, insert_bounds):
    try:
        insert = ""
        next, next_bounds = tokens.popleft()
        insert_bounds = get_overall_bounds([insert_bounds, next_bounds])
        while next != "LineBreak":
            insert += next + " "
            insert_bounds = get_overall_bounds([insert_bounds, next_bounds])
            next, next_bounds = tokens.popleft()

        stmt = Insert(insert_bounds, insert.strip())
        print("Parsed insert statement ", stmt.python_print())
        return stmt, tokens, insert_bounds, None
    except Exception as e:
        return None, tokens, insert_bounds, str(e)

    
def parse_suite(tokens: deque, end_conditions):
    try:
        out_of_tokens = not tokens
        nodes = []
        token, token_bounds = tokens.popleft()
        suite_bounds = token_bounds
        while token not in end_conditions and not out_of_tokens:
            if token == "FUNCTION":
                stmt, tokens, stmt_bounds, err = parse_function(tokens, token_bounds)
            elif token == "PRINT":
                stmt, tokens, stmt_bounds, err = parse_print(tokens, token_bounds)
            elif token == "IF":
                stmt, tokens, stmt_bounds, err = parse_if_statement(tokens, token_bounds)
            elif token == "RETURN":
                stmt, tokens, stmt_bounds, err = parse_return(tokens, token_bounds)
            elif token == "FOR":
                stmt, tokens, stmt_bounds, err = parse_for(tokens, token_bounds)
            elif token == "WHILE":
                stmt, tokens, stmt_bounds, err = parse_while(tokens, token_bounds)
            elif token == "CALL":
                stmt, tokens, stmt_bounds, err = parse_call(tokens, token_bounds)
            elif token == "IMPORT":
                stmt, tokens, stmt_bounds, err = parse_import(tokens, token_bounds, "IMPORT")
            elif token == "FROM":
                stmt, tokens, stmt_bounds, err = parse_import(tokens, token_bounds, "FROM")
            elif token == "TRY":
                stmt, tokens, stmt_bounds, err = parse_try_statement(tokens, token_bounds)
            elif token == "CLASS":
                stmt, tokens, stmt_bounds, err = parse_class(tokens, token_bounds)
            elif token == "COMMENT":
                stmt, tokens, stmt_bounds, err = parse_comment(tokens, token_bounds)
            elif token == "INSERT":
                stmt, tokens, stmt_bounds, err = parse_insert(tokens, token_bounds)
            else:
                stmt, tokens, stmt_bounds, err = parse_custom_statement(
                    tokens, token, token_bounds
                )
            
            if err is not None:
                return None, tokens, suite_bounds, str(err)
            suite_bounds = get_overall_bounds([suite_bounds, stmt_bounds])
            nodes.append(stmt)
            if tokens:
                token, bounds = tokens.popleft()
            else:
                out_of_tokens = True

        suite = Suite(suite_bounds, nodes)
        if not out_of_tokens:
            tokens.appendleft((token, bounds))
        print("Parsed suite ", suite.python_print())
        return suite, tokens, suite_bounds, None
    
    except Exception as e:
        return None, tokens, suite_bounds, str(e)


def parse_code(tokens: deque):
    try:
        suite, tokens, suite_bounds, err = parse_suite(tokens, [])
        if err:
            return None, err, suite_bounds
        if tokens:
            next, next_bounds = tokens.popleft()
            token_bounds = next_bounds
            while tokens:
                next, next_bounds = tokens.popleft()
                token_bounds = get_overall_bounds([token_bounds, next_bounds])
            return None, "Unexpected tokens after parsing program", token_bounds
        program = Program(suite_bounds, suite)
        print("Parsed program ", program.python_print())
        return program, None, None
    except Exception as e:
        return None, str(e), suite_bounds

from typing import Any, Tuple, Optional

from stimpl.expression import *
from stimpl.types import *
from stimpl.errors import *

"""
Interpreter State
"""


class State(object):
    def __init__(self, variable_name: str, variable_value: Expr, variable_type: Type, next_state: 'State') -> None:
        self.variable_name = variable_name
        self.value = (variable_value, variable_type)
        self.next_state = next_state

    def copy(self) -> 'State':
        variable_value, variable_type = self.value
        return State(self.variable_name, variable_value, variable_type, self.next_state)

    def set_value(self, variable_name, variable_value, variable_type):
        return State(variable_name, variable_value, variable_type, self)

    def get_value(self, variable_name) -> Any:
        # TODO Comment
        current_state = self
        while current_state:
            if current_state.variable_name == variable_name:
                return current_state.value
            current_state = current_state.next_state
        return None

    def __repr__(self) -> str:
        return f"{self.variable_name}: {self.value}, " + repr(self.next_state)


class EmptyState(State):
    def __init__(self):
        pass

    def copy(self) -> 'EmptyState':
        return EmptyState()

    def get_value(self, variable_name) -> None:
        return None

    def __repr__(self) -> str:
        return ""


"""
Main evaluation logic!
"""


def evaluate(expression: Expr, state: State) -> Tuple[Optional[Any], Type, State]:
    match expression:
        case Ren():
            return (None, Unit(), state)

        case IntLiteral(literal=l):
            return (l, Integer(), state)

        case FloatingPointLiteral(literal=l):
            return (l, FloatingPoint(), state)

        case StringLiteral(literal=l):
            return (l, String(), state)

        case BooleanLiteral(literal=l):
            return (l, Boolean(), state)

        case Print(to_print=to_print):
            printable_value, printable_type, new_state = evaluate(
                to_print, state)

            match printable_type:
                case Unit():
                    print("Unit")
                case _:
                    print(f"{printable_value}")

            return (printable_value, printable_type, new_state)

        case Sequence(exprs=exprs) | Program(exprs=exprs):
            print("SEQUENCING")
            print(exprs)
            if (exprs == None) or (len(exprs) == 0):
                return evaluate(Ren(), state)
            # TODO COMMENT I THINK THIS IS WRONG
            # I SAY THIS BECAUSE WE ARE EVALUATING WITHOUT PARSING
            last_value, last_type = None, Unit()
            for expr in exprs:
                last_value, last_type, state = evaluate(expr, state)
            return last_value, last_type, state

        case Variable(variable_name=variable_name):
            value = state.get_value(variable_name)
            if value == None:
                raise InterpSyntaxError(
                    f"Cannot read from {variable_name} before assignment.")
            variable_value, variable_type = value
            return (variable_value, variable_type, state)

        case Assign(variable=variable, value=value):

            value_result, value_type, new_state = evaluate(value, state)

            variable_from_state = new_state.get_value(variable.variable_name)
            _, variable_type = variable_from_state if variable_from_state else (
                None, None)

            if value_type != variable_type and variable_type != None:
                raise InterpTypeError(f"""Mismatched types for Assignment:
            Cannot assign {value_type} to {variable_type}""")

            new_state = new_state.set_value(
                variable.variable_name, value_result, value_type)
            return (value_result, value_type, new_state)

        case Add(left=left, right=right):
            result = 0
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Add:
            Cannot add {left_type} to {right_type}""")

            match left_type:
                case Integer() | String() | FloatingPoint():
                    result = left_result + right_result
                case _:
                    raise InterpTypeError(f"""Cannot add {left_type}s""")

            return (result, left_type, new_state)

        case Subtract(left=left, right=right):
            result = 0
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Add:
            Cannot add {left_type} to {right_type}""")

            match left_type:
                case Integer() | FloatingPoint():
                    result = left_result - right_result
                case _:
                    raise InterpTypeError(f"""Cannot add {left_type}s""")

            return (result, left_type, new_state)

        case Multiply(left=left, right=right):
            result = 0
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Add:
            Cannot add {left_type} to {right_type}""")

            match left_type:
                case Integer() | FloatingPoint():
                    result = left_result * right_result
                case _:
                    raise InterpTypeError(f"""Cannot add {left_type}s""")

            return (result, left_type, new_state)

        case Divide(left=left, right=right):
            result = 0
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Add:
            Cannot add {left_type} to {right_type}""")

            match left_type:
                case FloatingPoint():
                    result = left_result / right_result
                case Integer():
                    result = left_result // right_result
                case _:
                    raise InterpTypeError(f"""Cannot add {left_type}s""")

            return (result, left_type, new_state)

        case And(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for And:
            Cannot evaluate {left_type} and {right_type}""")
            match left_type:
                case Boolean():
                    result = left_value and right_value
                case _:
                    raise InterpTypeError(
                        "Cannot perform logical and on non-boolean operands.")

            return (result, left_type, new_state)

        case Or(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for And:
            Cannot evaluate {left_type} and {right_type}""")
            match left_type:
                case Boolean():
                    result = left_value or right_value
                case _:
                    raise InterpTypeError(
                        "Cannot perform logical and on non-boolean operands.")

            return (result, left_type, new_state)

        case Not(expr=expr):
            # TODO COMMENT
            # Opposite of this should be If, right?
            # BUT THE INTERFACE DOESN"T MATCH!!!
            expr_value, expr_type, new_state = evaluate(expr, state)
            if expr_type != Boolean():
                raise InterpTypeError("Cannot Not this Not.")
            return (not expr_value, Boolean(), new_state)

        case If(condition=condition, true=true, false=false):
            condition_value, condition_type, new_state = evaluate(condition, state)
            
            print(condition, true, false)
            if condition_type != Boolean():
                raise InterpTypeError("Cannot apply 'not' to non-boolean type.")
            if (condition_value):
                true_value, true_type, somestate = evaluate(true, state)
                return (true_value, true_type, new_state)
            else:
                false_value, false_type, somestate = evaluate(false, state)
                return (false_value, false_type, new_state)

        case Lt(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Lt:
            Cannot compare {left_type} and {right_type}""")

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value < right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform < on {left_type} type.")

            return (result, Boolean(), new_state)

        case Lte(left=left, right=right):
            """ TODO: Implement. """
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Lt:
            Cannot compare {left_type} and {right_type}""")
            if left_value == None and right_value == None:
                return (True, Boolean(), new_state)
            match left_type:
                case Integer() | String() | FloatingPoint():
                    result = left_value <= right_value
                case Boolean():
                    result = left_value == right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform <= on {left_type} type.")
            return (result, Boolean(), new_state)

        case Gt(left=left, right=right):
            """ TODO: Implement. """
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Lt:
            Cannot compare {left_type} and {right_type}""")

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value > right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform < on {left_type} type.")
            return (result, Boolean(), new_state)


        case Gte(left=left, right=right):
            """ TODO: Implement. """
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Lt:
            Cannot compare {left_type} and {right_type}""")
            if left_value == None and right_value == None:
                return (True, Boolean(), new_state)

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value >= right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform < on {left_type} type.")
            return (result, Boolean(), new_state)

        case Eq(left=left, right=right):
            """ TODO: Implement. """
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Lt:
            Cannot compare {left_type} and {right_type}""")
            if left_value == None and right_value == None:
                return (True, Boolean(), new_state)

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value == right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannnot perform < on {left_type} type.")
            return (result, Boolean(), new_state)

        case Ne(left=left, right=right):
            """ TODO: Implement. """
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Lt:
            Cannot compare {left_type} and {right_type}""")

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value != right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform < on {left_type} type.")
            return (result, Boolean(), new_state)

        case While(condition=condition, body=body):
            saved_off_state = state
            # TODO COMMENT, specifically why we just cheat this with true
            #(conditions are hard)
            iterations = 1
            while True:
                condition_value, condition_type, new_state = evaluate(condition, saved_off_state)
                if condition_type != Boolean():
                    raise InterpTypeError("Hey silly! Conditions which aren't boolean can't terminate!")
                if not condition_value:
                    break
                ignorable_value_1, ignorable_value_2, saved_off_state = evaluate(body,  saved_off_state)
                iterations = iterations + 1
                if iterations > 1000:
                    print("FUCK")
                    break
            return (None, Unit(), saved_off_state)

        case _:
            raise InterpSyntaxError("Unhandled!")
    pass


def run_stimpl(program, debug=False):
    state = EmptyState()
    program_value, program_type, program_state = evaluate(program, state)

    if debug:
        print(f"program: {program}")
        print(f"final_value: ({program_value}, {program_type})")
        print(f"final_state: {program_state}")

    return program_value, program_type, program_state

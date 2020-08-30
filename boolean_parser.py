import pyparsing
from itertools import islice
from dataclasses import dataclass
from typing import Dict, Optional, List, Union, Set
from pyparsing import (
    Group,
    Char,
    alphas,
    Forward,
    infixNotation,
    oneOf,
    opAssoc,
    Empty,
    ZeroOrMore,
)

def _eval_ast(ast, mapping: Dict[str, bool]) -> bool:
    # Base lookup variable case:
    if isinstance(ast, str):
        return mapping[ast[0]]

    # Singular expression -> recursively evaluate
    if len(ast) == 1 and isinstance(ast, List):
        return _eval_ast(ast[0], mapping)

    # Not operation (potential chaining):
    if "'" in ast:
        value = _eval_ast(ast[0], mapping)
        for i in islice(ast, 1, len(ast), 1):
            if i == "'":
                value = not value
            else:
                raise NotImplementedError("Degenerative case that should have been rejected by the parser. Please report this error.")
        return value

    # Case parentheses
    if ast[0] == "(" and ast[2] == ")":
        return _eval_ast(ast[1], mapping)

    # Case or:
    if ast[1] == "+":
        assert(len(ast) >= 3)
        assert(len(ast) % 2 == 1)
        for idx, node in zip(range(len(ast)), ast):
            if idx % 2 == 1:
                assert(node == "+")
            else:
                subresult = _eval_ast(node, mapping)
                if subresult:
                    return True
        return False

    # Case mult:
    if ast[1] == "*":
        assert(len(ast) >= 3)
        assert(len(ast) % 2 == 1)
        for idx, node in zip(range(len(ast)), ast):
            if idx % 2 == 1:
                assert(node == "*")
            else:
                subresult = _eval_ast(node, mapping)
                if not subresult:
                    return False
        return True

    # No operands found, so we multiply the subexpressions
    # Case Empty Mult:
    return all(_eval_ast(node, mapping) for node in ast)

def eval_ast(ast: List[Union[str, List]], mapping: Dict[str, bool]) -> bool:
    return _eval_ast(ast[0], mapping)


def find_leaf_nodes(ast) -> Set[str]:
    # Base lookup variable case:
    if isinstance(ast, str):
        return {ast}

    # Singular expression -> recursively evaluate
    if len(ast) == 1 and isinstance(ast, List):
        return find_leaf_nodes(ast[0])

    # Not operation (potential chaining):
    if "'" in ast:
        return find_leaf_nodes(ast[0])

    # Case Empty Mult:
    if len(ast) == 2:
        return find_leaf_nodes(ast[0]) | find_leaf_nodes(ast[1])

    # Case parentheses
    if ast[0] == "(" and ast[2] == ")":
        return find_leaf_nodes(ast[1])

    # Case or:
    if ast[1] == "+":
        return find_leaf_nodes(ast[0]) | find_leaf_nodes(ast[2])

    # Case mult:
    if ast[1] == "*":
        return find_leaf_nodes(ast[0]) and find_leaf_nodes(ast[2])

    # No operands found, so we multiply the subexpressions
    return set().union(*(find_leaf_nodes(node) for node in ast))



def create_ast(expression_str: str) -> List[Union[str, List]]:
    """Evaluates the given expression"""
    expression = Forward()
    operand = Group(Char(alphas) + ZeroOrMore("'")) | Group(Group("(" + expression + ")") + ZeroOrMore("'"))

    expression <<= infixNotation(
        operand,
        [(Empty(), 2, opAssoc.LEFT), ("*", 2, opAssoc.LEFT), ("+", 2, opAssoc.LEFT),],
    )
    return expression.parseString(expression_str, parseAll=True).asList()

def uses_all_nodes(ast, mapping: Dict[str, bool]) -> bool:
    actual_nodes = find_leaf_nodes(ast)
    expected_nodes = {key for key in mapping.keys()}

    if actual_nodes == expected_nodes:
        return True

    print(f"Boolean Expression is missing variables: {expected_nodes - actual_nodes}")
    print(f"Boolean Expression includes extra variables: {actual_nodes - expected_nodes}")

    return False



# print(create_ast("a"))
# print(create_ast("a'"))
# print(create_ast("a''"))
# print(create_ast("ab'"))
# print(create_ast("a'b"))
# print(create_ast("a'b"))
# print(create_ast("a'b'c'"))
# print(create_ast("a + b"))
# print(create_ast("(a)"))
# print(create_ast("(a + b)(b + a)"))
# print(create_ast("a + b * a"))
# from pprint import pprint
# pprint(create_ast("(a + b)'"))


# Test operands:
assert(eval_ast(create_ast("a"), {"a": True}) == True)
assert(eval_ast(create_ast("a"), {"a": False}) == False)

assert(eval_ast(create_ast("a'"), {"a": True}) == False)
assert(eval_ast(create_ast("a'"), {"a": False}) == True)

assert(eval_ast(create_ast("b''"), {"b": True}) == True)
assert(eval_ast(create_ast("b''"), {"b": False}) == False)

# Test Empty Mult:
assert(eval_ast(create_ast("ab"), {"a": True, "b": True}) == True)
assert(eval_ast(create_ast("ab"), {"a": False, "b": True}) == False)
assert(eval_ast(create_ast("ab"), {"a": True, "b": False}) == False)
assert(eval_ast(create_ast("ab"), {"a": False, "b": False}) == False)


assert(eval_ast(create_ast("a'b"), {"a": True, "b": True}) == False)
assert(eval_ast(create_ast("a'b"), {"a": False, "b": True}) == True)
assert(eval_ast(create_ast("a'b"), {"a": True, "b": False}) == False)
assert(eval_ast(create_ast("a'b"), {"a": False, "b": False}) == False)


assert(eval_ast(create_ast("a'b'"), {"a": True, "b": True}) == False)
assert(eval_ast(create_ast("a'b'"), {"a": False, "b": True}) == False)
assert(eval_ast(create_ast("a'b'"), {"a": True, "b": False}) == False)
assert(eval_ast(create_ast("a'b'"), {"a": False, "b": False}) == True)

assert(eval_ast(create_ast("a''b''"), {"a": True, "b": True}) == True)
assert(eval_ast(create_ast("a''b''"), {"a": False, "b": True}) == False)
assert(eval_ast(create_ast("a''b''"), {"a": True, "b": False}) == False)
assert(eval_ast(create_ast("a''b''"), {"a": False, "b": False}) == False)

# Test regular Mult:
assert(eval_ast(create_ast("a*b"), {"a": True, "b": True}) == True)
assert(eval_ast(create_ast("a*b"), {"a": False, "b": True}) == False)
assert(eval_ast(create_ast("a*b"), {"a": True, "b": False}) == False)
assert(eval_ast(create_ast("a*b"), {"a": False, "b": False}) == False)

assert(eval_ast(create_ast("a'*b"), {"a": True, "b": True}) == False)
assert(eval_ast(create_ast("a'*b"), {"a": False, "b": True}) == True)
assert(eval_ast(create_ast("a'*b"), {"a": True, "b": False}) == False)
assert(eval_ast(create_ast("a'*b"), {"a": False, "b": False}) == False)

# Test regular addition:
assert(eval_ast(create_ast("a+b"), {"a": True, "b": True}) == True)
assert(eval_ast(create_ast("a+b"), {"a": False, "b": True}) == True)
assert(eval_ast(create_ast("a+b"), {"a": True, "b": False}) == True)
assert(eval_ast(create_ast("a+b"), {"a": False, "b": False}) == False)

assert(eval_ast(create_ast("a+b'"), {"a": True, "b": True}) == True)
assert(eval_ast(create_ast("a+b'"), {"a": False, "b": True}) == False)
assert(eval_ast(create_ast("a+b'"), {"a": True, "b": False}) == True)
assert(eval_ast(create_ast("a+b'"), {"a": False, "b": False}) == True)


# Test parentheses:
assert(eval_ast(create_ast("(b)"), {"a": True, "b": True}) == True)
assert(eval_ast(create_ast("(b)"), {"a": True, "b": False}) == False)

assert(eval_ast(create_ast("(a+b)'"), {"a": True, "b": True}) == False)
assert(eval_ast(create_ast("(a)+b'"), {"a": False, "b": True}) == False)
assert(eval_ast(create_ast("a+(b)'"), {"a": True, "b": False}) == True)
assert(eval_ast(create_ast("a+b'"), {"a": False, "b": False}) == True)

# Random tests:
assert(eval_ast(create_ast("(ab) + a'*b"), {"a": False, "b": True}) == True)
assert(eval_ast(create_ast("(ab) + a'*b"), {"a": False, "b": False}) == False)
assert(eval_ast(create_ast("(ab) + a'*b"), {"a": True, "b": True}) == True)
assert(eval_ast(create_ast("(ab) + a'*b"), {"a": True, "b": False}) == False)

assert(eval_ast(create_ast("(ab)'"), {"a": True, "b": True}) == False)
assert(eval_ast(create_ast("(ab)'"), {"a": True, "b": False}) == True)
assert(eval_ast(create_ast("(ab)'"), {"a": False, "b": True}) == True)
assert(eval_ast(create_ast("(ab)'"), {"a": False, "b": False}) == True)


assert(eval_ast(create_ast("ab' + cd'"), {"a": True, "b": False, "c": False, "d": True}) == True)


assert(eval_ast(create_ast("a'b'c'"), {"a": False, "b": False, "c": False, "d": False}) == True)
assert(eval_ast(create_ast("a'b'c'd'"), {"a": False, "b": False, "c": False, "d": False}) == True)


assert(eval_ast(create_ast("abcd"), {"a": True, "b": True, "c": True, "d": True}) == True)


assert(find_leaf_nodes(create_ast("abcd")) == {"a", "b", "c", "d"})

assert(find_leaf_nodes(create_ast("a'b'c'd'")) == {"a", "b", "c", "d"})
assert(find_leaf_nodes(create_ast("(ab)'")) == {"a", "b"})


assert(find_leaf_nodes(create_ast("ab' + cd'")) == {"a", "b", "c", "d"})
assert(find_leaf_nodes(create_ast("a''b''")) == {"a", "b"})
assert(find_leaf_nodes(create_ast("(ab) + a'*b")) == {"a", "b"})


assert(uses_all_nodes(create_ast("a'b'c'd'"), {"a": False, "b": False, "c": False, "d": False}))
assert(uses_all_nodes(create_ast("a'b'e'"), {"a": False, "b": False, "c": False, "d": False}) == False)


print(create_ast("a'*b'*c'd'"))
print(create_ast("(a'b')(c'd')"))
print(create_ast("A'+B'+C'+D'"))
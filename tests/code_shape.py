"""The shape of a function, read from its syntax tree (R-004, D-544).

A test that guards how the code is built (a security check before an action, a callback instead of an inline rerun)
asks this module what the function calls, with which arguments and inside which condition. It never compares the
text of the code, so moving, renaming a variable or reformatting a file does not break the test.
"""

import ast
import inspect
import textwrap


# region Reading a function
def tree_of(function):
    """The syntax tree of one function."""
    return ast.parse(textwrap.dedent(inspect.getsource(function)))


def dotted(node):
    """`st.button` for the expression st.button, `is_author` for is_author; None for anything else."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


def calls(tree, name):
    """Every call to `name` (written as in the code, `st.rerun` or `is_author`) inside the tree."""
    return [node for node in ast.walk(tree) if isinstance(node, ast.Call) and dotted(node.func) == name]


def normal(expression):
    """An expression written the way the syntax tree writes it back, quotes included, to compare with keyword()."""
    return ast.unparse(ast.parse(expression, mode="eval").body)


def keyword(call, name):
    """The value of the argument `name=` of a call, as source text; None when the call does not pass it."""
    for item in call.keywords:
        if item.arg == name:
            return ast.unparse(item.value)
    return None


# endregion


# region Conditions
def guarded_by(tree, name, guard):
    """Whether every call to `name` sits inside an `if` whose condition calls `guard`."""
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    found = calls(tree, name)
    for call in found:
        node, safe = call, False
        while node in parents:
            node = parents[node]
            if isinstance(node, ast.If) and calls(node.test, guard):
                safe = True
                break
        if not safe:
            return False
    return bool(found)


def buttons_tested_inline(tree):
    """The labels of the buttons whose click is read in an `if st.button(...)`, instead of a callback."""
    labels = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            for call in calls(node.test, "st.button"):
                if call.args:
                    labels.append(ast.unparse(call.args[0]))
    return labels


def sets_true(tree, key):
    """Whether the function writes `st.session_state[key] = True`."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and node.value.value is True:
            for target in node.targets:
                if (
                    isinstance(target, ast.Subscript)
                    and dotted(target.value) == "st.session_state"
                    and ast.unparse(target.slice) == key
                ):
                    return True
    return False


# endregion

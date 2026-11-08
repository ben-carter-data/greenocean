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


def calls_named(tree, name):
    """Every call to the function `name`, with or without its module in front (`build_github_url` or
    `queries.build_github_url`)."""
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and (dotted(node.func) or "").split(".")[-1] == name
    ]


def uses(tree, name):
    """Every place the tree reads `name`, written as in the code: `overview.KPIS` or `RUN_WINDOW_CLOSING`."""
    return [node for node in ast.walk(tree) if isinstance(node, (ast.Name, ast.Attribute)) and dotted(node) == name]


def first(nodes):
    """The line of the first of the nodes, to compare the order of two steps of a function."""
    return min(node.lineno for node in nodes)


def arguments(call):
    """The positional arguments of a call, as source text."""
    return [ast.unparse(item) for item in call.args]


def literal(node):
    """The text of a string written as it is (a constant); None for anything computed."""
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def decorator(tree, name):
    """The decorator `name` (`st.dialog`, `st.fragment`) of the first function of the tree; None when it has not."""
    function = next(node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
    for item in function.decorator_list:
        if dotted(item.func if isinstance(item, ast.Call) else item) == name:
            return item
    return None


def defined(tree):
    """The names of the functions defined at the top level of a module's tree."""
    return {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def every_call(tree):
    """Every call of the tree."""
    return [node for node in ast.walk(tree) if isinstance(node, ast.Call)]


def imports(tree):
    """The name of every module the tree imports."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def texts(tree):
    """Every text the code writes, as the page or the database receives it: a string, or an f-string with `{}` where
    a value goes. The code around it does not count, so a comment or a name never matches."""
    parts = {id(part) for node in ast.walk(tree) if isinstance(node, ast.JoinedStr) for part in node.values}
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            found.append("".join(part.value if isinstance(part, ast.Constant) else "{}" for part in node.values))
        elif literal(node) is not None and id(node) not in parts:
            found.append(node.value)
    return found


def has_sequence(tree, items):
    """Whether a list or a tuple of the tree holds `items` one after the other, as a command does."""
    items = list(items)
    for node in ast.walk(tree):
        if isinstance(node, (ast.List, ast.Tuple)):
            values = [literal(item) for item in node.elts]
            if any(values[start : start + len(items)] == items for start in range(len(values))):
                return True
    return False


def deletes(tree):
    """Every `del` of the tree."""
    return [node for node in ast.walk(tree) if isinstance(node, ast.Delete)]


def conditions(tree):
    """The condition of every `if` of the tree, as source text."""
    return {ast.unparse(node.test) for node in ast.walk(tree) if isinstance(node, ast.If)}


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


# region Files
def file_tree(path):
    """The syntax tree of one Python file."""
    return ast.parse(path.read_text(encoding="utf-8"))


def folder_trees(folder):
    """The syntax trees of every Python file of a folder, in the order of their names."""
    return [file_tree(path) for path in sorted(folder.glob("*.py"))]


def string_literals(source):
    """Every string a module writes, whole (an f-string once, not each of its parts), with its source text: (line,
    text, node). D-557: the text is cut from lines split once per file; ast.get_source_segment splits the whole file
    again for each string, and on Python 3.11 in the CI that took four and a half minutes per test."""
    tree = ast.parse(source)
    lines = source.encode("utf-8").splitlines(keepends=True)
    parts = {id(part) for node in ast.walk(tree) if isinstance(node, ast.JoinedStr) for part in node.values}
    found = []
    for node in ast.walk(tree):
        is_text = isinstance(node, ast.JoinedStr) or (isinstance(node, ast.Constant) and isinstance(node.value, str))
        if not is_text or id(node) in parts:
            continue
        first, last = node.lineno - 1, node.end_lineno - 1
        if first == last:
            text = lines[first][node.col_offset : node.end_col_offset]
        else:
            text = (
                lines[first][node.col_offset :] + b"".join(lines[first + 1 : last]) + lines[last][: node.end_col_offset]
            )
        found.append((node.lineno, text.decode("utf-8"), node))
    return found


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

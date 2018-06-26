"""Models."""
from astroid.nodes import ClassDef, FunctionDef, Expr, Const, Attribute, Name

from pylint.interfaces import IAstroidChecker
from pylint.checkers.utils import check_messages
from pylint.checkers import BaseChecker

from pylint_unittest.__pkginfo__ import BASE_ID
from pylint_unittest.utils import node_is_subclass


MESSAGES = {
    'W%d01' % BASE_ID: (
        "Use %s instead of %s",
        'wrong-assert',
        "Used when a better unittest assertion than the one used is available"
    ),
    'W%d02' % BASE_ID: (
        "%s is deprecated, use %s instead",
        'deprecated-unittest-alias',
        "Used when the unittest method alias is deprecated"
    ),
}

DEPRECATED_ALIASES = {
    'failUnlessEqual': 'assertEqual',
    'assertEquals': 'assertEqual',
    'failIfEqual': 'assertNotEqual',
    'failUnless': 'assertTrue',
    '_assert': 'assertTrue',
    'failIf': 'assertFalse',
    'failUnlessRaises': 'assertRaises',
    'failUnlessAlmostEqual': 'assertAlmostEqual',
    'failIfAlmostEqual': 'assertNotAlmostEqual',
}


def is_method(node):
    return (isinstance(node, Attribute) and
            isinstance(node.expr, Name) and
            node.expr.name == 'self')


class UnittestAssertionsChecker(BaseChecker):
    """Unittest assertions checker."""
    __implements__ = IAstroidChecker

    name = 'unittest-assertions-checker'
    msgs = MESSAGES

    def __init__(self, linter=None):
        super(UnittestAssertionsChecker, self).__init__(linter)    
        self._is_testcase = False

    def visit_classdef(self, node):
        if node_is_subclass(node, 'unittest.case.TestCase', '.TestCase'):
            self._is_testcase = True

    def leave_classdef(self, node):
        self._is_testcase = False

    @check_messages('wrong-assert')
    def visit_call(self, node):
        if not self._is_testcase:
            return

        if not is_method(node.func):
            return

        funcname = node.func.attrname

        if funcname in ('assertEqual', 'assertIs'):
            for arg in node.args[:2]:
                if not isinstance(arg, Const):
                    continue
                if node.func.attrname == 'assertEqual' and arg.value is True:
                    self.add_message('wrong-assert', args=('assertTrue(x) or assertIs(x, True)', 'assertEqual(x, True)'), node=node)
                elif node.func.attrname == 'assertEqual' and arg.value is False:
                    self.add_message('wrong-assert', args=('assertFalse(x) or assertIs(x, False)', 'assertEqual(x, False)'), node=node)
                elif arg.value is None:
                    self.add_message('wrong-assert', args=('assertIsNone(x)', 'assertEqual(x, None)'), node=node)

        if funcname in DEPRECATED_ALIASES:
            new_name = DEPRECATED_ALIASES[funcname]
            self.add_message('deprecated-unittest-alias', args=(funcname, new_name), node=node)

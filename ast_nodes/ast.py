from automaton.automaton import State
from semantic.types import UnknownType
from visitor import visitor


class Node:
    def evaluate(self):
        raise NotImplementedError()


class AtomicNode(Node):
    def __init__(self, lex):
        self.lex = lex
        self.inferred_type = UnknownType()


class UnaryNode(Node):
    def __init__(self, node):
        self.node = node
        self.inferred_type = UnknownType()

    def evaluate(self):
        value = self.node.evaluate()
        return self.operate(value)

    @staticmethod
    def operate(value):
        raise NotImplementedError()


class BinaryNode(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.inferred_type = UnknownType()

    def evaluate(self):
        lvalue = self.left.evaluate()
        rvalue = self.right.evaluate()
        return self.operate(lvalue, rvalue)

    @staticmethod
    def operate(lvalue, rvalue):
        raise NotImplementedError()


class EpsilonNode(AtomicNode):
    def __init__(self):
        super().__init__('epsilon')

    def evaluate(self):
        return State(0, True)


def get_printer(atomic_node=AtomicNode, unary_node=UnaryNode, binary_node=BinaryNode, ):
    class PrintVisitor(object):
        @visitor.on('node')
        def visit(self, node, tabs):
            pass

        @visitor.when(UnaryNode)
        def visit(self, node, tabs=0):
            ans = '\t' * tabs + f'\\__<expr> {node.__class__.__name__}'
            child = self.visit(node.node, tabs + 1)
            return f'{ans}\n{child}'

        @visitor.when(BinaryNode)
        def visit(self, node, tabs=0):
            ans = '\t' * tabs + f'\\__<expr> {node.__class__.__name__} <expr>'
            left = self.visit(node.left, tabs + 1)
            right = self.visit(node.right, tabs + 1)
            return f'{ans}\n{left}\n{right}'

        @visitor.when(AtomicNode)
        def visit(self, node, tabs=0):
            return '\t' * tabs + f'\\__ {node.__class__.__name__}: {node.lex}'

    printer = PrintVisitor()
    return lambda ast: printer.visit(ast)

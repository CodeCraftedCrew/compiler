import string

from ast_nodes.ast import AtomicNode, BinaryNode, EpsilonNode, UnaryNode
from ast_nodes.tools import get_character_automaton
from automaton.automaton import State
from automaton.operations import closure, concat, join, repeat, positive_closure


class SymbolNode(AtomicNode):
    def evaluate(self):
        value = ''
        if isinstance(self.lex, str):
            value = self.lex
        elif isinstance(self.lex, OrdNode):
            value = chr(self.lex.evaluate())
        elif isinstance(self.lex, int):
            value = chr(self.lex)
        elif isinstance(self.lex, State):
            return self.lex
        return get_character_automaton(value)


class LetterNode(AtomicNode):

    def __init__(self):
        super().__init__('letter')

    def evaluate(self):
        return join([get_character_automaton(char) for char in string.ascii_letters])


class DigitNode(AtomicNode):

    def __init__(self):
        super().__init__('number')

    def evaluate(self):
        return join([get_character_automaton(digit) for digit in string.digits])


class AlphanumericNode(AtomicNode):

    def __init__(self):
        super().__init__('alphanum')

    def evaluate(self):
        return join([DigitNode().evaluate(), LetterNode().evaluate(), get_character_automaton('_')])


class QuestionNode(UnaryNode):

    def operate(self, value: State):
        return join([value, EpsilonNode().evaluate()])


class PlusNode(UnaryNode):

    def operate(self, value: State):
        return positive_closure(value)


class ClosureNode(UnaryNode):

    def operate(self, value: State):
        return closure(value)


class UnionNode(BinaryNode):

    def operate(self, left_value: State, right_value: State):
        return join([left_value, right_value])


class ConcatNode(BinaryNode):

    def operate(self, left_value: State, right_value: State):
        return concat([left_value, right_value])


class OrNode(UnaryNode):

    def operate(self, value):
        if not isinstance(value, list):
            value = [value]
        return join([get_character_automaton(chr(x)) for x in value])


class ComplementNode(UnaryNode):

    def operate(self, value):
        if not isinstance(value, list):
            value = [value]
        value = [x for x in string.printable if x not in list(map(chr, value))]
        return join([get_character_automaton(x) for x in value])


class AppendNode(BinaryNode):

    def operate(self, left_value, right_value):
        if not isinstance(left_value, list):
            left_value = [left_value]
        if not isinstance(right_value, list):
            right_value = [right_value]
        return left_value + right_value


class RepeatNode(BinaryNode):

    def operate(self, value: State, range_param):
        return repeat(value, range_param[0], range_param[1])


class RangeNode(BinaryNode):

    def operate(self, left_value: chr, right_value: chr):
        return [x for x in range(left_value, right_value + 1)]


class ParametersNode(BinaryNode):

    def operate(self, left_value: int, right_value: int):
        return [left_value, right_value]


class OrdNode(AtomicNode):

    def evaluate(self):
        return ord(self.lex)


class ConcatCharacterNode(BinaryNode):

    def operate(self, left_value, right_value):
        if not isinstance(left_value, list):
            left_value = [left_value]
        if not isinstance(right_value, list):
            right_value = [right_value]
        return left_value + right_value


class JoinCharacterNode(UnaryNode):

    def operate(self, value):
        if not isinstance(value, list):
            value = [value]
        return join(*[get_character_automaton(chr(x)) for x in value])
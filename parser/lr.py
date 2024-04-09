import dill
from abc import abstractmethod
from enum import Enum, auto
from pathlib import Path

from grammar.grammar import Grammar
from parser.parser import Parser


class Action(Enum):
    SHIFT = auto()
    REDUCE = auto()
    ACCEPTED = auto()
    ERROR = auto()


class LRParser(Parser):

    def __init__(self, g: Grammar, path=None):
        super().__init__()
        self.g = g
        self.augmented_grammar = g.augmented_grammar()

        self.action = {}
        self.go_to = {}

        cached = False
        if path:
            grammar_path = Path(f'{path}/grammar.pkl')
            if grammar_path.exists():
                cached_grammar = dill.load(open(grammar_path, 'rb'))

                if cached_grammar == str(g):

                    action_path = Path(f'{path}/action.pkl')
                    go_to_path = Path(f'{path}/go_to.pkl')

                    if action_path.exists() and go_to_path.exists():

                        action_index = dill.load(open(action_path, 'rb'))
                        go_to_index = dill.load(open(go_to_path, 'rb'))

                        self.load(action_index, go_to_index)

                        cached = True

        if not cached:
            self._build_parsing_table()
            if path and path.exists():
                dill.dump(str(g), open(f'{path}/grammar.pkl', 'wb'))

                action_index, go_to_index = self.reduce()
                dill.dump(action_index, open(f'{path}/action.pkl', 'wb'))
                dill.dump(go_to_index, open(f'{path}/go_to.pkl', 'wb'))

    @abstractmethod
    def _build_parsing_table(self):
        pass

    def __call__(self, w):
        stack = [0]
        cursor = 0
        output = []
        operations = []

        while True:
            state = stack[-1]
            lookahead = w[cursor]

            try:
                action, tag = self.action[state, lookahead.Name]
            except KeyError:
                print(f"Unexpected token {lookahead.Name}. Attempting panic-mode error recovery.")
                while True:
                    try:
                        for i in range(len(stack) - 2, -1, -2):
                            if stack[i].is_non_terminal and (state, stack[i].Name) in self.go_to:
                                a = stack[i]
                                break
                        else:
                            raise Exception("Panic-mode error recovery failed. Cannot proceed.")

                        while cursor < len(w) and (state, w[cursor].Name) not in self.action:
                            cursor += 1

                        if cursor == len(w):
                            raise Exception("Panic-mode error recovery failed. Cannot proceed.")

                        lookahead = a
                        action, tag = self.go_to[state, a.Name]

                        break

                    except Exception as e:
                        # Error during panic-mode recovery, raise and handle the original error
                        print(f"Panic-mode error recovery failed: {e}")
                        raise Exception(f"Original error: Unexpected token {lookahead.Name}")

            match action:
                case Action.SHIFT:
                    operations.append(action)
                    stack.append(lookahead)
                    stack.append(tag)
                    cursor += 1
                case Action.REDUCE:
                    operations.append(action)
                    for symbol in reversed(tag.Body._symbols):
                        stack.pop()
                        assert stack.pop() == symbol
                    output.append(tag)
                    goto = self.go_to[stack[-1], tag.Head.Name]
                    stack.append(tag.Head)
                    stack.append(goto[1])
                case Action.ACCEPTED:
                    stack.pop()
                    assert stack.pop() == self.g.startSymbol
                    assert len(stack) == 1 and stack[-1] == 0
                    return output, operations
                case _:
                    raise Exception()

    def reduce(self):

        action_index = {}

        for key, (action, tag) in self.action.items():

            if action == Action.REDUCE:
                action_index[key] = (action, self.g.Productions.index(tag))
            else:
                action_index[key] = (action, tag)

        go_to_index = {}

        for key, (action, tag) in self.go_to.items():
            go_to_index[key] = (action, tag)

        return action_index, go_to_index

    def load(self, action_index, go_to_index):

        for key, (action, tag) in action_index.items():

            if action == Action.REDUCE:
                self.action[key] = (action, self.g.Productions[tag])
            else:
                self.action[key] = (action, tag)

        for key, (action, tag) in go_to_index.items():
            self.go_to[key] = (action, tag)

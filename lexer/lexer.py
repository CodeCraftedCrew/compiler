import dill
from pathlib import Path

from automaton.automaton import State
from automaton.operations import get_final_states
from lexer.pattern import TokenPattern
from lexer.regex import get_regex_parser
from lexer.tools import Token, TokenType


class Lexer:
    def __init__(self, patterns: list[TokenPattern], eof, path=None):

        self.path = path
        cached = False
        if path:
            patterns_path = Path(f'{path}/patterns.pkl')
            if patterns_path.exists():
                cached_patterns = dill.load(open(patterns_path, 'rb'))

                if cached_patterns == [(pattern.regex, pattern.token_type.name) for pattern in patterns]:

                    automaton_path = Path(f'{path}/automaton.pkl')

                    if automaton_path.exists():
                        self.automaton = dill.load(open(automaton_path, 'rb'))
                        cached = True

        if not cached:
            self.regexs = self._build_regexs(patterns)
            self.automaton = self._build_automaton()

            if path and Path(path).exists():
                dill.dump([(pattern.regex, pattern.token_type.name) for pattern in patterns], open(f'{path}/patterns.pkl', 'wb'))
                dill.dump(self.automaton, open(f'{path}/automaton.pkl', 'wb'))

        self.eof = eof

    def _build_regexs(self, patterns):
        regexs = []
        regex_parser = get_regex_parser(path=self.path)
        for i, pattern in enumerate(patterns):
            automaton = pattern.automaton(regex_parser)

            final_states = get_final_states(automaton)

            for s in final_states:
                s.tag = (i, pattern.token_type)
            regexs.append(automaton)
        return regexs

    def _build_automaton(self):
        start = State('start')
        for state in self.regexs:
            start.add_epsilon_transition(state)
        return start.to_deterministic()

    def _walk(self, string):
        state = self.automaton
        final = state if state.final else None
        final_lex = lex = ''

        for symbol in string:
            if state.has_transition(symbol):
                state = state[symbol][0]
                lex += symbol
                if state.final:
                    final = state
                    final_lex = lex
            else:
                break

        return final, final_lex

    def _tokenize(self, text):

        line = column = 1
        i = 0
        while i < len(text):
            state, lex = self._walk(text[i:])

            if state is None:
                raise Exception(f"Unexpected character '{text[i]}' at {line}:{column}")

            i += len(lex)

            p = [s.tag for s in state.state if s.final]
            token_type = min(p)[1]

            if token_type == TokenType.LINEBREAK:
                line += 1
                column = 0
                continue

            if token_type == TokenType.SPACE:
                column += 1
                continue

            if token_type == TokenType.TAB:
                column += 4
                continue

            column += len(lex)

            yield lex, token_type, line, column

        yield '$', TokenType.EOF, line, column

    def __call__(self, text):
        return [Token(lex, ttype, line, column) for lex, ttype, line, column in self._tokenize(text)]

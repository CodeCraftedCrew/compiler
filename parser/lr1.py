from automaton.automaton import State, multiline_formatter
from grammar.grammar import Item
from grammar.tools import calculate_first_sets, ContainerSet, compress, expand
from parser.lr import LRParser, Action


class LR1Parser(LRParser):

    def _build_parsing_table(self):

        automaton = self.build_automaton()

        pending = [automaton]
        visited = [automaton]
        count = -1

        index_by_state = {}

        while pending:

            current = pending.pop()
            count += 1
            index_by_state[current] = count

            for transition in current.transitions.values():
                if transition[0] not in visited:
                    pending.append(transition[0])
                    visited.append(transition[0])

            for item in current.state:

                production = item.production

                if item.is_reduce_item:
                    if production.Head == self.augmented_grammar.startSymbol:
                        self._register(self.action, (count, self.g.EOF.Name), (Action.ACCEPTED, 0))
                    else:
                        for symbol in item.lookaheads:
                            self._register(self.action, (count, symbol.Name), (Action.REDUCE, production))
                else:
                    next_symbol = item.next_symbol

                    if next_symbol.is_terminal:
                        self._register(self.action, (count, next_symbol.Name),
                                       (Action.SHIFT, current.transitions[next_symbol.Name][0]))
                    else:
                        self._register(self.go_to, (count, next_symbol.Name),
                                       (Action.SHIFT, current.transitions[next_symbol.Name][0]))

        for key, (action, state) in self.action.items():
            if action == Action.SHIFT:
                self.action[key] = (action, index_by_state[state])

        for key, (action, state) in self.go_to.items():
            if action == Action.SHIFT:
                self.go_to[key] = (action, index_by_state[state])

    @staticmethod
    def _register(table, key, value):
        assert key not in table or table[key] == value, 'Shift-Reduce or Reduce-Reduce conflict!!!'
        table[key] = value

    def build_automaton(self):

        firsts = calculate_first_sets(self.augmented_grammar)
        firsts[self.augmented_grammar.EOF] = ContainerSet(*[self.augmented_grammar.EOF])

        assert len(self.augmented_grammar.startSymbol.productions) > 0

        i_0 = Item(self.augmented_grammar.startSymbol.productions[0], 0, lookaheads=[self.augmented_grammar.EOF])
        start = frozenset([i_0])

        closure = self.closure(start, firsts)
        automaton = State(frozenset(closure), True)

        pending = [start]
        visited = {start: automaton}

        while pending:
            current = pending.pop()
            current_state = visited[current]

            closure = self.closure(current, firsts)

            for symbol in self.augmented_grammar.terminals + self.augmented_grammar.nonTerminals:

                new_items = frozenset(self.goto(closure, symbol, just_kernel=True))
                if not new_items:
                    continue
                try:
                    next_state = visited[new_items]
                except KeyError:
                    pending.append(new_items)
                    next_state = State(frozenset(new_items.union(self.closure(new_items, firsts))),
                                       any(item.is_reduce_item for item in new_items))
                    visited[new_items] = next_state

                current_state.add_transition(symbol.Name, next_state)

        automaton.set_formatter(multiline_formatter)
        return automaton

    def closure(self, items, firsts):
        closure = ContainerSet(*items)

        changed = True
        while changed:
            new_items = ContainerSet()

            for item in closure:
                new_items.update(ContainerSet(*expand(item, firsts)))

            changed = closure.update(new_items)

        return compress(closure)

    def goto(self, items, symbol, firsts=None, just_kernel=False):
        assert just_kernel or firsts is not None, "`firsts` must be provided if `just_kernel=False`"

        items = frozenset(item.next_item() for item in items if item.next_symbol == symbol)
        return items if just_kernel else self.closure(items, firsts)

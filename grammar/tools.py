from grammar.grammar import Grammar, Epsilon, Item


class ContainerSet:
    def __init__(self, *values, contains_epsilon=False):
        self.set = set(values)
        self.contains_epsilon = contains_epsilon

    def add(self, value):
        n = len(self.set)
        self.set.add(value)
        return n != len(self.set)

    def extend(self, values):
        change = False
        for value in values:
            change |= self.add(value)
        return change

    def set_epsilon(self, value=True):
        last = self.contains_epsilon
        self.contains_epsilon = value
        return last != self.contains_epsilon

    def update(self, other):
        n = len(self.set)
        self.set.update(other.set)
        return n != len(self.set)

    def epsilon_update(self, other):
        return self.set_epsilon(self.contains_epsilon | other.contains_epsilon)

    def hard_update(self, other):
        return self.update(other) | self.epsilon_update(other)

    def find_match(self, match):
        for item in self.set:
            if item == match:
                return item
        return None

    def __len__(self):
        return len(self.set) + int(self.contains_epsilon)

    def __str__(self):
        return '%s-%s' % (str(self.set), self.contains_epsilon)

    def __repr__(self):
        return str(self)

    def __iter__(self):
        return iter(self.set)

    def __nonzero__(self):
        return len(self) > 0

    def __eq__(self, other):
        if isinstance(other, set):
            return self.set == other
        return (isinstance(other, ContainerSet) and self.set == other.set
                and self.contains_epsilon == other.contains_epsilon)


def calculate_first_sets(grammar: Grammar):
    """
    Calculate the FIRST sets for the given grammar.
    """

    first_sets = {}
    changes = True

    for terminal in grammar.terminals:
        first_sets[terminal] = ContainerSet(terminal)

    while changes:
        changes = False

        for production in grammar.Productions:
            production_firsts = calculate_firsts_for_production(first_sets, production.Body)

            first_sets[production.Head] = first_sets.get(production.Head, ContainerSet())
            changes |= first_sets[production.Head].hard_update(production_firsts)

    return first_sets


def calculate_firsts_for_production(firsts, body):
    firsts_body = ContainerSet()

    if isinstance(body, Epsilon):
        firsts_body.contains_epsilon = True
    else:
        for symbol in body._symbols:
            firsts_body.update(firsts.get(symbol, ContainerSet()))

            if not firsts.get(symbol, ContainerSet()).contains_epsilon:
                break
        else:
            firsts_body.contains_epsilon = True

    return firsts_body


def expand(item, firsts):
    next_symbol = item.next_symbol

    if next_symbol is None or not next_symbol.is_non_terminal:
        return []

    lookaheads = ContainerSet()

    for symbol in item.preview():
        first = calculate_firsts_for_production(firsts, symbol)

        if len(first) == 0:
            lookaheads.add(symbol[0].Grammar.EOF)

        lookaheads.update(first)

    assert not lookaheads.contains_epsilon

    return [Item(prod, 0, lookaheads) for prod in next_symbol.productions]


def compress(items):
    centers = {}

    for item in items:
        center = item.center()
        try:
            lookaheads = centers[center]
        except KeyError:
            centers[center] = lookaheads = set()

        lookaheads.update(item.lookaheads)

    return {Item(x.production, x.pos, set(lookahead)) for x, lookahead in centers.items()}

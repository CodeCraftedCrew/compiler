import json


class Symbol(object):

    def __init__(self, name: str, grammar):
        self.Name = name
        self.Grammar = grammar

    def __str__(self):
        return self.Name

    def __repr__(self):
        return repr(self.Name)

    def __add__(self, other):
        if isinstance(other, Symbol):
            return Sentence(self, other)

        raise TypeError(other)

    def __or__(self, other):

        if isinstance(other, Sentence):
            return SentenceList(Sentence(self), other)

        raise TypeError(other)

    @property
    def is_terminal(self):
        return False

    @property
    def is_non_terminal(self):
        return False

    @property
    def is_epsilon(self):
        return False

    def __len__(self):
        return 1


class NonTerminal(Symbol):

    def __init__(self, name, grammar):
        super().__init__(name, grammar)
        self.productions = []

    def __imod__(self, other):

        if isinstance(other, Sentence):
            p = Production(self, other)
            self.Grammar.add_production(p)
            return self

        if isinstance(other, tuple):
            assert len(other) > 1

            if len(other) == 2:
                other += (None,) * len(other[0])

            assert len(other) == len(
                other[0]) + 2, "Exactly one rule must be defined for each production symbol."

            if isinstance(other[0], Epsilon):
                p = AttributeProduction(self, Sentence(*[]), other[1:])
            elif isinstance(other[0], Sentence):
                p = AttributeProduction(self, other[0], other[1:])
            elif isinstance(other[0], Symbol):
                p = AttributeProduction(self, Sentence(other[0]), other[1:])
            else:
                raise Exception("")

            self.Grammar.add_production(p)
            return self

        if isinstance(other, Symbol):
            p = Production(self, Sentence(other))
            self.Grammar.add_production(p)
            return self

        if isinstance(other, SentenceList):

            for s in other:
                p = Production(self, s)
                self.Grammar.add_production(p)

            return self

        raise TypeError(other)

    @property
    def is_non_terminal(self):
        return True


class Terminal(Symbol):

    def __init__(self, name, grammar):
        super().__init__(name, grammar)

    @property
    def is_terminal(self):
        return True


class EOF(Terminal):

    def __init__(self, grammar):
        super().__init__('$', grammar)


class Sentence(object):

    def __init__(self, *args):
        self._symbols = tuple(x for x in args if not x.is_epsilon)
        self.hash = hash(self._symbols)

    def __len__(self):
        return len(self._symbols)

    def __add__(self, other):
        if isinstance(other, Symbol):
            return Sentence(*(self._symbols + (other,)))

        if isinstance(other, Sentence):
            return Sentence(*(self._symbols + other._symbols))

        raise TypeError(other)

    def __or__(self, other):
        if isinstance(other, Sentence):
            return SentenceList(self, other)

        if isinstance(other, Symbol):
            return SentenceList(self, Sentence(other))

        raise TypeError(other)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return ("%s " * len(self._symbols) % tuple(self._symbols)).strip()

    def __iter__(self):
        return iter(self._symbols)

    def __getitem__(self, index):
        return self._symbols[index]

    def __eq__(self, other):
        return self._symbols == other._symbols

    def __hash__(self):
        return self.hash


class SentenceList(object):

    def __init__(self, *args):
        self._sentences = list(args)

    def add(self, sentence: Sentence):
        if not isinstance(sentence, Sentence) or sentence is None:
            raise ValueError(sentence)

        self._sentences.append(sentence)

    def __iter__(self):
        return iter(self._sentences)

    def __or__(self, other):
        if isinstance(other, Sentence):
            self.add(other)
            return self

        if isinstance(other, Symbol):
            return self | Sentence(other)


class Epsilon(Terminal, Sentence):

    def __init__(self, grammar):
        super().__init__('epsilon', grammar)

    def __str__(self):
        return "ε"

    def __repr__(self):
        return 'epsilon'

    def __iter__(self):
        yield from ()

    def __len__(self):
        return 0

    def __add__(self, other):
        return other

    def __eq__(self, other):
        return isinstance(other, (Epsilon,))

    def __hash__(self):
        return hash("")

    @property
    def is_epsilon(self):
        return True


class Production(object):

    def __init__(self, non_terminal, sentence):
        self.Head = non_terminal
        self.Body = sentence

    def __str__(self):
        return '%s := %s' % (self.Head, self.Body)

    def __repr__(self):
        return '%s -> %s' % (self.Head, self.Body)

    def __iter__(self):
        yield self.Head
        yield self.Body

    def __eq__(self, other):
        return isinstance(other, Production) and self.Head == other.Head and self.Body == other.Body

    def __hash__(self):
        return hash((self.Head, self.Body))

    @property
    def is_epsilon(self):
        return self.Body.is_epsilon


class AttributeProduction(Production):

    def __init__(self, non_terminal, sentence, attributes):
        if not isinstance(sentence, Sentence) and isinstance(sentence, Symbol):
            sentence = Sentence(sentence)
        super(AttributeProduction, self).__init__(non_terminal, sentence)

        self.attributes = attributes

    def __str__(self):
        return '%s := %s' % (self.Head, self.Body)

    def __repr__(self):
        return '%s -> %s' % (self.Head, self.Body)

    def __iter__(self):
        yield self.Head
        yield self.Body

    @property
    def is_epsilon(self):
        return self.Body.is_epsilon

    def synthesize(self):
        pass


class Grammar:

    def __init__(self):

        self.Productions = []
        self.nonTerminals = []
        self.terminals = []
        self.startSymbol = None
        # production type
        self.pType = None
        self.Epsilon = Epsilon(self)
        self.EOF = EOF(self)

        self.symbolDict = {'$': self.EOF}

    def non_terminal(self, name, start_symbol=False):

        name = name.strip()
        if not name:
            raise Exception("Empty name")

        term = NonTerminal(name, self)

        if start_symbol:

            if self.startSymbol is None:
                self.startSymbol = term
            else:
                raise Exception("Cannot define more than one start symbol.")

        self.nonTerminals.append(term)
        self.symbolDict[name] = term
        return term

    def non_terminals(self, names):

        ans = tuple((self.non_terminal(x) for x in names.strip().split()))

        return ans

    def add_production(self, production):

        if len(self.Productions) == 0:
            self.pType = type(production)

        assert type(production) == self.pType, "The Productions most be of only 1 type."

        production.Head.productions.append(production)
        self.Productions.append(production)

    def terminal(self, name):

        name = name.strip()
        if not name:
            raise Exception("Empty name")

        term = Terminal(name, self)
        self.terminals.append(term)
        self.symbolDict[name] = term
        return term

    def set_terminals(self, names):

        ans = tuple((self.terminal(x) for x in names.strip().split()))

        return ans

    def __str__(self):

        mul = '%s, '

        ans = 'Non-Terminals:\n\t'

        non_terminals = mul * (len(self.nonTerminals) - 1) + '%s\n'

        ans += non_terminals % tuple(self.nonTerminals)

        ans += 'Terminals:\n\t'

        terminals = mul * (len(self.terminals) - 1) + '%s\n'

        ans += terminals % tuple(self.terminals)

        ans += 'Productions:\n\t'

        ans += str(self.Productions)

        return ans

    def __getitem__(self, name):
        try:
            return self.symbolDict[name]
        except KeyError:
            return None

    @property
    def to_json(self):

        productions = []

        for p in self.Productions:
            head = p.Head.Name

            body = []

            for s in p.Body:
                body.append(s.Name)

            productions.append({'Head': head, 'Body': body})

        d = {'NonTerminals': [symbol.Name for symbol in self.nonTerminals],
             'Terminals': [symbol.Name for symbol in self.terminals],
             'Productions': productions}
        return json.dumps(d)

    @staticmethod
    def from_json(data):
        data = json.loads(data)

        g = Grammar()
        dic = {'epsilon': g.Epsilon}

        for term in data['Terminals']:
            dic[term] = g.terminal(term)

        for noTerm in data['NonTerminals']:
            dic[noTerm] = g.non_terminal(noTerm)

        for p in data['Productions']:
            head = p['Head']
            dic[head] %= Sentence(*[dic[term] for term in p['Body']])

        return g

    def copy(self):
        g = Grammar()
        g.Productions = self.Productions.copy()
        g.nonTerminals = self.nonTerminals.copy()
        g.terminals = self.terminals.copy()
        g.pType = self.pType
        g.startSymbol = self.startSymbol
        g.Epsilon = self.Epsilon
        g.EOF = self.EOF
        g.symbolDict = self.symbolDict.copy()

        return g

    @property
    def is_augmented_grammar(self):
        augmented = 0
        for left, right in self.Productions:
            if self.startSymbol == left:
                augmented += 1
        if augmented <= 1:
            return True
        else:
            return False

    def augmented_grammar(self, force=False):
        if not self.is_augmented_grammar or force:

            g = self.copy()
            s = g.startSymbol
            g.startSymbol = None
            ss = g.non_terminal('S\'', True)
            if g.pType is AttributeProduction:
                ss %= s + g.Epsilon, lambda x: x
            else:
                ss %= s + g.Epsilon

            return g
        else:
            return self.copy()


class Item:

    def __init__(self, production, pos, lookaheads=None):
        if lookaheads is None:
            lookaheads = []
        self.production = production
        self.pos = pos
        self.lookaheads = frozenset(look for look in lookaheads)

    def __str__(self):
        s = str(self.production.Head) + " -> "
        if len(self.production.Body) > 0:
            for i, c in enumerate(self.production.Body):
                if i == self.pos:
                    s += "."
                s += str(self.production.Body[i])
            if self.pos == len(self.production.Body):
                s += "."
        else:
            s += "."
        s += ", " + str(self.lookaheads)[10:-1]
        return s

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return (
                (self.pos == other.pos) and
                (self.production == other.production) and
                (set(self.lookaheads) == set(other.lookaheads))
        )

    def __hash__(self):
        return hash((self.production, self.pos, self.lookaheads))

    @property
    def is_reduce_item(self):
        return len(self.production.Body) == self.pos

    @property
    def next_symbol(self):
        if self.pos < len(self.production.Body):
            return self.production.Body[self.pos]
        else:
            return None

    def next_item(self):
        if self.pos < len(self.production.Body):
            return Item(self.production, self.pos + 1, self.lookaheads)
        else:
            return None

    def preview(self, skip=1):
        unseen = self.production.Body[self.pos + skip:]
        return [Sentence(*(unseen + (lookahead,))) for lookahead in self.lookaheads]

    def center(self):
        return Item(self.production, self.pos)

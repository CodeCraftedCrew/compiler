from ast_nodes.ast import EpsilonNode
from ast_nodes.lexer import UnionNode, AlphanumericNode, LetterNode, DigitNode, ComplementNode, RangeNode, \
    ClosureNode, PlusNode, QuestionNode, ConcatNode, OrdNode, ConcatCharacterNode, JoinCharacterNode, SymbolNode
from evaluation.evaluation import evaluate_reverse_parse
from grammar.grammar import Grammar
from parser.lr import LRParser
from parser.lr1 import LR1Parser


def get_regex_parser(path=None):
    grammar = Grammar()

    (digit, letter, symbol, star, plus, question, open_brace, close_brace, open_parenthesis, close_parenthesis,
     hyphen, caret, alphanumeric, alpha, any_digit, open_bracket, close_bracket, pipe) = grammar.set_terminals(
        r"digit letter symbol * + ? { } ( ) - ^ \w \l \d [ ] |")

    e = grammar.Epsilon
    regular_expression = grammar.non_terminal("RE", True)

    expression, string, repeat, group, contains, element, repeated_item, r, character = (
        grammar.non_terminals("E S REP G C EL RI R CH"))

    regular_expression %= regular_expression + pipe + expression, lambda h, s: UnionNode(s[1], s[3])
    regular_expression %= expression, lambda h, s: s[1]
    regular_expression %= e, lambda h, s: EpsilonNode()

    expression %= expression + repeat, lambda h, s: ConcatNode(s[1], s[2])
    expression %= repeat, lambda h, s: s[1]

    repeat %= repeated_item + star, lambda h, s: ClosureNode(s[1])
    repeat %= repeated_item + plus, lambda h, s: PlusNode(s[1])
    repeat %= repeated_item + question, lambda h, s: QuestionNode(s[1])
    repeat %= repeated_item, lambda h, s: s[1]

    repeated_item %= open_parenthesis + regular_expression + close_parenthesis, lambda h, s: s[2]
    repeated_item %= open_bracket + contains + close_bracket, lambda h, s: s[2]
    repeated_item %= alphanumeric, lambda h, s: AlphanumericNode()
    repeated_item %= alpha, lambda h, s: LetterNode()
    repeated_item %= any_digit, lambda h, s: DigitNode()
    repeated_item %= character, lambda h, s: SymbolNode(s[1])

    contains %= caret + element, lambda h, s: ComplementNode(s[2])
    contains %= element, lambda h, s: JoinCharacterNode(s[1])

    element %= element + string, lambda h, s: ConcatCharacterNode(s[1], s[2])
    element %= string, lambda h, s: s[1]

    string %= character + hyphen + character, lambda h, s: RangeNode(s[1], s[3])
    string %= character, lambda h, s: s[1]

    character %= digit, lambda h, s: OrdNode(s[1])
    character %= letter, lambda h, s: OrdNode(s[1])
    character %= symbol, lambda h, s: OrdNode(s[1])

    return LR1Parser(grammar, path=path)


def parse(parser: LRParser, expression):
    tokens = tokenize(expression, parser.g.terminals)
    tokens.append(parser.g.EOF)

    parse_result, operations = parser(tokens)

    tokens = get_specific_characters(expression, tokens, parser.g.terminals)
    ast = evaluate_reverse_parse(parse_result, operations, tokens)

    evaluation = ast.evaluate()

    return evaluation.to_deterministic()


def get_specific_characters(expression, tokens, terminals):
    try:
        terminals_dict = {terminal.Name: terminal for terminal in terminals}
        characters = [terminals_dict.get("digit"), terminals_dict.get("letter"), terminals_dict.get("symbol")]

        expression = expression.replace('\\', '')
        result_tokens = []
        for i in range(len(tokens)):
            if tokens[i] in characters:
                result_tokens.append(expression[i])
            else:
                result_tokens.append(tokens[i])

        return result_tokens
    except Exception as e:
        print(e)


def tokenize(expression, terminals):
    terminals_dict = {terminal.Name: terminal for terminal in terminals}

    digit = terminals_dict.get("digit")
    letter = terminals_dict.get("letter")
    symbol = terminals_dict.get("symbol")

    mapped_tokens = []
    brackets = False
    escape = False

    for token in expression:
        found = False

        if not escape and token == '\\':
            escape = True
            continue

        if escape:
            token = '\\' + token
            escape = False

        if not brackets:
            if token == '[':
                brackets = True

            if token != '^' and token != '-':
                terminal = terminals_dict.get(token)
                if terminal is not None:
                    mapped_tokens.append(terminal)
                    found = True
        else:
            if token == ']':
                brackets = False

            terminal = terminals_dict.get(token)
            if terminal is not None:
                mapped_tokens.append(terminal)
                found = True

        if not found:

            if token.isdigit():
                mapped_tokens.append(digit)
            elif token.isalpha():
                mapped_tokens.append(letter)
            else:
                mapped_tokens.append(symbol)

    return mapped_tokens

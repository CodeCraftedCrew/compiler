from grammar.grammar import EOF, Terminal
from parser.lr import Action


def evaluate_reverse_parse(right_parse, operations, tokens):
    if not right_parse or not operations or not tokens:
        return

    right_parse = iter(right_parse)
    tokens = iter(tokens)
    stack = []
    for operation in operations:
        if operation == Action.SHIFT:
            token = next(tokens)
            stack.append(token.Name) if isinstance(token, Terminal) else stack.append(token)
        elif operation == Action.REDUCE:
            production = next(right_parse)
            head, body = production
            attributes = production.attributes
            assert all(rule is None for rule in attributes[1:]), 'There must be only synthesized attributes.'
            rule = attributes[0]

            if len(body):
                synthesized = [None] + stack[-len(body):]
                value = rule(None, synthesized)
                stack[-len(body):] = [value]
            else:
                stack.append(rule(None, None))
        else:
            raise Exception('Invalid action!!!')

    assert len(stack) == 1
    assert isinstance(next(tokens), EOF)
    return stack[0]

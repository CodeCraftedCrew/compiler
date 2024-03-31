from pandas import DataFrame

from parser.lr import Action


def encode_value(value, index_by_state):
    try:
        action, tag = value
        if action == Action.SHIFT:
            return 'S' + str(index_by_state[tag])
        elif action == Action.REDUCE:
            return repr(tag)
        elif action == Action.ACCEPTED:
            return 'OK'
        else:
            return value
    except TypeError as e:
        return value


def table_to_dataframe(table, index_by_state):
    d = {}
    for (state, symbol), value in table.items():
        value = encode_value(value, index_by_state)
        try:
            d[state][symbol] = value
        except KeyError:
            d[state] = {symbol: value}

    return DataFrame.from_dict(d, orient='index', dtype=str)
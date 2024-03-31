import copy

from automaton.automaton import State


def join(states):
    initial_state = State(frozenset())

    for state in states:
        initial_state.add_epsilon_transition(state)

    final_state = State(frozenset(), True)

    modify_final_state(states, [final_state])

    return initial_state


def concat(states):
    final_state = State(frozenset(), True)
    for i in range(len(states) - 1):
        modify_final_state([states[i]], [states[i + 1]])
    modify_final_state([states[-1]], [final_state])

    return states[0] if len(states) > 0 else final_state


def closure(state):
    start_state = State(frozenset())
    start_state.add_epsilon_transition(state)

    final_state = State(frozenset(), True)

    modify_final_state([state], [state, final_state])

    start_state.add_epsilon_transition(final_state)

    return start_state


def repeat(state, min_param, max_param):

    assert min_param <= max_param, "min_param must be less than max_param in repeat operation"

    if max_param == 0:
        states = [copy.deepcopy(state)] * (max_param - 1) + [state]
        new_state = concat(states)
        new_state.add_epsilon_transition(state)

        return new_state

    final_state = State(frozenset(), True)
    states = [copy.deepcopy(state) for _ in range(max_param)]

    for i in range(len(states) - 1):
        modify_final_state([states[i]], [states[i + 1]] if i < min_param - 1 else [states[i + 1], final_state])

    return states[0]


def modify_final_state(states, final_states):
    pending = states if isinstance(states, list) else [states]
    visited = set(states)

    while pending:
        current = pending.pop()
        for state in current.transitions.values():
            if state[0] not in visited:
                visited.add(state[0])
                pending.append(state[0])

        for state in current.epsilon_transitions:
            if state not in visited:
                visited.add(state)
                pending.append(state)

        if current.final:
            current.final = False
            for state in final_states:
                current.add_epsilon_transition(state)


def get_final_states(state):

    pending = [state]
    visited = {state}
    finals = []

    while pending:
        current = pending.pop()
        for _, state in current.transitions.items():
            if state[0] not in visited:
                visited.add(state[0])
                pending.append(state[0])

        if current.final:
            finals.append(current)

    return finals

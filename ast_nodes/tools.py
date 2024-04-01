from automaton.automaton import State


def get_character_automaton(char):
    automaton = State(frozenset())
    automaton.add_transition(char, State(frozenset(), True))

    return automaton

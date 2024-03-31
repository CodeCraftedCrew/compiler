from automaton.automaton import State


def get_character_automaton(char):
    automaton = State(0)
    automaton.add_transition(char, State(0, True))

    return automaton

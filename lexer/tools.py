from enum import Enum, auto


class Token:
    """
    Basic token class.

    Parameters
    ----------
    lex : str
        Token's lexeme.
    token_type : Enum
        Token's type.
    """

    def __init__(self, lex, token_type, line, column):
        self.lex = lex
        self.token_type = token_type
        self.line = line
        self.column = column

    def __str__(self):
        return f'{self.token_type}: {self.lex}'

    def __repr__(self):
        return str(self)

    @property
    def is_valid(self):
        return True


class UnknownToken(Token):
    def __init__(self, lex, line, column):
        Token.__init__(self, lex, None, line, column)

    def transform_to(self, token_type):
        return Token(self.lex, token_type, self.line, self.column)

    @property
    def is_valid(self):
        return False


class TokenType(Enum):
    # expressions

    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()

    # arithmetic operations

    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    POWER = auto()
    POWER_V2 = auto()
    MOD = auto()

    # symbols

    OPEN_BRACES = auto()
    CLOSE_BRACES = auto()
    SEMICOLON = auto()
    OPEN_PARENTHESIS = auto()
    CLOSE_PARENTHESIS = auto()
    ARROW = auto()
    COMMA = auto()
    ASSIGNMENT = auto()
    DESTRUCTIVE_ASSIGNMENT = auto()
    DOT = auto()
    COLON = auto()
    OPEN_BRACKETS = auto()
    CLOSE_BRACKETS = auto()
    DOUBLE_PIPE = auto()
    CONCAT = auto()
    DOUBLE_CONCAT = auto()
    LINEBREAK = auto()
    SPACE = auto()
    TAB = auto()
    ESCAPED_QUOTE = auto()

    # keywords

    FUNCTION = auto()
    LET = auto()
    IN = auto()
    IF = auto()
    ELIF = auto()
    ELSE = auto()
    TRUE = auto()
    FALSE = auto()
    WHILE = auto()
    FOR = auto()
    TYPE = auto()
    NEW = auto()
    INHERITS = auto()
    IS = auto()
    AS = auto()
    PROTOCOL = auto()
    EXTENDS = auto()

    # relational

    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    EQUAL = auto()
    DIFFERENT = auto()
    AND = auto()
    OR = auto()
    NOT = auto()

    EOF = auto()

    # End of File

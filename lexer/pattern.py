from lexer.regex import parse
from lexer.tools import TokenType


class TokenPattern:
    def __init__(self, regex: str, token_type: TokenType):
        self.regex = regex
        self.token_type = token_type
        self._automaton = None

    def automaton(self, regex_parser):
        if self._automaton is None:
            self._automaton = parse(regex_parser, self.regex)
        return self._automaton

    def __hash__(self):
        return hash((self.regex, self.token_type))

    def __eq__(self, other):
        return isinstance(other, TokenPattern) and self.regex == other.regex and self.token_type == other.token_type


def get_patterns():

    nonzero_digits = '|'.join(str(n) for n in range(1, 10))
    letters = '|'.join(chr(n) for n in range(ord('a'), ord('z') + 1)) + "|_|" + '|'.join(chr(n) for n in range(ord('A'), ord('Z') + 1))

    patterns = [
        TokenPattern(r"function", TokenType.FUNCTION),
        TokenPattern(r"let", TokenType.LET),
        TokenPattern(r"in", TokenType.IN),
        TokenPattern(r"if", TokenType.IF),
        TokenPattern(r"elif", TokenType.ELIF),
        TokenPattern(r"else", TokenType.ELSE),
        TokenPattern(r"true", TokenType.TRUE),
        TokenPattern(r"false", TokenType.FALSE),
        TokenPattern(r"while", TokenType.WHILE),
        TokenPattern(r"for", TokenType.FOR),
        TokenPattern(r"type", TokenType.TYPE),
        TokenPattern(r"new", TokenType.NEW),
        TokenPattern(r"inherits", TokenType.INHERITS),
        TokenPattern(r"is", TokenType.IS),
        TokenPattern(r"as", TokenType.AS),
        TokenPattern(r"protocol", TokenType.PROTOCOL),
        TokenPattern(r"extends", TokenType.EXTENDS),
        TokenPattern(f"(0|{nonzero_digits})+(.)?(0|{nonzero_digits})*", TokenType.NUMBER),
        TokenPattern("\"([^\"]*)\"", TokenType.STRING),
        TokenPattern(f"({letters})({letters}|0|_|{nonzero_digits})*", TokenType.IDENTIFIER),
        TokenPattern(r"\+", TokenType.PLUS),
        TokenPattern(r"\-", TokenType.MINUS),
        TokenPattern(r"\*", TokenType.MULTIPLY),
        TokenPattern(r"\/", TokenType.DIVIDE),
        TokenPattern(r"\^", TokenType.POWER),
        TokenPattern(r"\*\*", TokenType.POWER_V2),
        TokenPattern(r"%", TokenType.MOD),
        TokenPattern(r'\{', TokenType.OPEN_BRACES),
        TokenPattern(r'\}', TokenType.CLOSE_BRACES),
        TokenPattern(";", TokenType.SEMICOLON),
        TokenPattern(r"\(", TokenType.OPEN_PARENTHESIS),
        TokenPattern(r"\)", TokenType.CLOSE_PARENTHESIS),
        TokenPattern("=>", TokenType.ARROW),
        TokenPattern(",", TokenType.COMMA),
        TokenPattern("=", TokenType.ASSIGNMENT),
        TokenPattern(":=", TokenType.DESTRUCTIVE_ASSIGNMENT),
        TokenPattern(".", TokenType.DOT),
        TokenPattern(":", TokenType.COLON),
        TokenPattern(r"\[", TokenType.OPEN_BRACKETS),
        TokenPattern(r"\]", TokenType.CLOSE_BRACKETS),
        TokenPattern(r"\|\|", TokenType.DOUBLE_PIPE),
        TokenPattern("@", TokenType.CONCAT),
        TokenPattern("@@", TokenType.DOUBLE_CONCAT),
        TokenPattern("\n|\r|\n\r", TokenType.LINEBREAK),
        TokenPattern('  *', TokenType.SPACE),
        TokenPattern("\t", TokenType.TAB),
        TokenPattern(r">", TokenType.GREATER),
        TokenPattern(r">=", TokenType.GREATER_EQUAL),
        TokenPattern(r"<", TokenType.LESS),
        TokenPattern(r"<=", TokenType.LESS_EQUAL),
        TokenPattern(r"==", TokenType.EQUAL),
        TokenPattern(r"!=", TokenType.DIFFERENT),
        TokenPattern(r"&", TokenType.AND),
        TokenPattern(r"\|", TokenType.OR),
        TokenPattern(r"!", TokenType.NOT)
    ]

    return patterns

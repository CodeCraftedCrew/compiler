from sys import stderr


class Error:

    def __init__(self, program: str, error_out=stderr):
        self.program = program.splitlines()
        self.error_out = error_out
        self.errors = False

    def print_token(self, token):
        self.print_line(token.line)
        spaces = " " * (1 + len(str(token.line)) + token.column)
        pointer = "^" * len(token.lex)
        print(f"{spaces}{pointer}", file=self.error_out)

    def print_line(self, line: int):
        code_line = self.program[line - 1]
        print(f"{line}|{code_line}", file=self.error_out)

    def __call__(self, message: str, *, line: int = -1, token=None):
        self.errors = True
        print(message, file=self.error_out)
        if token:
            self.print_token(token)
        elif line != -1:
            self.print_line(line)
        else:
            print(message)
        exit(1)

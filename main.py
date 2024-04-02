import argparse
from pathlib import Path

from errors.error import Error
from evaluation.evaluation import evaluate_reverse_parse
from interpreter.interpreter import Interpreter
from language.hulk import get_hulk_grammar
from lexer.lexer import Lexer
from lexer.pattern import get_patterns
from parser.lr1 import LR1Parser
from semantic.type_builder import TypeBuilder
from semantic.type_checker import TypeChecker
from semantic.type_collector import TypeCollector
from semantic.type_inference import TypeInference


def handle_args():
    parser = argparse.ArgumentParser(description="Executes and evaluates programs written in the Hulk language.")
    parser.add_argument("path", type=str, help="Path to .hulk file")

    args = parser.parse_args()
    return args.path.split('=')[1]


def main():
    path = Path(handle_args())

    if not path.exists():
        print(f"File {path} not found")

    src_path = Path(__file__).parent

    grammar, mapping = get_hulk_grammar()

    lexer = Lexer(patterns=get_patterns(), eof=grammar.EOF,
                  path=src_path / 'cache/lexer')

    parser = LR1Parser(grammar, src_path / 'cache/hulk')

    for i in range(32, 45):
        with open(src_path / f'test/{i}.hulk', 'r') as f:
            program = f.read()

        try:
            tokens = lexer(program)
            terminals = [mapping.get(token.token_type) for token in tokens]

            parsed, operations = parser(terminals)

            ast = evaluate_reverse_parse(parsed, operations, tokens[:-1] + [grammar.EOF])

        except Exception as e:
            print(e)
            continue

        error = Error(program)

        collector = TypeCollector(error)
        collector.visit(ast)

        builder = TypeBuilder(collector.context, error)
        builder.visit(ast)

        inference = TypeInference(builder.context, error)
        inference.visit(ast)

        checker = TypeChecker(builder.context, error)
        checker.visit(ast)

        if error.errors:
            continue

        interpreter = Interpreter(checker.context, error)
        interpreter.visit(ast)

        print(f"finish {i}")


if __name__ == '__main__':
    main()

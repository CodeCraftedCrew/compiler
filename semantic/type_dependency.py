from semantic.types import UnknownType


class TypeDependency:

    def __init__(self, name, line, column, type, dependencies):

        self.name = name
        self.type = type or UnknownType()
        self.line = line
        self.column = column
        self.dependencies = set(dependencies)

    def add_dependency(self, dependency):
        self.dependencies.add(dependency)

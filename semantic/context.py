from collections import OrderedDict

from semantic.types import Type, Method, NumberType, StringType, BooleanType, ObjectType


class Context:
    def __init__(self):
        self.types = {"object": ObjectType(), "boolean": BooleanType(), "number": NumberType(), "string": StringType()}
        self.methods = []

    def create_type(self, name: str):
        if name in self.types:
            return False, f'Type with the same name ({name}) already in context.'
        typex = self.types[name] = Type(name)
        return True, typex

    def get_type(self, name: str):
        try:
            return True, self.types[name]
        except KeyError:
            return False, f'Type "{name}" is not defined.'

    def get_method(self, name: str):
        try:
            return True, next(method for method in self.methods if method.name == name)
        except StopIteration:
            return False, f'Method "{name}" is not defined.'

    def define_method(self, name: str, param_names: list, param_types: list, return_type):
        if name in (method.name for method in self.methods):
            return False, f'Method "{name}" already defined.'
        method = Method(name, param_names, param_types, return_type)
        self.methods.append(method)
        return True, method

    def update_method(self, name: str, param_types: list, return_type):
        try:
            method = next(method for method in self.methods if method.name == name)
            method.param_types = param_types
            method.return_type = return_type
        except StopIteration:
            return False, f'Method "{name}" is not defined.'

    def all_methods(self, clean=True):
        plain = OrderedDict()
        for method in self.methods:
            plain[method.name] = (method, self)
        return plain.values() if clean else plain

    def get_lowest_ancestor(self, types):
        pass  # Todo

    def __str__(self):
        return '{\n\t' + '\n\t'.join(y for x in self.types.values() for y in str(x).split('\n')) + '\n}'

    def __repr__(self):
        return str(self)

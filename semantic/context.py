from collections import OrderedDict

from semantic.types import Type, Method, NumberType, StringType, BooleanType, ObjectType, IterableType, UnknownType, \
    UndefinedType


class Context:
    def __init__(self):
        self.types = {"Object": ObjectType(), "Boolean": BooleanType(), "Number": NumberType(), "String": StringType()}
        self.methods = []

    def create_type(self, name: str, is_protocol=False):
        if name in self.types:
            return False, f'Type with the same name ({name}) already in context.'
        typex = self.types[name] = Type(name, is_protocol)
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

    def define_method(self, name: str, param_names: list, param_types: list, return_type, line):
        if name in (method.name for method in self.methods):
            return False, f'Method "{name}" already defined.'
        method = Method(name, param_names, param_types, return_type, line)
        self.methods.append(method)
        return True, method

    def update_method(self, name: str, param_types: list, return_type):
        try:
            method = next(method for method in self.methods if method.name == name)
            method.param_types = param_types
            method.return_type = return_type
        except StopIteration:
            return False, f'Method "{name}" is not defined.'

    def define_built_in_methods(self):

        global_functions = {
            "sqrt": (["value"], [NumberType()], NumberType()),
            "sin": (["angle"], [NumberType()], NumberType()),
            "cos": (["angle"], [NumberType()], NumberType()),
            "log": (["base", "value"], [NumberType(), NumberType()], NumberType()),
            "exp": (["value"], [NumberType()], NumberType()),
            "rand": ([], [], NumberType()),
            "print": (["message"], [StringType()], StringType()),
            "range": (["min", "max"], [NumberType(), NumberType()], IterableType(NumberType()))
        }

        for func_name, (param_names, param_types, return_type) in global_functions.items():
            self.define_method(func_name, param_names, param_types, return_type, -1)

    def all_methods(self, clean=True):
        plain = OrderedDict()
        for method in self.methods:
            plain[method.name] = (method, self)
        return plain.values() if clean else plain

    def get_lowest_ancestor(self, type_a, type_b):

        if type_a in [UnknownType(), UndefinedType()]:
            return type_b

        if type_b in [UnknownType(), UndefinedType()]:
            return type_a

        while type_a.depth > type_b.depth:
            type_a = type_a.parent

        while type_b.depth > type_a.depth:
            type_b = type_b.parent

        while type_b != type_a:
            type_a = type_a.parent
            type_b = type_b.parent

        return type_a

    def check_inheritance(self, child: Type, parent: Type, args, line):

        errors = []

        if len(child.params) > 0:

            if len(args) != len(parent.params):
                errors.append((f"{parent.name} expects {len(parent.params)} arguments, "
                               f"got {len(args)}", line))

            parent_args = list(parent.params.values())

            for i in range(len(parent_args)):
                if not parent_args[i] or parent_args[i] == UnknownType():
                    parent_args[i] = parent.params_inferred_type[i]

            for i in range(len(args)):
                if not args[i].conforms_to(parent_args[i]):
                    errors.append(
                        (f"Argument type mismatch, on {parent.name} got {args[i]} "
                         f"expected {parent_args[i]}", line))

        parent_methods = parent.all_methods(False)
        child_methods = child.all_methods(False)

        for name, (method, _) in child_methods.items():

            if name in parent_methods:

                base_method = parent_methods[name][0]

                if len(base_method.param_types) != len(method.param_types):
                    errors.append((f"{name} expects {len(base_method.param_types)} parameters, "
                                   f"got {len(method.param_types)}", method.line))

                for i in range(len(base_method.param_types)):

                    if method.param_types[i] != base_method.param_types[i]:
                        errors.append(
                            (f"Parameter type mismatch, on {method.param_names[i].name} got {method.param_types[i].name} "
                             f"expected {base_method.param_types[i].name}", method.line))

                if method.return_type != base_method.return_type:
                    errors.append((f"Return type mismatch, on {name} got {method.return_type} "
                                   f"expected {base_method.return_type}", method.line))

        return errors

    def __str__(self):
        return '{\n\t' + '\n\t'.join(y for x in self.types.values() for y in str(x).split('\n')) + '\n}'

    def __repr__(self):
        return str(self)

import itertools as itl

from semantic.types import UnknownType, NumberType, StringType, IterableType


class VariableInfo:
    def __init__(self, name, declared_type=None, inferred_type=None, value=None):
        self.name = name
        self.value = value
        self.type = declared_type
        self.inferred_type = inferred_type or UnknownType()


class FunctionInfo:
    def __init__(self, name, params, return_type=None):
        self.name = name
        self.params = params
        self.type = return_type
        self.inferred_type = UnknownType()


class Scope:
    def __init__(self, parent=None):
        self.local_vars = []
        self.local_funcs = []
        self.parent = parent
        self.children = []
        self.var_index_at_parent = 0 if parent is None else len(parent.local_vars)
        self.func_index_at_parent = 0 if parent is None else len(parent.local_funcs)

    def add_builtin(self):
        global_variables = {
            "PI": NumberType(),
            "E": NumberType()
        }

        for name, declared_type in global_variables.items():
            self.define_variable(name, declared_type)

    def create_child_scope(self):
        child_scope = Scope(self)
        self.children.append(child_scope)
        return child_scope

    def define_variable(self, variable_name, declared_type=None, inferred_type=None, value=None):
        self.local_vars.append(VariableInfo(variable_name, declared_type, inferred_type, value))

    def update_variable_inferred_type(self, variable_name, inferred_type):
        variable = self.find_variable(variable_name)

        if variable is None:
            return False, f"Variable {variable_name} is not defined in the current scope."

        if variable.type:
            return True

        variable.inferred_type = inferred_type

    def define_function(self, function_name, params, return_type=None):
        self.local_funcs.append(FunctionInfo(function_name, params, return_type))
        
    def update_function_inferred_type(self, function_name, inferred_type):
        function = self.find_function(function_name)

        if function is None:
            return False, f"Function {function_name} is not defined in the current scope."

        if function.type:
            return True

        function.inferred_type = inferred_type

    def find_function(self, function_name, index=None):
        locals = self.local_funcs if index is None else itl.islice(self.local_funcs, index)
        try:
            return next(x for x in locals if x.name == function_name)
        except StopIteration:
            return self.parent.find_function(function_name, self.func_index_at_parent) if self.parent else None

    def find_variable(self, variable_name, index=None):
        locals = self.local_vars if index is None else itl.islice(self.local_vars, index)
        try:
            return next(x for x in locals if x.name == variable_name)
        except StopIteration:
            return self.parent.find_variable(variable_name, self.var_index_at_parent) if self.parent else None

    def is_var_defined(self, variable_name):
        return self.find_variable(variable_name) is not None

    def is_local_var(self, variable_name):
        return any(True for x in self.local_vars if x.name == variable_name)

    def is_local_func(self, function_name):
        return any(True for x in self.local_funcs if x.name == function_name)

    def is_func_defined(self, function_name):
        return self.find_function(function_name)

    def get_local_function_info(self, function_name):
        for func in self.local_funcs:
            if func.name == function_name:
                return func
        return None

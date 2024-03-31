import itertools as itl


class VariableInfo:
    def __init__(self, name, declared_type=None, inferred_types=None):
        self.name = name
        self.type = declared_type
        self.inferred_types = set(inferred_types or [])


class FunctionInfo:
    def __init__(self, name, params, return_type=None):
        self.name = name
        self.params = params
        self.type = return_type


class Scope:
    def __init__(self, parent=None):
        self.local_vars = []
        self.local_funcs = []
        self.parent = parent
        self.children = []
        self.var_index_at_parent = 0 if parent is None else len(parent.local_vars)
        self.func_index_at_parent = 0 if parent is None else len(parent.local_funcs)

    def create_child_scope(self):
        child_scope = Scope(self)
        self.children.append(child_scope)
        return child_scope

    def define_variable(self, vname, declared_type=None, inferred_type=None):
        self.local_vars.append(VariableInfo(vname, declared_type, inferred_type))

    def update_inferred_types(self, vname, inferred_type):
        variable = self.find_variable(vname)

        if variable is None:
            return False, f"Variable {vname} is not defined in the current scope."

        if variable.type:
            return True

        variable.inferred_types = variable.inferred_types.add(inferred_type)
        return True

    def define_function(self, fname, params, return_type=None):
        self.local_funcs.append(FunctionInfo(fname, params, return_type))

    def find_function(self, fname, index=None):
        locals = self.local_funcs if index is None else itl.islice(self.local_funcs, index)
        try:
            return next(x for x in locals if x.name == fname)
        except StopIteration:
            return self.parent.find_function(fname, self.func_index_at_parent) if self.parent is not None else None

    def find_variable(self, vname, index=None):
        locals = self.local_vars if index is None else itl.islice(self.local_vars, index)
        try:
            return next(x for x in locals if x.name == vname)
        except StopIteration:
            return self.parent.find_variable(vname, self.var_index_at_parent) if self.parent is None else None

    def is_var_defined(self, vname):
        return self.find_variable(vname) is not None

    def is_local_var(self, vname):
        return any(True for x in self.local_vars if x.name == vname)

    def is_local_func(self, fname):
        return any(True for x in self.local_funcs if x.name == fname)

    def is_func_defined(self, fname):
        return self.find_function(fname)

    def get_local_function_info(self, fname):
        for func in self.local_funcs:
            if func.name == fname:
                return func
        return None

from collections import OrderedDict


class Type:
    def __init__(self, name: str, is_protocol=False):
        self.name = name
        self.params = {}
        self.is_protocol = is_protocol
        self.attributes = []
        self.methods = []
        self.parent = None

    def set_parent(self, parent):
        if isinstance(parent, StringType) or isinstance(parent, NumberType) or isinstance(parent, BooleanType):
            return False, f"{self.name} can not inherit from {parent}."
        if self.is_protocol:
            self.parent = self.parent.append(parent) if self.parent else [parent]
            return True, None
        if self.parent is not None:
            return False, f'Parent type is already set for {self.name}.'
        self.parent = parent
        return True, None

    def get_attribute(self, name: str):
        if self.is_protocol:
            return False, f"No attribute can be accessed for {self.name}"
        try:
            return True, next(attr for attr in self.attributes if attr.name == name)
        except StopIteration:
            if self.parent is None:
                return False, f'Attribute "{name}" is not defined in {self.name}.'

            success, value = self.parent.get_attribute(name)
            if not success:
                return False, f'Attribute "{name}" is not defined in {self.name}.'
            else:
                return success, value

    def define_attribute(self, name: str, typex):
        if self.is_protocol:
            return False, f"Attributes can not be defined for {self.name}"
        if not self.get_attribute(name)[0]:
            attribute = Attribute(name, typex)
            self.attributes.append(attribute)
            return True, attribute
        else:
            return False, f'Attribute "{name}" is already defined in {self.name}.'

    def update_attribute(self, name: str, typex):
        if self.is_protocol:
            return False, f"No attribute can be accessed for {self.name}"
        try:
            attribute = next(attr for attr in self.attributes if attr.name == name)
            attribute.type = typex
        except StopIteration:
            if self.parent is None:
                return False, f'Attribute "{name}" is not defined in {self.name}.'

            success, value = self.parent.get_attribute(name)
            if not success:
                return False, f'Attribute "{name}" is not defined in {self.name}.'
            else:
                value.type = typex

    def get_method(self, name: str):
        try:
            return True, next(method for method in self.methods if method.name == name)
        except StopIteration:
            if self.parent is None:
                return False, f'Method "{name}" is not defined in {self.name}.'

            success, value = self.parent.get_method(name)

            if not success:
                return False, f'Method "{name}" is not defined in {self.name}.'
            else:
                return success, value

    def get_base(self, name: str):
        parent = self.parent
        while parent:

            success, value = parent.get_method(name)
            if success:
                return value

            parent = parent.parent

        return None

    def define_method(self, name: str, param_names: list, param_types: list, return_type):
        if name in (method.name for method in self.methods):
            return False, f'Method "{name}" already defined in {self.name}'

        method = Method(name, param_names, param_types, return_type)
        self.methods.append(method)
        return True, method

    def update_method(self, name: str, param_types: list, return_type):
        try:
            method = next(method for method in self.methods if method.name == name)
            method.param_types = param_types
            method.return_type = return_type
        except StopIteration:
            if self.parent is None:
                return False, f'Method "{name}" is not defined in {self.name}.'

            success, value = self.parent.get_method(name)

            if not success:
                return False, f'Method "{name}" is not defined in {self.name}.'
            else:
                value.param_types = param_types
                value.return_type = return_type

    def all_attributes(self, clean=True):
        if self.is_protocol:
            return False, f"No attribute can be accessed for {self.name}"
        plain = OrderedDict() if self.parent is None else self.parent.all_attributes(False)
        for attr in self.attributes:
            plain[attr.name] = (attr, self)
        return plain.values() if clean else plain

    def all_methods(self, clean=True):
        plain = OrderedDict() if self.parent is None else self.parent.all_methods(False)
        for method in self.methods:
            plain[method.name] = (method, self)
        return plain.values() if clean else plain

    def conforms_to(self, other):
        return other.bypass() or self == other or self.parent is not None and self.parent.conforms_to(other)

    def bypass(self):
        return False

    def __str__(self):
        if self.is_protocol:

            output = f'protocol {self.name}'
            parent = '' if self.parent is None else ' extends' + ', '.join(parent.name for parent in self.parent)
            output += parent
            output += ' {'
            output += '\n\t' if self.attributes or self.methods else ''
            output += '\n\t'.join(str(x) for x in self.methods)
            output += '\n' if self.methods else ''
            output += '}\n'

            return output

        output = f'type {self.name}'
        parent = '' if self.parent is None else f' inherits {self.parent.name}'
        output += parent
        output += ' {'
        output += '\n\t' if self.attributes or self.methods else ''
        output += '\n\t'.join(str(x) for x in self.attributes)
        output += '\n\t' if self.attributes else ''
        output += '\n\t'.join(str(x) for x in self.methods)
        output += '\n' if self.methods else ''
        output += '}\n'
        return output

    def __repr__(self):
        return str(self)


class Attribute:
    def __init__(self, name, typex):
        self.name = name
        self.type = typex

    def __str__(self):
        return f'[attrib] {self.name}' + ' : {self.type.name}' if self.type is not None else '' + ';'

    def __repr__(self):
        return str(self)


class Method:
    def __init__(self, name, param_names, params_types, return_type):
        self.name = name
        self.param_names = param_names
        self.param_types = params_types
        self.return_type = return_type
        self.inferred_type = UnknownType()

    def __str__(self):
        params = ', '.join(f'{n}:{t.name}' for n, t in zip(self.param_names, self.param_types))
        return f'[method] {self.name}({params}): {self.return_type.name};'

    def __eq__(self, other):
        return other.name == self.name and \
            other.return_type == self.return_type and \
            other.param_types == self.param_types


class ErrorType(Type):
    def __init__(self):
        Type.__init__(self, '<error>')

    def conforms_to(self, other):
        return True

    def bypass(self):
        return True

    def __eq__(self, other):
        return isinstance(other, Type)


class VoidType(Type):
    def __init__(self):
        Type.__init__(self, '<void>')

    def conforms_to(self, other):
        raise Exception('Invalid type: void type.')

    def bypass(self):
        return True

    def __eq__(self, other):
        return isinstance(other, VoidType)


class ObjectType(Type):
    def __init__(self):
        Type.__init__(self, 'object')

    def __eq__(self, other):
        return other.name == self.name or isinstance(other, ObjectType)

    def conforms_to(self, other):
        return isinstance(other, ObjectType)


class NumberType(Type):
    def __init__(self):
        Type.__init__(self, 'number')

    def __eq__(self, other):
        return other.name == self.name or isinstance(other, NumberType)

    def conforms_to(self, other):
        return isinstance(other, NumberType) or isinstance(other, StringType) or isinstance(other, ObjectType)


class StringType(Type):
    def __init__(self):
        Type.__init__(self, 'string')

    def __eq__(self, other):
        return other.name == self.name or isinstance(other, StringType)

    def conforms_to(self, other):
        return isinstance(other, StringType) or isinstance(other, ObjectType)


class BooleanType(Type):
    def __init__(self):
        Type.__init__(self, 'boolean')

    def __eq__(self, other):
        return other.name == self.name or isinstance(other, BooleanType)

    def conforms_to(self, other):
        return isinstance(other, BooleanType) or isinstance(other, ObjectType)


class NullType(Type):
    def __init__(self):
        Type.__init__(self, 'null')

    def __eq__(self, other):
        return other.name == self.name or isinstance(other, NullType)

    def conforms_to(self, other):
        return False


class IterableType(Type):
    def __init__(self, value_type):
        Type.__init__(self, "iterable")
        self.value_type = value_type

    def conforms_to(self, other):
        return isinstance(other, IterableType) and other.value_type.conforms_to(self.value_type)


class UndefinedType(Type):
    def __init__(self):
        Type.__init__(self, 'undefined')

    def __eq__(self, other):
        return other.name == self.name or isinstance(other, UndefinedType)

    def conforms_to(self, other):
        return True


class UnknownType(Type):
    def __init__(self):
        Type.__init__(self, 'unknown')

    def __eq__(self, other):
        return other.name == self.name or isinstance(other, UnknownType)

    def conforms_to(self, other):
        return True

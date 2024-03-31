from ast_nodes.hulk import ProgramNode, TypeDeclarationNode, AttributeDeclarationNode, FunctionDeclarationNode, \
    ParameterDeclarationNode, ProtocolDeclarationNode
from semantic.type_hierarchy import ProtocolHierarchy
from semantic.types import UnknownType, UndefinedType
from errors.error import Error
from visitor import visitor


class TypeBuilder:

    def __init__(self, context, error: Error):

        self.context = context
        self.error = error
        self.current_type = None
        self.extensions = ProtocolHierarchy()

    @visitor.on('node')
    def visit(self, node, scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node: ProgramNode):

        protocol_definitions = [node for node in node.statements if isinstance(node, ProtocolDeclarationNode)]

        for type_definition in [node for node in node.statements if isinstance(node, TypeDeclarationNode)]:
            self.visit(type_definition)

        for protocol_definition in protocol_definitions:
            self.visit(protocol_definition)

        for function_definition in [node for node in node.statements if isinstance(node, FunctionDeclarationNode)]:
            self.visit(function_definition)

        for protocol in protocol_definitions:
            self.check_extensions(protocol)

    @visitor.when(TypeDeclarationNode)
    def visit(self, declaration: TypeDeclarationNode):

        success, value = self.context.get_type(declaration.id)

        if not success:
            self.error(message=value, line=declaration.line)
            return

        self.current_type = value

        self.current_type.params = {param.id: self.visit(param) for param in declaration.params}

        if declaration.parent:
            success, parent = self.context.get_type(declaration.parent)

            if not success:
                self.error(parent)
            else:

                if parent.conforms_to(self.current_type):
                    self.error(f"Circular dependency involving {declaration.parent} and {declaration.id}",
                               line=declaration.line)
                else:
                    success, error = self.current_type.set_parent(parent)

                    if not success:
                        self.error(error)

        for attribute_definition in declaration.attributes:
            self.visit(attribute_definition)

        for method_declaration in declaration.methods:
            self.visit(method_declaration)

    @visitor.when(AttributeDeclarationNode)
    def visit(self, declaration: AttributeDeclarationNode):

        success, attribute_type = (self.context.get_type(declaration.type) if declaration.type is not None
                                   else True, UnknownType())

        if not success:
            self.error(message=attribute_type, line=declaration.line)

        success, value = self.current_type.define_attribute(declaration.id,
                                                            attribute_type if success else UndefinedType())
        if not success:
            self.error(message=value, line=declaration.line)

    @visitor.when(ProtocolDeclarationNode)
    def visit(self, declaration: ProtocolDeclarationNode):
        success, value = self.context.get_type(declaration.id)

        if not success:
            self.error(message=value, line=declaration.line)
            return

        self.current_type = value

        for extend_declaration in declaration.extends or []:

            success, extend = self.context.get_type(extend_declaration)

            if not success:
                self.error(extend)
            else:

                if not extend.is_protocol:
                    self.error(f"{declaration.id} can not extend from {extend_declaration}",
                               line=declaration.line)
                else:
                    success, error = self.current_type.set_parent(extend)

                    if not success:
                        self.error(error)

        for method_declaration in declaration.methods:
            self.visit(method_declaration)

    @visitor.when(FunctionDeclarationNode)
    def visit(self, declaration: FunctionDeclarationNode):

        success, return_type = (self.context.get_type(declaration.type) if declaration.type is not None
                                else True, UnknownType())

        if not success:
            self.error(message=return_type, line=declaration.line)

        args_type = [self.visit(param) for param in declaration.params]

        if self.current_type:
            success, value = self.current_type.define_method(declaration.id, [param.id for param in declaration.params],
                                                             args_type, return_type if success else UndefinedType())
        else:
            success, value = self.context.define_method(declaration.id, [param.id for param in declaration.params],
                                                        args_type, return_type if success else UndefinedType())

        if not success:
            self.error(message=value, line=declaration.line)

    @visitor.when(ParameterDeclarationNode)
    def visit(self, declaration: ParameterDeclarationNode):
        success, parameter_type = self.context.get_type(declaration.type) if declaration.type is not None \
            else True, UnknownType()

        if not success:
            self.error(message=parameter_type, token=declaration.token)
            return UndefinedType()

        return parameter_type

    def check_extensions(self, declaration: ProtocolDeclarationNode):

        success, extension = self.context.get_type(declaration.id)
        if not success:
            return

        for extend in declaration.extends or []:

            success, extended = self.context.get_type(extend)

            if not success:
                continue

            if extended.conforms_to(extension):
                self.error(message=f"Circular dependency involving {extend} and {declaration.id}",
                           line=declaration.line)
                continue

            extended_methods = [method.id for method in extended.methods]

            for method in extension.methods:

                if method.id in extended_methods:
                    self.error(f"Method {method} is defined both in {extension.id} and {extended.id}",
                               line=method.line)

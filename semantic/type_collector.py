from ast_nodes.hulk import TypeDeclarationNode, ProgramNode, ProtocolDeclarationNode
from errors.error import Error
from semantic.context import Context
from visitor import visitor


class TypeCollector:

    def __init__(self, error: Error):
        self.context = None
        self.error = error

    @visitor.on('node')
    def visit(self, node, scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node: ProgramNode):
        self.context = Context()
        self.context.define_built_in_methods()

        for type_definition in [node for node in node.statements if isinstance(node, TypeDeclarationNode)]:
            self.visit(type_definition)

        for protocol_definition in [node for node in node.statements if isinstance(node, ProtocolDeclarationNode)]:
            self.visit(protocol_definition)

    @visitor.when(TypeDeclarationNode)
    def visit(self, declaration: TypeDeclarationNode):
        success, value = self.context.create_type(declaration.id.lex)
        if not success:
            self.error(message=value, line=declaration.id.line)

    @visitor.when(ProtocolDeclarationNode)
    def visit(self, declaration: ProtocolDeclarationNode):
        success, value = self.context.create_type(declaration.id.lex, is_protocol=True)
        if not success:
            self.error(message=value, line=declaration.id.line)
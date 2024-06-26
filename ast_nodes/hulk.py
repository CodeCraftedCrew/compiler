from ast_nodes.ast import Node, AtomicNode, BinaryNode
from lexer.tools import Token
from semantic.types import UnknownType


class ProgramNode(Node):
    def __init__(self, statements, global_expression):
        self.statements = statements
        self.global_expression = global_expression
        self.return_type = UnknownType()


class DeclarationNode(Node):
    pass


class ExpressionNode(Node):
    def __init__(self):
        self.inferred_type = UnknownType()


class ParameterDeclarationNode(DeclarationNode):
    def __init__(self, idx: Token, declared_type: Token):
        self.id = idx
        self.type = declared_type
        self.inferred_type = UnknownType()


class AttributeDeclarationNode(DeclarationNode):
    def __init__(self, idx: Token, declared_type: Token, expr: ExpressionNode):
        self.id = idx
        self.type = declared_type
        self.expression = expr
        self.inferred_type = UnknownType()


class FunctionDeclarationNode(DeclarationNode):
    def __init__(self, idx: Token, params: list[ParameterDeclarationNode], return_type: Token,
                 body: ExpressionNode = None):
        self.id = idx
        self.params = params
        self.type = return_type
        self.body = body
        self.inferred_type = UnknownType()

    def is_compact(self):
        return not self.is_extended()

    def is_extended(self):
        return isinstance(self.body, BlockNode)


class InheritsNode(DeclarationNode):
    def __init__(self, idx: Token, arguments: list[ExpressionNode]):
        self.id = idx
        self.arguments = arguments
        self.args_inferred_types = []


class TypeDeclarationNode(DeclarationNode):
    def __init__(self, idx: Token, params: list[ParameterDeclarationNode],
                 attributes: list[AttributeDeclarationNode], methods: list[FunctionDeclarationNode],
                 inherits: InheritsNode = None):
        self.id = idx
        self.params = params or []
        self.inherits = inherits
        self.attributes = attributes or []
        self.methods = methods or []


class ProtocolDeclarationNode(DeclarationNode):
    def __init__(self, idx: Token, methods: list[FunctionDeclarationNode], extends: list[str] = None):
        self.id = idx
        self.extends = extends
        self.methods = methods or []


class VariableDeclarationNode(ExpressionNode):
    def __init__(self, idx: Token, declared_type: Token, expr: ExpressionNode):
        super().__init__()
        self.id = idx
        self.type = declared_type
        self.expr = expr


class VariableNode(ExpressionNode):
    def __init__(self, idx: Token):
        super().__init__()
        self.id = idx


class DestructiveAssignNode(ExpressionNode):
    def __init__(self, idx: Token, expr: ExpressionNode):
        super().__init__()
        self.id = idx
        self.expr = expr


class CallNode(ExpressionNode):
    def __init__(self, obj: ExpressionNode, idx: Token, params: list[ExpressionNode],
                 is_attribute=False):
        super().__init__()
        self.obj = obj
        self.id = idx
        self.params = params
        self.is_attribute = is_attribute
        self.params_inferred_type = []


class ElIfNode(ExpressionNode):
    def __init__(self, condition: ExpressionNode, body: ExpressionNode):
        super().__init__()
        self.condition = condition
        self.body = body


class IfNode(ExpressionNode):
    def __init__(self, condition: ExpressionNode, body: ExpressionNode, elif_clauses: list[ElIfNode] = None,
                 else_body: ExpressionNode = None):
        super().__init__()
        self.condition = condition
        self.body = body
        self.elif_clauses = elif_clauses or []
        self.else_body = else_body


class ForNode(ExpressionNode):
    def __init__(self, item_idx: Token, declared_type: Token, iterable: ExpressionNode, body: ExpressionNode):
        super().__init__()
        self.item_id = item_idx
        self.item_declared_type = declared_type
        self.iterable = iterable
        self.body = body
        self.item_inferred_type = UnknownType()


class WhileNode(ExpressionNode):
    def __init__(self, condition: ExpressionNode, body: ExpressionNode, else_clause: ExpressionNode = None):
        super().__init__()
        self.condition = condition
        self.body = body
        self.else_clause = else_clause


class BlockNode(ExpressionNode):
    def __init__(self, body: list[ExpressionNode]):
        super().__init__()
        self.body = body


class LetNode(ExpressionNode):
    def __init__(self, declarations: list[VariableDeclarationNode], body: ExpressionNode):
        super().__init__()
        self.declarations = declarations
        self.body = body


class InstantiateNode(ExpressionNode):
    def __init__(self, idx: Token, params: list[ExpressionNode]):
        super().__init__()
        self.idx = idx
        self.params = params
        self.params_inferred_type = []


class VectorNode(ExpressionNode):
    def __init__(self, elements: list[ExpressionNode], generator: ExpressionNode = None, item: Token = None,
                 iterator: ExpressionNode = None):
        super().__init__()
        self.elements = elements
        self.generator = generator
        self.item = item
        self.iterator = iterator


class IndexNode(ExpressionNode):
    def __init__(self, obj: ExpressionNode, index: ExpressionNode):
        super().__init__()
        self.obj = obj
        self.index = index


class ModNode(BinaryNode):
    pass


class PlusNode(BinaryNode):
    pass


class MinusNode(BinaryNode):
    pass


class StarNode(BinaryNode):
    pass


class DivNode(BinaryNode):
    pass


class OrNode(BinaryNode):
    pass


class AndNode(BinaryNode):
    pass


class EqualNode(BinaryNode):
    pass


class DifferentNode(BinaryNode):
    pass


class LessNode(BinaryNode):
    pass


class LessEqualNode(BinaryNode):
    pass


class GreaterNode(BinaryNode):
    pass


class GreaterEqualNode(BinaryNode):
    pass


class IsNode(BinaryNode):
    pass


class AsNode(BinaryNode):
    pass


class ConcatNode(BinaryNode):
    def __init__(self, left: ExpressionNode, right: ExpressionNode, is_double=False):
        super().__init__(left, right)
        self.is_double = is_double


class PowerNode(BinaryNode):
    pass


class NotNode(ExpressionNode):
    def __init__(self, exp: ExpressionNode):
        super().__init__()
        self.expression = exp


class LiteralNode(AtomicNode):
    pass
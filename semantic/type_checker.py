from ast_nodes.ast import BinaryNode
from ast_nodes.hulk import ProgramNode, TypeDeclarationNode, AttributeDeclarationNode, FunctionDeclarationNode, \
    ProtocolDeclarationNode, VariableDeclarationNode, DestructiveAssignNode, CallNode, IfNode, ForNode, BlockNode, \
    WhileNode, LetNode, InstantiateNode, AsNode, PlusNode, MinusNode, DivNode, StarNode, PowerNode, EqualNode, \
    DifferentNode, NotNode, LiteralNode, ConcatNode, LessEqualNode, GreaterEqualNode, IsNode, GreaterNode, LessNode, \
    OrNode, AndNode
from errors.error import Error
from semantic.scope import Scope
from semantic.types import UnknownType, IterableType, BooleanType, NumberType, UndefinedType, StringType
from visitor import visitor


class TypeChecker:

    def __init__(self, context, error: Error):

        self.error = error
        self.context = context

        self.current_type = None
        self.current_method = None

    @visitor.on('node')
    def visit(self, node, scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node: ProgramNode):

        for statement in node.statements:
            self.visit(statement)

    @visitor.when(TypeDeclarationNode)
    def visit(self, declaration: TypeDeclarationNode, scope: Scope):

        success, value = self.context.get_type(declaration.id)

        if not success:
            return

        self.current_type = value

        attribute_scope = Scope(scope)

        for param_name, param_type in self.current_type.params:
            scope.define_variable(param_name, param_type)

        for attribute_declaration in declaration.attributes:
            self.visit(attribute_declaration.expression, attribute_scope)

        for method_declaration in declaration.methods:
            self.visit(method_declaration, scope)

    @visitor.when(AttributeDeclarationNode)
    def visit(self, attribute_declaration: AttributeDeclarationNode, scope: Scope):

        self.visit(attribute_declaration.expression, scope)

        if attribute_declaration.type:
            success, return_type = self.context.get_type(attribute_declaration.type)

            if not success:
                self.error(f"Invalid type for attribute {attribute_declaration.id}")
                return

            if not attribute_declaration.inferred_type.conforms_to(return_type):
                self.error(f"Inferred type does not conform to declared type for attribute {attribute_declaration.id}")

    @visitor.when(FunctionDeclarationNode)
    def visit(self, function_declaration: FunctionDeclarationNode, scope: Scope):

        if self.current_type:
            scope.define_variable("self", self.current_type)

        success, function = self.context.get_method(function_declaration.id) if self.current_type is None \
            else self.current_type.get_method(function_declaration.id)

        if not success:
            self.error(function)
            return

        self.current_method = function

        new_scope = Scope(scope)

        for param in function_declaration.params:
            new_scope.define_variable(param.id, self.visit(param, scope))

        self.visit(function_declaration.body, new_scope)

        if function_declaration.type:

            success, return_type = self.context.get_type(function_declaration.type)

            if not success:
                self.error(f"Invalid return type for function {function_declaration.id}")
                return

            if not function_declaration.inferred_type.conforms_to(return_type):
                self.error(f"Inferred type does not conform to declared type for function {function_declaration.id}"
                           + f" in type {self.current_type.name}" if self.current_type else "")

    @visitor.when(ProtocolDeclarationNode)
    def visit(self, node: ProtocolDeclarationNode, scope: Scope):
        pass

    @visitor.when(VariableDeclarationNode)
    def visit(self, variable: VariableDeclarationNode, scope: Scope):

        self.visit(variable.expr, scope)

        if variable.type:

            success, declared_type = self.context.get_type(variable.type)

            if not success:
                self.error(f"Invalid type for variable {variable.id}")
                return

            if not variable.inferred_type.conforms_to(declared_type):
                self.error(f"Inferred type does not conform to declared type for variable {variable.id}"
                           + f" of function {self.current_method.name}" if self.current_method else ""
                           + f" of type {self.current_type.name}" if self.current_type else "")

    @visitor.when(DestructiveAssignNode)
    def visit(self, assign: DestructiveAssignNode, scope: Scope):

        variable = scope.find_variable(assign.id)

        if variable is None:
            self.error(f"Variable {assign.id} does not exist in the scope "
                       f"in which the destructive assignment is declared.")

        self.visit(assign.expr, scope)

        if not assign.inferred_type.conforms_to(variable.type):
            self.error(f"Inferred type for destructive assignment does not conform to declared type for variable {variable.id}"
                       + f" of function {self.current_method.name}" if self.current_method else ""
                       + f" of type {self.current_type.name}" if self.current_type else "")

    @visitor.when(CallNode)
    def visit(self, call: CallNode, scope: Scope):

        if call.obj is None:
            success, method = self.context.get_method(call.id)
        else:
            self.visit(call.obj, scope)
            obj_type = call.inferred_type
            success, method = obj_type.get_method(call.id)

        if not success:
            self.error(method)
            return

        param_types = [self.visit(param, scope) for param in call.params]

        if len(param_types) != len(method.param_types):
            self.error(message=f"{method.name} expects {len(method.param_types)} parameters, got {len(param_types)}")

        for i in range(len(method.param_types)):
            if isinstance(method.param_types[i], UnknownType) or isinstance(param_types[i], UnknownType):
                continue
            if method.param_types[i].name != param_types[i].name:
                self.error(f"Parameter type mismatch, on {method.param_names[i]} got {param_types[i].name} "
                           f"expected {method.param_types[i].name}")

    @visitor.when(IfNode)
    def visit(self, node: IfNode, scope: Scope):

        self.visit(node.condition, scope)
        if node.condition.inferred_type != BooleanType():
            self.error(f"Can not implicitly convert from {node.condition.inferred_type.name} to boolean")

        for elif_clause in node.elif_clauses:
            self.visit(elif_clause.condition, scope)

            if elif_clause.condition.inferred_type != BooleanType():
                self.error(f"Can not implicitly convert from {node.condition.inferred_type.name} to boolean")

            self.visit(elif_clause.body, scope)

        self.visit(node.body, scope)
        self.visit(node.else_body, scope)

    @visitor.when(ForNode)
    def visit(self, node: ForNode, scope: Scope):

        self.visit(node.iterable, scope)
        new_scope = Scope(scope)
        new_scope.define_variable(node.item_id, node.item_declared_type)

        self.visit(node.body, scope)

    @visitor.when(WhileNode)
    def visit(self, node: WhileNode, scope: Scope):

        self.visit(node.condition, scope)

        if node.condition.inferred_type != BooleanType():
            self.error(f"Can not implicitly convert from {node.condition.inferred_type.name} to boolean")

        self.visit(node.body, scope)
        self.visit(node.else_clause, scope)

    @visitor.when(BlockNode)
    def visit(self, block: BlockNode, scope: Scope):

        for expression in block.body:
            self.visit(expression, scope)


    @visitor.when(LetNode)
    def visit(self, node: LetNode, scope: Scope):

        new_scope = Scope(scope)

        for declaration in node.declarations:
            self.visit(declaration, scope)
            new_scope.define_variable(declaration.id, declaration.type)
            new_scope = Scope(new_scope)

        self.visit(node.body, new_scope)


    @visitor.when(InstantiateNode)
    def visit(self, node: InstantiateNode, scope: Scope):
        success, inferred_type = self.context.get_type(node.idx)

        if not success:
            self.error(f"Invalid type {node.idx} for instance")

    @visitor.when(BinaryNode)
    def visit(self, node: BinaryNode, scope: Scope):

        self.visit(node.left, scope)

        if isinstance(node, AsNode):
            return

        inferred_type_right = self.visit(node.right, scope)
        node.right.inferred_type = inferred_type_right

        if (isinstance(node, PlusNode) or isinstance(node, MinusNode) or isinstance(node, DivNode)
                or isinstance(node, StarNode) or isinstance(node, PowerNode)):
            return NumberType()

        if (isinstance(node, EqualNode) or isinstance(node, DifferentNode) or isinstance(node, LessNode)
                or isinstance(node, LessEqualNode) or isinstance(node, GreaterNode) or isinstance(node, OrNode)
                or isinstance(node, GreaterEqualNode) or isinstance(node, IsNode) or isinstance(node, AndNode)):
            return BooleanType()

        if isinstance(node, ConcatNode):
            return StringType()

        return UndefinedType()

    @visitor.when(NotNode)
    def visit(self, node: NotNode, scope: Scope):

        if node.inferred_type != BooleanType():
            self.error(f"Can not implicitly convert from {node.inferred_type.name} to boolean")

        self.visit(node.expression, scope)

        return BooleanType()

    @visitor.when(LiteralNode)
    def visit(self, literal: LiteralNode, scope: Scope):
        pass

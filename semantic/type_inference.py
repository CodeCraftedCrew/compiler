from ast_nodes.ast import BinaryNode
from ast_nodes.hulk import ProgramNode, TypeDeclarationNode, BlockNode, LiteralNode, VariableDeclarationNode, \
    ProtocolDeclarationNode, FunctionDeclarationNode, ParameterDeclarationNode, AttributeDeclarationNode, \
    DestructiveAssignNode, CallNode, IfNode, ForNode, WhileNode, LetNode, InstantiateNode, MinusNode, PlusNode, DivNode, \
    StarNode, PowerNode, DifferentNode, LessEqualNode, GreaterNode, EqualNode, LessNode, GreaterEqualNode, IsNode, \
    AsNode, OrNode, AndNode, ConcatNode, NotNode
from lexer.tools import TokenType
from semantic.types import UnknownType, BooleanType, NumberType, StringType, NullType, UndefinedType, IterableType, Type
from semantic.scope import Scope
from visitor import visitor
from errors.error import Error


class TypeInference:

    def __init__(self, context, error: Error):

        self.context = context
        self.error = error

        self.changes = True

        self.current_type = None
        self.current_method = None

    def get_return_type(self, type_name: str):

        success, return_type = self.context.get_type(type_name)

        if success:
            return return_type

        return UndefinedType()

    @visitor.on('node')
    def visit(self, node, scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node: ProgramNode):

        while self.changes:

            self.changes = False

            scope = Scope()
            for statement in node.statements:
                self.visit(statement, scope.create_child_scope())

            inferred_type = self.visit(node.global_expression, scope.create_child_scope())

            if inferred_type != node.return_type:
                self.changes = True
                node.return_type = inferred_type

    @visitor.when(ParameterDeclarationNode)
    def visit(self, parameter_declaration: ParameterDeclarationNode, scope):

        if parameter_declaration.type in [None, "unknown"]:
            variable = scope.find_variable(parameter_declaration.id)

            if variable:
                self.changes = True
                inferred_type = self.context.get_lowest_ancestor(variable.inferred_types)
                parameter_declaration.type = inferred_type.name
                return inferred_type

        return self.get_return_type(parameter_declaration.type or "unknown")

    @visitor.when(AttributeDeclarationNode)
    def visit(self, attribute_declaration: AttributeDeclarationNode, scope):

        inferred_type = self.visit(attribute_declaration.expression, scope)
        lca = self.context.get_lowest_ancestor([inferred_type, attribute_declaration.inferred_type])

        if lca != attribute_declaration.inferred_type:
            self.changes = True
            attribute_declaration.inferred_type = lca

        return self.get_return_type(attribute_declaration.type) if attribute_declaration.type \
            else attribute_declaration.inferred_type

    @visitor.when(FunctionDeclarationNode)
    def visit(self, function_declaration: FunctionDeclarationNode, scope: Scope):

        if self.current_type:
            scope.define_variable("self", self.current_type)

        success, function = self.context.get_method(function_declaration.id) if self.current_type is None \
            else self.current_type.get_method(function_declaration.id)

        if not success:
            self.error(function, line=function_declaration.line)
            return

        self.current_method = function

        new_scope = Scope(scope)

        for param in function_declaration.params:
            new_scope.define_variable(param.id, self.visit(param, scope))

        inferred_type = self.visit(function_declaration.body, new_scope)
        lca = self.context.get_lowest_ancestor([inferred_type, function_declaration.inferred_type])

        if function_declaration.inferred_type != lca:
            self.changes = True
            function_declaration.inferred_type = lca

        return function_declaration.type or function_declaration.inferred_type

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

        return value

    @visitor.when(ProtocolDeclarationNode)
    def visit(self, node: ProtocolDeclarationNode, scope: Scope):
        pass

    @visitor.when(VariableDeclarationNode)
    def visit(self, variable: VariableDeclarationNode, scope: Scope):

        inferred_type = self.visit(variable.expr, scope)
        lca = self.context.get_lowest_ancestor([variable.inferred_type, inferred_type])

        if variable.inferred_type != lca:
            self.changes = True
            variable.inferred_type = inferred_type

        return variable.type or variable.inferred_type

    @visitor.when(DestructiveAssignNode)
    def visit(self, assign: DestructiveAssignNode, scope: Scope):

        variable = scope.find_variable(assign.id)

        if variable is None:
            return UndefinedType()

        inferred_type = self.visit(assign.expr, scope)
        lca = self.context.get_lowest_ancestor([assign.inferred_type, inferred_type])

        if assign.inferred_type != lca:
            self.changes = True
            assign.inferred_type = lca

        return variable.type or assign.inferred_type

    @visitor.when(CallNode)
    def visit(self, call: CallNode, scope: Scope):

        if call.obj is None:
            success, method = self.context.get_method(call.id)
        else:
            obj_type = self.visit(call.obj, scope)

            if obj_type in [None, UnknownType()]:
                return UnknownType()

            success, method = obj_type.get_method(call.id)

        if not success:
            self.error(method, line=call.line)
            return UndefinedType()

        param_types = [self.visit(param, scope) for param in call.params]

        if len(param_types) != len(method.param_types):
            self.error(message=f"{method.name} expects {len(method.param_types)} parameters, got {len(param_types)}")

        for i in range(len(method.param_types)):
            if method.param_types[i] is UnknownType or param_types[i] is UnknownType():
                continue
            if method.param_types[i].name != param_types[i].name:
                self.error(f"Parameter type mismatch, on {method.param_names[i]} got {param_types[i].name} "
                           f"expected {method.param_types[i].name}", line=call.line)

        return method.return_type or method.inferred_type or UnknownType()  # Todo add inferred type to methods

    @visitor.when(IfNode)
    def visit(self, node: IfNode, scope: Scope):

        self.visit(node.condition, scope)
        for elif_clause in node.elif_clauses:
            self.visit(elif_clause.condition, scope)

        possible_types = ([self.visit(node.body, scope), self.visit(node.else_body, scope)] +
                          [self.visit(elif_clause.body, scope) for elif_clause in node.elif_clauses])

        if any(typex is UnknownType() for typex in possible_types):
            return UnknownType()

        return_type = self.context.get_lowest_ancestor(possible_types)
        node.inferred_type = return_type
        return return_type

    @visitor.when(ForNode)
    def visit(self, node: ForNode, scope: Scope):

        inferred_iterable_type = self.visit(node.iterable, scope)
        inferred_type_item = None

        if isinstance(inferred_iterable_type, IterableType):
            if isinstance(inferred_iterable_type.value_type, str):

                success, type = self.context.get_type(inferred_iterable_type.value_type)

                if success:
                    inferred_type_item = type
                else:
                    inferred_type_item = UnknownType()

            elif isinstance(inferred_iterable_type.value_type, Type):
                inferred_type_item = inferred_iterable_type.value_type

            else:
                inferred_type_item = UnknownType()

        new_scope = Scope(scope)
        new_scope.define_variable(node.item_id, None, inferred_type_item)

        inferred_type = self.visit(node.body, scope)
        node.inferred_type = inferred_type

        return inferred_type

    @visitor.when(WhileNode)
    def visit(self, node: WhileNode, scope: Scope):

        condition_inferred_type = self.visit(node.condition, scope)
        node.condition.inferred_type = condition_inferred_type

        inferred_type = self.visit(node.body, scope)
        node.inferred_type = inferred_type

        else_inferred_type = self.visit(node.else_clause, scope)
        node.else_clause.inferred_type = else_inferred_type

        return inferred_type

    @visitor.when(BlockNode)
    def visit(self, block: BlockNode, scope: Scope):

        exp_type = None

        for expression in block.body:
            exp_type = self.visit(expression, scope)

        block.inferred_type = exp_type
        return exp_type

    @visitor.when(LetNode)
    def visit(self, node: LetNode, scope: Scope):

        new_scope = Scope(scope)

        for declaration in node.declarations:
            inferred_type = self.visit(declaration, scope)
            declaration.inferred_type = inferred_type
            new_scope.define_variable(declaration.id, declaration.type, inferred_type)
            new_scope = Scope(new_scope)

        inferred_type = self.visit(node.body, new_scope)

        if node.inferred_type != inferred_type:
            self.changes = True
            node.inferred_type = inferred_type

        return inferred_type

    @visitor.when(InstantiateNode)
    def visit(self, node: InstantiateNode, scope: Scope):
        success, inferred_type = self.context.get_type(node.idx)

        if not success:
            node.inferred_type = UndefinedType()
            return UndefinedType()

        node.inferred_type = inferred_type
        return inferred_type

    @visitor.when(BinaryNode)
    def visit(self, node: BinaryNode, scope: Scope):

        inferred_type_left = self.visit(node.left, scope)
        node.left.inferred_type = inferred_type_left

        if isinstance(node, AsNode):
            success, declared_type = self.context.get_type(node.right)

            if not success:
                return UndefinedType()
            else:
                return declared_type

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

        inferred_type = self.visit(node.expression, scope)
        node.expression.inferred_type = inferred_type

        return BooleanType()

    @visitor.when(LiteralNode)
    def visit(self, literal: LiteralNode, scope: Scope):
        if literal.lex.token_type == TokenType.TRUE or literal.lex.token_type == TokenType.FALSE:
            return BooleanType()
        if literal.lex.token_type == TokenType.NUMBER:
            return NumberType()
        if literal.lex.token_type == TokenType.STRING:
            return StringType()
        if literal.lex is None:
            return NullType()

        return UndefinedType()

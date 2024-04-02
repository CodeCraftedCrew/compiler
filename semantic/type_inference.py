from ast_nodes.ast import BinaryNode
from ast_nodes.hulk import ProgramNode, TypeDeclarationNode, BlockNode, LiteralNode, VariableDeclarationNode, \
    ProtocolDeclarationNode, FunctionDeclarationNode, ParameterDeclarationNode, AttributeDeclarationNode, \
    DestructiveAssignNode, CallNode, IfNode, ForNode, WhileNode, LetNode, InstantiateNode, MinusNode, PlusNode, DivNode, \
    StarNode, PowerNode, DifferentNode, LessEqualNode, GreaterNode, EqualNode, LessNode, GreaterEqualNode, IsNode, \
    AsNode, OrNode, AndNode, ConcatNode, NotNode, ModNode, VariableNode, InheritsNode, VectorNode, IndexNode
from lexer.tools import TokenType, Token
from semantic.types import UnknownType, BooleanType, NumberType, StringType, NullType, UndefinedType, IterableType, \
    Type, VectorType
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
            scope.add_builtin()

            for statement in node.statements:
                self.visit(statement, scope.create_child_scope())

            if node.global_expression:

                inferred_type = self.visit(node.global_expression, scope.create_child_scope())

                if inferred_type != node.return_type:
                    self.changes = True
                    node.return_type = inferred_type

    @visitor.when(ParameterDeclarationNode)
    def visit(self, parameter_declaration: ParameterDeclarationNode, scope):

        if not parameter_declaration.type:
            variable = scope.find_variable(parameter_declaration.id.lex)

            if variable:

                if parameter_declaration.inferred_type != variable.inferred_type:
                    self.changes = True
                    parameter_declaration.inferred_type = variable.inferred_type

                return parameter_declaration.inferred_type

        return self.get_return_type(parameter_declaration.type.lex) if parameter_declaration.type \
            else parameter_declaration.inferred_type

    @visitor.when(AttributeDeclarationNode)
    def visit(self, attribute_declaration: AttributeDeclarationNode, scope):

        inferred_type = self.visit(attribute_declaration.expression, scope)

        if inferred_type != attribute_declaration.expression.inferred_type:
            self.changes = True
            attribute_declaration.expression.inferred_type = inferred_type

        if inferred_type != attribute_declaration.inferred_type:
            self.changes = True
            attribute_declaration.inferred_type = inferred_type
            self.current_type.get_attribute(attribute_declaration.id.lex)[1].inferred_type = inferred_type

        return self.get_return_type(attribute_declaration.type.lex) if attribute_declaration.type \
            else attribute_declaration.inferred_type

    @visitor.when(FunctionDeclarationNode)
    def visit(self, function_declaration: FunctionDeclarationNode, scope: Scope):

        if self.current_type:
            scope.define_variable("self", self.current_type)

        success, function = self.context.get_method(function_declaration.id.lex) if self.current_type is None \
            else self.current_type.get_method(function_declaration.id.lex)

        if not success:
            return

        self.current_method = function

        new_scope = scope.create_child_scope()

        for param in function_declaration.params:
            new_scope.define_variable(param.id.lex, self.get_return_type(param.type.lex) if param.type else None,
                                      param.inferred_type)

        inferred_type = self.visit(function_declaration.body, new_scope)

        param_types = [self.visit(param, new_scope) for param in function_declaration.params]

        if function.param_types != param_types:
            self.changes = True
            function.param_types = param_types

        if function_declaration.inferred_type != inferred_type:
            self.changes = True
            function_declaration.inferred_type = inferred_type

            if not function_declaration.type:
                function.return_type = inferred_type

        return self.get_return_type(function_declaration.type.lex) if function_declaration.type \
            else function_declaration.inferred_type

    @visitor.when(InheritsNode)
    def visit(self, declaration: InheritsNode, scope: Scope):

        declaration.args_inferred_types = [self.visit(arg, scope) for arg in declaration.arguments]

    @visitor.when(TypeDeclarationNode)
    def visit(self, declaration: TypeDeclarationNode, scope: Scope):

        success, value = self.context.get_type(declaration.id.lex)

        if not success:
            return

        self.current_type = value

        attribute_scope = scope.create_child_scope()

        items = list(self.current_type.params.items())

        for i in range(len(items)):
            param_name, param_type = items[i]
            attribute_scope.define_variable(param_name, param_type, self.current_type.params_inferred_type[i])

        if declaration.inherits:
            self.visit(declaration.inherits, attribute_scope)

        for attribute_declaration in declaration.attributes:
            self.visit(attribute_declaration, attribute_scope)

        for i in range(len(items)):

            param_name, param_type = items[i]
            variable = attribute_scope.find_variable(param_name)

            if variable.inferred_type != UnknownType():
                lca = self.context.get_lowest_ancestor(self.current_type.params_inferred_type[i], variable.inferred_type)
                if lca != self.current_type.params_inferred_type[i]:
                    self.changes = True
                    self.current_type.params_inferred_type[i] = variable.inferred_type

        for method_declaration in declaration.methods:
            self.visit(method_declaration, scope)

        return value

    @visitor.when(ProtocolDeclarationNode)
    def visit(self, node: ProtocolDeclarationNode, scope: Scope):
        pass

    @visitor.when(VariableDeclarationNode)
    def visit(self, variable: VariableDeclarationNode, scope: Scope):

        inferred_type = self.visit(variable.expr, scope)
        lca = self.context.get_lowest_ancestor(variable.inferred_type, inferred_type)

        if variable.inferred_type != lca:
            self.changes = True
            variable.inferred_type = inferred_type

        return variable.inferred_type

    @visitor.when(VariableNode)
    def visit(self, variable: VariableNode, scope: Scope):

        scope_variable = scope.find_variable(variable.id.lex)

        if not scope_variable:
            return UndefinedType()

        return scope_variable.type or scope_variable.inferred_type

    @visitor.when(DestructiveAssignNode)
    def visit(self, assign: DestructiveAssignNode, scope: Scope):

        if isinstance(assign.id, Token):

            variable = scope.find_variable(assign.id.lex)

            if variable is None:
                return UndefinedType()

            declared_type = variable.type
        else:
            declared_type = self.visit(assign.id, scope)

            if assign.id.inferred_type != declared_type:
                self.changes = True
                assign.id.inferred_type = declared_type

        inferred_type = self.visit(assign.expr, scope)

        if assign.inferred_type != inferred_type:
            self.changes = True
            assign.inferred_type = inferred_type

        if declared_type and declared_type != UnknownType():
            return declared_type

        return assign.inferred_type

    @visitor.when(CallNode)
    def visit(self, call: CallNode, scope: Scope):

        if call.obj is None:
            if call.is_attribute:
                return UndefinedType()
            if self.current_type and self.current_method and call.token.lex == "base":
                success, method = self.current_type.get_base(self.current_method.name)
            else:
                success, method = self.context.get_method(call.token.lex)
        else:
            obj_type = self.visit(call.obj, scope)

            call.obj.inferred_type = obj_type

            if obj_type in [None, UnknownType()]:
                return UnknownType()
            if call.is_attribute:
                success, attribute = obj_type.get_attribute(call.token.lex)

                if not success:
                    return UndefinedType()

                return attribute.type or attribute.inferred_type

            success, method = obj_type.get_method(call.token.lex)

        if not success:
            return UnknownType()

        param_types = [self.visit(param, scope) for param in call.params]
        call.params_inferred_type = param_types

        for i in range(len(method.param_types)):
            if (isinstance(param_types[i], UnknownType) and param_types[i] != method.param_types[i] and
                    not isinstance(method.param_types[i], UnknownType)):
                self.changes = True
                call.params[i].inferred_type = method.param_types[i]

                if isinstance(call.params[i], VariableNode):
                    lca = self.context.get_lowest_ancestor(param_types[i], method.param_types[i])
                    scope.update_variable_inferred_type(call.params[i].id.lex, lca)

        return method.return_type or method.inferred_type

    @visitor.when(IfNode)
    def visit(self, node: IfNode, scope: Scope):

        condition_inferred_type = self.visit(node.condition, scope)
        node.condition.inferred_type = condition_inferred_type

        for elif_clause in node.elif_clauses:
            elif_inferred_type = self.visit(elif_clause.condition, scope)
            elif_clause.condition.inferred_type = elif_inferred_type

        possible_types = ([self.visit(node.body, scope), self.visit(node.else_body, scope)] +
                          [self.visit(elif_clause.body, scope) for elif_clause in node.elif_clauses])

        return_type = UnknownType()

        for possible_type in possible_types:
            return_type = self.context.get_lowest_ancestor(return_type, possible_type)

        if node.inferred_type != return_type:
            self.changes = True
            node.inferred_type = return_type

        return return_type

    @visitor.when(ForNode)
    def visit(self, node: ForNode, scope: Scope):

        inferred_iterable_type = self.visit(node.iterable, scope)

        if inferred_iterable_type.conforms_to(IterableType()) and not isinstance(inferred_iterable_type, UnknownType):
            inferred_type_item = inferred_iterable_type.get_method("current")[1].return_type
        else:
            inferred_type_item = UnknownType()

        new_scope = scope.create_child_scope()
        new_scope.define_variable(node.item_id.lex, self.get_return_type(node.item_declared_type.lex) if node.item_declared_type else None, inferred_type_item)

        inferred_type = self.visit(node.body, new_scope)
        node.inferred_type = inferred_type

        return inferred_type

    @visitor.when(WhileNode)
    def visit(self, node: WhileNode, scope: Scope):

        condition_inferred_type = self.visit(node.condition, scope)
        node.condition.inferred_type = condition_inferred_type

        inferred_type = self.visit(node.body, scope.create_child_scope())
        node.inferred_type = inferred_type

        if node.else_clause:
            else_inferred_type = self.visit(node.else_clause, scope.create_child_scope())
            node.else_clause.inferred_type = else_inferred_type

        return inferred_type

    @visitor.when(BlockNode)
    def visit(self, block: BlockNode, scope: Scope):

        exp_type = None

        for expression in block.body:
            exp_type = self.visit(expression, scope.create_child_scope())

        block.inferred_type = exp_type
        return exp_type

    @visitor.when(LetNode)
    def visit(self, node: LetNode, scope: Scope):

        new_scope = scope.create_child_scope()

        for declaration in node.declarations:
            inferred_type = self.visit(declaration, new_scope)
            declaration.inferred_type = inferred_type

            new_scope.define_variable(declaration.id.lex, self.get_return_type(declaration.type.lex) if declaration.type else None,
                                      inferred_type)
            new_scope = new_scope.create_child_scope()

        inferred_type = self.visit(node.body, new_scope)

        if node.inferred_type != inferred_type:
            self.changes = True
            node.inferred_type = inferred_type

        for declaration in reversed(node.declarations):

            variable = new_scope.find_variable(declaration.id.lex)

            if variable.inferred_type != UnknownType():
                declaration.inferred_type = variable.inferred_type

            new_scope = new_scope.parent

        return inferred_type

    @visitor.when(InstantiateNode)
    def visit(self, node: InstantiateNode, scope: Scope):

        param_types = [self.visit(param, scope) for param in node.params]
        node.params_inferred_type = param_types

        success, inferred_type = self.context.get_type(node.idx.lex)

        if not success:
            node.inferred_type = UndefinedType()
            return UndefinedType()

        parent = inferred_type

        while parent:

            if len(param_types) == len(parent.params):

                if len(parent.params_inferred_type) == 0:
                    parent.params_inferred_type = param_types

                for i in range(len(param_types)):
                    lca = self.context.get_lowest_ancestor(parent.params_inferred_type[i], param_types[i])
                    if lca != parent.params_inferred_type[i]:
                        self.changes = True
                        parent.params_inferred_type[i] = lca

                break
            else:
                parent = parent.parent

        node.inferred_type = inferred_type
        return inferred_type

    def infer_from_operator(self, node, type_instance, scope):

        if isinstance(node, VariableNode):
            variable = scope.find_variable(node.id.lex)

            if variable and not variable.type:
                lca = self.context.get_lowest_ancestor(type_instance, variable.inferred_type)
                if lca != variable.inferred_type:
                    self.changes = True
                    scope.update_variable_inferred_type(variable.name, lca)

    @visitor.when(BinaryNode)
    def visit(self, node: BinaryNode, scope: Scope):

        inferred_type_left = self.visit(node.left, scope)
        if node.left.inferred_type != inferred_type_left:
            self.changes = True
            node.left.inferred_type = inferred_type_left

        if isinstance(node, AsNode):
            success, declared_type = self.context.get_type(node.right)

            if not success:
                return UndefinedType()
            else:
                return declared_type

        if isinstance(node, IsNode):
            return BooleanType()

        inferred_type_right = self.visit(node.right, scope)

        if node.right.inferred_type != inferred_type_right:
            self.changes = True
            node.right.inferred_type = inferred_type_right

        if (isinstance(node, PlusNode) or isinstance(node, MinusNode) or isinstance(node, DivNode)
                or isinstance(node, StarNode) or isinstance(node, PowerNode) or isinstance(node, ModNode)):

            self.infer_from_operator(node.right, NumberType(), scope)
            self.infer_from_operator(node.left, NumberType(), scope)

            return NumberType()

        if isinstance(node, EqualNode) or isinstance(node, DifferentNode):
            return BooleanType()

        if (isinstance(node, LessNode) or isinstance(node, LessEqualNode) or isinstance(node, GreaterNode)
           or isinstance(node, GreaterEqualNode)):
            self.infer_from_operator(node.right, NumberType(), scope)
            self.infer_from_operator(node.left, NumberType(), scope)
            return BooleanType()

        if isinstance(node, AndNode) or isinstance(node, OrNode):
            self.infer_from_operator(node.right, BooleanType(), scope)
            return BooleanType()

        if isinstance(node, ConcatNode):
            return StringType()

        return UndefinedType()

    @visitor.when(NotNode)
    def visit(self, node: NotNode, scope: Scope):

        inferred_type = self.visit(node.expression, scope)
        node.expression.inferred_type = inferred_type

        return BooleanType()

    @visitor.when(VectorNode)
    def visit(self, node: VectorNode, scope: Scope):
        if node.elements:

            types = []
            for element in node.elements:
                inferred_type = self.visit(element, scope)
                if element.inferred_type != inferred_type:
                    self.changes = True
                    element.inferred_type = inferred_type
                types.append(inferred_type)

            lca = types[0]
            for inferred_type in types:
                lca = self.context.get_lowest_ancestor(lca, inferred_type)

            node.inferred_type = VectorType(lca)

            return VectorType(lca)
        else:
            inferred_iterable_type = self.visit(node.iterator, scope)

            if node.iterator.inferred_type != inferred_iterable_type:
                self.changes = True
                node.iterator.inferred_type = inferred_iterable_type

            if inferred_iterable_type.conforms_to(IterableType()) and not isinstance(inferred_iterable_type,
                                                                                     UnknownType):
                inferred_type_item = inferred_iterable_type.get_method("current")[1].return_type
            else:
                inferred_type_item = UnknownType()

            new_scope = scope.create_child_scope()
            new_scope.define_variable(node.item.lex, None, inferred_type_item)

            inferred_type = self.visit(node.generator, new_scope)
            node.inferred_type = VectorType(inferred_type)

            return VectorType(inferred_type)

    @visitor.when(IndexNode)
    def visit(self, node: IndexNode, scope: Scope):

        left_inferred_type = self.visit(node.obj, scope)

        if node.obj.inferred_type != left_inferred_type:
            self.changes = True
            node.obj.inferred_type = left_inferred_type

        index_inferred_type = self.visit(node.index, scope)

        if node.index.inferred_type != index_inferred_type:
            self.changes = True
            node.index.inferred_type = index_inferred_type

        if isinstance(left_inferred_type, VectorType):
            return left_inferred_type.item_type
        return UnknownType()


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

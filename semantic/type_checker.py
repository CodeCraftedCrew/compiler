from ast_nodes.ast import BinaryNode
from ast_nodes.hulk import ProgramNode, TypeDeclarationNode, AttributeDeclarationNode, FunctionDeclarationNode, \
    ProtocolDeclarationNode, VariableDeclarationNode, DestructiveAssignNode, CallNode, IfNode, ForNode, BlockNode, \
    WhileNode, LetNode, InstantiateNode, AsNode, PlusNode, MinusNode, DivNode, StarNode, PowerNode, \
    NotNode, LiteralNode, ConcatNode, LessEqualNode, GreaterEqualNode, IsNode, GreaterNode, LessNode, \
    OrNode, AndNode, ParameterDeclarationNode, VariableNode, InheritsNode, VectorNode, IndexNode
from errors.error import Error
from lexer.tools import Token
from semantic.scope import Scope
from semantic.types import UnknownType, IterableType, BooleanType, NumberType, UndefinedType, StringType, VectorType
from visitor import visitor


class TypeChecker:

    def __init__(self, context, error: Error):

        self.error = error
        self.context = context

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

        scope = Scope()

        for statement in node.statements:
            self.visit(statement, scope.create_child_scope())

        if node.global_expression:
            self.visit(node.global_expression, scope.create_child_scope())

            if node.return_type in [UnknownType(), UndefinedType()]:
                self.error("It was not possible to infer type of global expression")
        else:
            self.error(f"No global expression")

    @visitor.when(InheritsNode)
    def visit(self, declaration: InheritsNode, scope: Scope):

        for arg in declaration.args_inferred_types:
            self.visit(arg, scope)
            if arg in [UnknownType(), UndefinedType()]:
                self.error("It was not possible to infer type argument", line=declaration.id.line)

        success, parent = self.context.get_type(declaration.id.lex)

        if not success:
            return

        param_types = list(parent.params.values())

        for i in range(len(param_types)):
            if not param_types[i] or param_types[i] == UnknownType():
                param_types[i] = parent.params_inferred_type[i]

        if len(param_types) != len(declaration.args_inferred_types):
            self.error(f"{parent.name} expects {len(parent.params)} arguments, "
                       f"got {len(declaration.args_inferred_types)}", line=declaration.id.line)
            return

        for i in range(len(param_types)):

            if not declaration.args_inferred_types[i].conforms_to(param_types[i]):
                self.error(f"Argument type mismatch, on {parent.name} got {declaration.args_inferred_types[i].name} "
                           f"expected {param_types[i].name}", line=declaration.id.line)

    @visitor.when(TypeDeclarationNode)
    def visit(self, declaration: TypeDeclarationNode, scope: Scope):

        success, value = self.context.get_type(declaration.id.lex)

        if not success:
            return

        self.current_type = value

        attribute_scope = scope.create_child_scope()

        for param in declaration.params:
            attribute_scope.define_variable(param.id.lex,
                                            self.get_return_type(param.type.lex) if param.type else param.inferred_type)
            self.visit(param, scope)

        if len(declaration.params) > 0 and declaration.inherits:
            self.visit(declaration.inherits, attribute_scope)

        for attribute_declaration in declaration.attributes:
            self.visit(attribute_declaration.expression, attribute_scope)

            if attribute_declaration.expression.inferred_type in [UnknownType(), UndefinedType()]:
                self.error(f"It was not possible to infer the type for attribute", line=attribute_declaration.id.line)

        for method_declaration in declaration.methods:
            self.visit(method_declaration, scope)

        if declaration.inherits:

            success, parent = self.context.get_type(declaration.inherits.id.lex)

            if not success:
                return

            errors = self.context.check_inheritance(
                self.current_type, parent, declaration.inherits.args_inferred_types, declaration.id.line)

            for error in errors:
                self.error(error[0], line=error[1])

    @visitor.when(AttributeDeclarationNode)
    def visit(self, attribute_declaration: AttributeDeclarationNode, scope: Scope):

        self.visit(attribute_declaration.expression, scope)

        if attribute_declaration.type:
            success, return_type = self.context.get_type(attribute_declaration.type.lex)

            if not success:
                self.error(f"Invalid type for attribute {attribute_declaration.id.lex}", token=attribute_declaration.type)
                return

            if not attribute_declaration.inferred_type.conforms_to(return_type):
                self.error(
                    f"Inferred type does not conform to declared type for attribute {attribute_declaration.id.lex}",
                line=attribute_declaration.id.line)

    @visitor.when(ParameterDeclarationNode)
    def visit(self, parameter_declaration: ParameterDeclarationNode, scope):
        pass

    @visitor.when(FunctionDeclarationNode)
    def visit(self, function_declaration: FunctionDeclarationNode, scope: Scope):

        if function_declaration.id.lex == "base":
            self.error(f"Invalid function declaration `base` is a reserved word", line=function_declaration.id.line)
            return

        if self.current_type:
            scope.define_variable("self", self.current_type)

        success, function = self.context.get_method(function_declaration.id.lex) if self.current_type is None \
            else self.current_type.get_method(function_declaration.id.lex)

        if not success:
            self.error(function, line=function_declaration.id.line)
            return

        self.current_method = function

        new_scope = scope.create_child_scope()

        for param in function_declaration.params:
            new_scope.define_variable(param.id.lex,
                                      self.get_return_type(param.type.lex) if param.type else param.inferred_type)
            self.visit(param, scope)

        self.visit(function_declaration.body, new_scope)
        if function_declaration.inferred_type in [UnknownType(), UndefinedType()]:
            self.error(f"It was not possible to infer the type for function body", token=function_declaration.id)

        if function_declaration.type:

            success, return_type = self.context.get_type(function_declaration.type.lex)

            if not success:
                self.error(f"Invalid return type for function {function_declaration.id.lex}", line=function_declaration.id.line)
                return

            if not function_declaration.inferred_type.conforms_to(return_type):
                self.error(f"Inferred type does not conform to declared type for function {function_declaration.id.lex}"
                           + f" in type {self.current_type.name}" if self.current_type else "", line=function_declaration.id.line)

    @visitor.when(ProtocolDeclarationNode)
    def visit(self, node: ProtocolDeclarationNode, scope: Scope):
        pass

    @visitor.when(VariableDeclarationNode)
    def visit(self, variable: VariableDeclarationNode, scope: Scope):

        if scope.is_local_var(variable.id.lex):
            self.error(f"Variable {variable.id.lex} already defined in this scope", token=variable.id)

        self.visit(variable.expr, scope)

        if variable.type:

            success, declared_type = self.context.get_type(variable.type.lex)

            if not success:
                self.error(f"Invalid type for variable {variable.id.lex}", token=variable.id)
                return

            if not variable.inferred_type.conforms_to(declared_type):
                self.error(f"Inferred type does not conform to declared type for variable {variable.id.lex}",
                           token=variable.id)

    @visitor.when(DestructiveAssignNode)
    def visit(self, assign: DestructiveAssignNode, scope: Scope):

        if isinstance(assign.id, Token):

            variable = scope.find_variable(assign.id.lex)

            declared_type = variable.type

            if variable is None:
                self.error(f"Variable {assign.id.lex} does not exist in the scope "
                           f"in which the destructive assignment is declared.", token=assign.id)

            if assign.id.lex == "self" and self.current_type:
                self.error("`self` is not a valid assignment target", token=assign.id)
        else:
            self.visit(assign.id, scope)
            if assign.id.inferred_type in [UnknownType(), UndefinedType()]:
                self.error(f"It was not possible to infer the type for variable")
            declared_type = assign.id.inferred_type

        self.visit(assign.expr, scope)
        if assign.expr.inferred_type in [UnknownType(), UndefinedType()]:
            self.error(f"It was not possible to infer the type for destructive assignment")

        if not assign.inferred_type.conforms_to(declared_type):
            if isinstance(assign.id, Token):
                self.error(
                    f"Inferred type for destructive assignment does not conform to declared type for variable {assign.id.lex}"
                    , line=assign.id.line)
            else:
                self.error(
                    f"Inferred type for destructive assignment does not conform to declared type for the variable")


    @visitor.when(VariableNode)
    def visit(self, node, scope):
        if not scope.is_var_defined(node.id.lex):
            self.error(f"Variable {node.id.lex} is not defined in the current scope.", token=node.id)

    @visitor.when(CallNode)
    def visit(self, call: CallNode, scope: Scope):

        if call.obj is None:

            if self.current_type and self.current_method and call.token.lex == "base":
                success, method = self.current_type.get_base(self.current_method.name)
            else:
                success, method = self.context.get_method(call.token.lex)



                if not success:
                    self.error(method, token=call.token)
                    return
        else:
            self.visit(call.obj, scope)

            if call.obj.inferred_type in [UnknownType(), UndefinedType()]:
                self.error(f"It was not possible to infer the type for the object", token=call.token)

            obj_type = call.obj.inferred_type

            if call.is_attribute:

                success, attribute = obj_type.get_attribute(call.token.lex)

                if not success:
                    self.error(attribute, token=call.token)
                    return

                return

            success, method = obj_type.get_method(call.token.lex)

        if not success:
            self.error(method, token=call.token)
            return

        param_types = call.params_inferred_type

        if len(param_types) != len(method.param_types):
            self.error(message=f"{method.name} expects {len(method.param_types)} parameters, got {len(param_types)}", line=method.line)

        for i in range(len(method.param_types)):
            if not method.param_types[i] or isinstance(method.param_types[i], UnknownType):
                continue

            if isinstance(param_types[i], UnknownType):
                self.error(message=f"Type for parameter {i} could not be inferred", line=method.line)

            if not param_types[i].conforms_to(method.param_types[i] or UnknownType()):
                self.error(f"Parameter type mismatch, on {method.param_names[i]} got {param_types[i].name} "
                           f"expected {method.param_types[i].name}", line=method.line)

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

        if node.inferred_type in [UnknownType(), UndefinedType()]:
            self.error(f"It was not possible to infer the type for the if body")

    @visitor.when(ForNode)
    def visit(self, node: ForNode, scope: Scope):

        self.visit(node.iterable, scope)

        if node.item_declared_type:

            success, item_type = self.context.get_type(node.item_declared_type.lex)

            if not success:
                self.error(f"Type {node.item_declared_type.lex} of {node.item_id.lex} not defined", line=node.item_id.line)

            if not node.item_inferred_type.conforms_to(item_type):
                self.error(f"Inferred type does not conform to declared type for {node.item_id.lex}", line=node.item_id.line)
        else:
            item_type = node.item_inferred_type

        if not node.iterable.inferred_type.conforms_to(IterableType()):
            self.error(f"Type can not be determined because there is no implicit conversion from Iterable to "
                       f"{node.inferred_type}", line=node.item_id.line)

        new_scope = scope.create_child_scope()
        new_scope.define_variable(node.item_id.lex, item_type)

        self.visit(node.body, new_scope)

        if node.body.inferred_type in [UnknownType(), UndefinedType()]:
            self.error(f"It was not possible to infer the type for the for body", line=node.item_id.line)

    @visitor.when(WhileNode)
    def visit(self, node: WhileNode, scope: Scope):

        self.visit(node.condition, scope)

        if node.condition.inferred_type != BooleanType():
            self.error(f"Can not implicitly convert from {node.condition.inferred_type.name} to boolean")

        self.visit(node.body, scope)

        if node.body.inferred_type in [UnknownType(), UndefinedType()]:
            self.error(f"It was not possible to infer the type for the while body")



    @visitor.when(BlockNode)
    def visit(self, block: BlockNode, scope: Scope):

        for expression in block.body:
            self.visit(expression, scope.create_child_scope())

            if expression.inferred_type in [UnknownType(), UndefinedType()]:
                self.error(f"It was not possible to infer the type for the block expression")

    @visitor.when(LetNode)
    def visit(self, node: LetNode, scope: Scope):

        new_scope = scope.create_child_scope()

        for declaration in node.declarations:
            self.visit(declaration, new_scope)
            new_scope.define_variable(declaration.id.lex, self.get_return_type(
                declaration.type.lex) if declaration.type else declaration.inferred_type)
            new_scope = new_scope.create_child_scope()

        self.visit(node.body, new_scope)

        if node.body.inferred_type in [UnknownType(), UndefinedType()]:
            self.error(f"It was not possible to infer the type for the let body")

    @visitor.when(InstantiateNode)
    def visit(self, node: InstantiateNode, scope: Scope):
        success, inferred_type = self.context.get_type(node.idx.lex)

        parent = inferred_type
        while parent:

            if len(parent.params) > 0:

                args = parent.params_inferred_type

                if len(args) != len(node.params_inferred_type):
                    self.error(f"{parent.name} expects {len(parent.params)} arguments, "
                               f"got {len(node.params_inferred_type)}", line=node.idx.line)

                for i in range(len(args)):
                    if not node.params_inferred_type[i].conforms_to(args[i]):
                        self.error(f"Argument type mismatch, on {parent.name} got {node.params_inferred_type[i].name} "
                                   f"expected {args[i].name}", line=node.idx.line)
                break
            else:
                parent = parent.parent

        if not success:
            self.error(f"Invalid type {node.idx.lex} for instance", line=node.idx.line)

    @visitor.when(BinaryNode)
    def visit(self, node: BinaryNode, scope: Scope):

        self.visit(node.left, scope)

        if node.left.inferred_type in [UnknownType(), UndefinedType()]:
            self.error(f"It was not possible to infer the type for left operator")

        if isinstance(node, AsNode) or isinstance(node, IsNode):

            if not isinstance(node.right, Token):
                self.error(f"Operator can only be used with Types and Protocols")
            else:
                success, declared_type = self.context.get_type(node.right.lex)

                if not success:
                    self.error(f"Invalid type {node.right.lex}", token=node.right)
                    return

                if not declared_type.conforms_to(node.left.inferred_type):
                    self.error(f"You can not cast from {node.left.inferred_type} to {declared_type}")

            return

        self.visit(node.right, scope)

        if node.right.inferred_type in [UnknownType(), UndefinedType(), None]:
            self.error(f"It was not possible to infer the type for left operator")

        if (isinstance(node, PlusNode) or isinstance(node, MinusNode) or isinstance(node, DivNode)
                or isinstance(node, StarNode) or isinstance(node, PowerNode)):
            if not isinstance(node.left.inferred_type, NumberType) or not isinstance(node.right.inferred_type,
                                                                                     NumberType):
                self.error(f"Operator can only be applied to numbers")

        elif (isinstance(node, LessNode) or isinstance(node, LessEqualNode) or isinstance(node, GreaterNode)
              or isinstance(node, GreaterEqualNode)):

            if not isinstance(node.left.inferred_type, NumberType) or not isinstance(node.right.inferred_type,
                                                                                     NumberType):
                self.error(f"Operator can only be applied to numbers")

        elif isinstance(node, OrNode) or isinstance(node, AndNode):
            if not isinstance(node.left.inferred_type, BooleanType) or not isinstance(node.right.inferred_type,
                                                                                      BooleanType):
                self.error(f"Operator can only be applied to boolean")

        elif isinstance(node, ConcatNode):
            if not node.left.inferred_type.conforms_to(StringType()) or not node.right.inferred_type.conforms_to(
                    StringType()):
                self.error(f"Operator can only be applied to string or number")

    @visitor.when(NotNode)
    def visit(self, node: NotNode, scope: Scope):

        if node.inferred_type != BooleanType():
            self.error(f"Can not implicitly convert from {node.inferred_type.name} to boolean")

        self.visit(node.expression, scope)

    @visitor.when(VectorNode)
    def visit(self, node: VectorNode, scope: Scope):

        if node.elements:

            for element in node.elements:
                self.visit(element, scope)

            if isinstance(node.inferred_type, VectorType) and node.inferred_type.item_type in [UnknownType(), UndefinedType()]:
                self.error(f"Type of elements in vector could not be inferred")

        else:
            self.visit(node.iterator, scope)

            if not node.iterator.inferred_type.conforms_to(IterableType()):
                self.error(f"Type can not be determined because there is no implicit conversion from Vector to "
                           f"{node.iterator.inferred_type.name}", line=node.item.line)
                return

            new_scope = scope.create_child_scope()
            new_scope.define_variable(node.item.lex, node.iterator.inferred_type.get_method("current")[1].return_type)

            self.visit(node.generator, new_scope)

    @visitor.when(IndexNode)
    def visit(self, node: IndexNode, scope: Scope):

        self.visit(node.obj, scope)

        if not isinstance(node.obj, VectorType):
            self.error(f"Indexing is only valid for vectors")

        self.visit(node.index, scope)

        if node.index.inferred_type != NumberType():
            self.error(f"Index must be a number")

    @visitor.when(LiteralNode)
    def visit(self, literal: LiteralNode, scope: Scope):
        pass

import math
import random

from ast_nodes.hulk import VariableDeclarationNode, VariableNode, DestructiveAssignNode, IfNode, ForNode, WhileNode, \
    BlockNode, LetNode, InstantiateNode, VectorNode, IndexNode, ModNode, PlusNode, MinusNode, StarNode, DivNode, OrNode, \
    AndNode, EqualNode, DifferentNode, LessNode, LessEqualNode, GreaterNode, GreaterEqualNode, IsNode, AsNode, \
    ConcatNode, PowerNode, NotNode, LiteralNode, ExpressionNode, ProgramNode, ParameterDeclarationNode, \
    FunctionDeclarationNode, AttributeDeclarationNode, CallNode, TypeDeclarationNode, ProtocolDeclarationNode
from errors.error import Error
from lexer.tools import Token, TokenType
from semantic.context import Context
from semantic.scope import Scope, InstanceInfo, VariableInfo
from semantic.types import NullType, NumberType
from visitor import visitor


class Interpreter:
    def __init__(self, context: Context, error: Error):
        self.context = context
        self.error = error
        self.symbols_table = {}

        self.global_scope = Scope()
        self.global_scope.add_builtin()

        self.current_method = []
        self.built_in_functions = {
            "print": print,
            "cos": math.cos,
            "sin": math.sin,
            "tan": math.tan,
            "sqrt": math.sqrt,
            "exp": math.exp,
            "log": math.log,
            "rand": random.random,
            "range": range
        }

    @visitor.on('node')
    def visit(self, node, scope):
        pass

    @visitor.when(ExpressionNode)
    def visit(self, node: ExpressionNode, scope: Scope):
        pass

    @visitor.when(VariableDeclarationNode)
    def visit(self, node: VariableDeclarationNode, scope: Scope):
        expr_value = self.visit(node.expr, scope)
        scope.define_variable(node.id.lex, value=expr_value)

    @visitor.when(VariableNode)
    def visit(self, node, scope: Scope):
        variable_info = scope.find_variable(node.id.lex)
        if variable_info:
            return variable_info.value
        return NullType()

    @visitor.when(DestructiveAssignNode)
    def visit(self, node: DestructiveAssignNode, scope: Scope):
        expr_value = self.visit(node.expr, scope)
        if isinstance(node.id, Token):
            variable_info = scope.find_variable(node.id.lex)
            if variable_info:
                variable_info.value = expr_value
        if isinstance(node.id, CallNode):
            variable_info = scope.find_variable("self")
            if variable_info:
                variable_info.value.attributes[node.id.token.lex] = expr_value

        return expr_value

    @visitor.when(IfNode)
    def visit(self, node: IfNode, scope: Scope):
        condition_value = self.visit(node.condition, scope)
        if condition_value:
            return self.visit(node.body, scope.create_child_scope())
        for elif_clause in node.elif_clauses:
            elif_condition_value = self.visit(elif_clause.condition, scope)
            if elif_condition_value:
                return self.visit(elif_clause.body, scope.create_child_scope())
        if node.else_body:
            return self.visit(node.else_body, scope.create_child_scope())
        return NullType()

    @visitor.when(ForNode)
    def visit(self, node: ForNode, scope: Scope):
        iterable_value = self.visit(node.iterable, scope)
        result = NullType

        if (isinstance(node.iterable, CallNode) and node.iterable.token.lex == "range") or isinstance(iterable_value, list):
            for item in iterable_value:
                child_scope = scope.create_child_scope()
                child_scope.define_variable(node.item_id.lex, value=item)
                result = self.visit(node.body, child_scope)

            return result

        transform = LetNode(
            declarations=[VariableDeclarationNode(Token("iterable", TokenType.IDENTIFIER, -1, -1), None, node.iterable)],
            body=WhileNode(
                condition=CallNode(VariableNode(Token("iterable", TokenType.IDENTIFIER, -1, -1)), Token("next", TokenType.IDENTIFIER, -1, -1), []),
                body=LetNode(
                    declarations=[VariableDeclarationNode(node.item_id, None, CallNode(VariableNode(Token("iterable", TokenType.IDENTIFIER, -1, -1)), Token("current", TokenType.IDENTIFIER, -1, -1), []))],
                    body=node.body)))

        return self.visit(transform, scope)


    @visitor.when(WhileNode)
    def visit(self, node: WhileNode, scope: Scope):
        condition_value = self.visit(node.condition, scope)
        result = NullType()
        while condition_value:
            result = self.visit(node.body, scope.create_child_scope())
            condition_value = self.visit(node.condition, scope)
        if node.else_clause and isinstance(result, NullType):
            result = self.visit(node.else_clause, scope.create_child_scope())
        return result

    @visitor.when(BlockNode)
    def visit(self, node: BlockNode, scope: Scope):
        result = NullType()
        for expr in node.body:
            result = self.visit(expr, scope.create_child_scope())
        return result

    @visitor.when(LetNode)
    def visit(self, node: LetNode, scope: Scope):
        child_scope = scope.create_child_scope()
        for decl in node.declarations:
            decl_value = self.visit(decl, child_scope)
            child_scope.define_variable(decl.id.lex, value=decl_value)
        return self.visit(node.body, child_scope)

    @visitor.when(InstantiateNode)
    def visit(self, node: InstantiateNode, scope: Scope):
        param_values = [self.visit(param, scope) for param in node.params]

        param_names = list(node.inferred_type.params.keys())

        return self.instantiate(node.inferred_type, param_names, param_values)

    @visitor.when(VectorNode)
    def visit(self, node: VectorNode, scope: Scope):
        if node.elements:
            elements_values = [self.visit(element, scope) for element in node.elements]
            return elements_values
        else:
            iterator_value = self.visit(node.iterator, scope)

            result = []

            if (isinstance(node.iterator, CallNode) and node.iterator.token.lex == "range") or isinstance(
                    iterator_value, list):
                for item in iterator_value:
                    child_scope = scope.create_child_scope()
                    child_scope.define_variable(node.item.lex, value=item)
                    result.append(self.visit(node.generator, child_scope))

                return result

            new_scope = scope.create_child_scope()
            new_scope.define_variable("iterator", value=iterator_value)

            condition = CallNode(VariableNode(Token("iterator", TokenType.IDENTIFIER, -1, -1)),
                                       Token("next", TokenType.IDENTIFIER, -1, -1), [])

            condition_value = self.visit(condition, new_scope)
            while condition_value:
                item_value = self.visit(CallNode(
                            VariableNode(Token("iterator", TokenType.IDENTIFIER, -1, -1)),
                            Token("current", TokenType.IDENTIFIER, -1, -1), []), new_scope)

                while_scope = new_scope.create_child_scope()
                while_scope.define_variable(node.item.lex, item_value)

                result.append(self.visit(node.generator, while_scope))
                condition_value = self.visit(condition, new_scope)

            return result

    @visitor.when(IndexNode)
    def visit(self, node: IndexNode, scope: Scope):
        obj_value = self.visit(node.obj, scope)
        index_value = self.visit(node.index, scope)
        return obj_value[index_value]

    @visitor.when(ModNode)
    def visit(self, node: ModNode, scope: Scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val % right_val

    @visitor.when(PlusNode)
    def visit(self, node: PlusNode, scope: Scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val + right_val

    @visitor.when(MinusNode)
    def visit(self, node: MinusNode, scope: Scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val - right_val

    @visitor.when(StarNode)
    def visit(self, node: StarNode, scope: Scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val * right_val

    @visitor.when(DivNode)
    def visit(self, node: DivNode, scope: Scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val / right_val

    @visitor.when(OrNode)
    def visit(self, node: OrNode, scope: Scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val or right_val

    @visitor.when(AndNode)
    def visit(self, node: AndNode, scope: Scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val and right_val

    @visitor.when(EqualNode)
    def visit(self, node: EqualNode, scope: Scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val == right_val

    @visitor.when(DifferentNode)
    def visit(self, node: DifferentNode, scope: Scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val != right_val

    @visitor.when(LessNode)
    def visit(self, node: LessNode, scope: Scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val < right_val

    @visitor.when(LessEqualNode)
    def visit(self, node: LessEqualNode, scope: Scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val <= right_val

    @visitor.when(GreaterNode)
    def visit(self, node: GreaterNode, scope: Scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val > right_val

    @visitor.when(GreaterEqualNode)
    def visit(self, node: GreaterEqualNode, scope: Scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val >= right_val

    @visitor.when(IsNode)
    def visit(self, node, scope: Scope):
        left_val = self.visit(node.left, scope)

        assert isinstance(node.right, Token), "Static type must be an identifier"
        right_val = node.right.lex
        _, static_type = self.context.get_type(right_val)

        return left_val.type.conforms_to(static_type)

    @visitor.when(AsNode)
    def visit(self, node: AsNode, scope: Scope):

        left_val = self.visit(node.left, scope)

        assert isinstance(node.right, Token), "Static type must be an identifier"
        right_val = node.right.lex
        _, static_type = self.context.get_type(right_val)

        left_val.inferred_type = static_type
        return left_val

    @visitor.when(ConcatNode)
    def visit(self, node: ConcatNode, scope: Scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return str(left_val) + (" " if node.is_double else "") + str(right_val)

    @visitor.when(PowerNode)
    def visit(self, node: PowerNode, scope: Scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val ** right_val

    @visitor.when(NotNode)
    def visit(self, node: NotNode, scope: Scope):
        exp_val = self.visit(node.expression, scope)
        return not exp_val

    @visitor.when(LiteralNode)
    def visit(self, node: LiteralNode, scope: Scope):
        if (node.lex.token_type == TokenType.NUMBER):
            if '.' in node.lex.lex:
                return float(node.lex.lex)
            else:
                return int(node.lex.lex)
        if (node.lex.token_type == TokenType.TRUE):
            return True
        if (node.lex.token_type == TokenType.FALSE):
            return False
        return str(node.lex.lex)

    
    @visitor.when(CallNode)
    def visit(self, node: CallNode, scope: Scope):
        func_name = node.token.lex
        if func_name in self.built_in_functions:
            func = self.built_in_functions[func_name]
            args = [self.visit(arg, scope) for arg in node.params]
            return func(*args)
        else:
            new_scope = self.global_scope.create_child_scope()
            args = [self.visit(arg, scope) for arg in node.params]

            if node.obj:

                obj_value = self.visit(node.obj, scope)

                assert isinstance(obj_value, InstanceInfo), "Operator . can only be applied to instances."

                if node.is_attribute:
                    return obj_value.attributes[node.token.lex]
                else:
                    params, method = self.symbols_table[f"{obj_value.type.name}.method:{node.token.lex}"]

                    for i in range(len(params)):
                        new_scope.define_variable(params[i], value=args[i])

                    new_scope.define_variable("self", value=obj_value)

                    self.current_method.append(node.token.lex)
                    result = self.visit(method, new_scope)
                    self.current_method.remove(node.token.lex)

                    return result
            else:

                if node.token.lex == "base":

                    self_instance = scope.find_variable("self").value
                    return self.get_base_method(self_instance, args)

                if node.token.lex in self.built_in_functions.keys():
                    return self.built_in_functions[node.token.lex](args)

                params, function = self.symbols_table[f"function:{node.token.lex}"]

                for i in range(len(params)):
                    new_scope.define_variable(params[i], value=args[i])

                return self.visit(function, new_scope)

    @visitor.when(ProtocolDeclarationNode)
    def visit(self, node: ProtocolDeclarationNode, scope: Scope):

        for method_declaration in node.methods:
            self.symbols_table[f"{node.id.lex}.method:{method_declaration.id.lex}"] = (
                [param.id.lex for param in method_declaration.params], method_declaration.body)

    @visitor.when(TypeDeclarationNode)
    def visit(self, node: TypeDeclarationNode, scope: Scope):

        success, value = self.context.get_type(node.id.lex)

        if not success:
            return

        self.symbols_table[f"{node.id.lex}.{node.id.lex}.ctor"] = [param.id.lex for param in node.params]

        if node.inherits:
            self.symbols_table[f"from:{node.id.lex}to:{node.inherits.id.lex}"] = [arg for arg in node.inherits.arguments]

        for attribute_definition in node.attributes:
            self.symbols_table[f"{node.id.lex}.attribute:{attribute_definition.id.lex}"] = attribute_definition.expression

        for method_declaration in node.methods:
            self.symbols_table[f"{node.id.lex}.method:{method_declaration.id.lex}"] = (
                [param.id.lex for param in method_declaration.params], method_declaration.body)

    @visitor.when(AttributeDeclarationNode)
    def visit(self, node, scope):
        pass

    @visitor.when(FunctionDeclarationNode)
    def visit(self, node: FunctionDeclarationNode, scope: Scope):
        self.symbols_table[f"function:{node.id.lex}"] = (
            [param.id.lex for param in node.params], node.body)

    @visitor.when(ParameterDeclarationNode)
    def visit(self, node: ParameterDeclarationNode, scope: Scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node: ProgramNode):
        for type_definition in [node for node in node.statements if isinstance(node, TypeDeclarationNode)]:
            self.visit(type_definition, self.global_scope)

        for protocol_definition in [node for node in node.statements if isinstance(node, ProtocolDeclarationNode)]:
            self.visit(protocol_definition, self.global_scope)

        for function_definition in [node for node in node.statements if isinstance(node, FunctionDeclarationNode)]:
            self.visit(function_definition, self.global_scope)

        self.visit(node.global_expression, self.global_scope)
        self.global_scope.add_builtin()

    def get_base_method(self, self_instance: InstanceInfo, param_values):
        method_name = self.current_method[-1]

        assert method_name is not None, "`base` method can only be called from inside another one"

        parent = self_instance.parent

        while parent:

            method_identifier = f"{parent.name}.method:{method_name}"

            params, method = self.symbols_table.get(method_identifier, ([], None))

            if method:

                scope = self.global_scope.create_child_scope()
                scope.define_variable("self", value=parent)

                for i in range(len(params)):
                    scope.define_variable(params[i], value=param_values[i])

                return self.visit(method, scope)

            parent = parent.parent

        raise Exception(f"Base for method {method_name} not found")

    def instantiate(self, typex, param_names, param_values):

        attrs = list(attr.name for attr in typex.attributes)

        scope = Scope()

        for i in range(len(param_names)):
            scope.define_variable(param_names[i], value=param_values[i])

        attributes = {attr: self.visit(self.symbols_table[f"{typex.name}.attribute:{attr}"], scope) for attr in attrs}

        parent_arguments = self.symbols_table[f"from:{typex.name}to:{typex.parent.name}"]

        parent_names = list(typex.parent.params.keys())
        parent_values = [self.visit(arg, scope) for arg in parent_arguments]

        if len(parent_values) != len(typex.parent.params):
            parent_values = param_values

        instance = InstanceInfo(typex, param_names, param_values, attributes,
                                self.instantiate(typex.parent, parent_names, parent_values) if typex.parent else None)

        return instance


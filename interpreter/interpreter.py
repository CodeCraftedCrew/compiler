from ast_nodes.hulk import VariableDeclarationNode, VariableNode, DestructiveAssignNode, IfNode, ForNode, WhileNode, \
    BlockNode, LetNode, InstantiateNode, VectorNode, IndexNode, ModNode, PlusNode, MinusNode, StarNode, DivNode, OrNode, \
    AndNode, EqualNode, DifferentNode, LessNode, LessEqualNode, GreaterNode, GreaterEqualNode, IsNode, AsNode, \
    ConcatNode, PowerNode, NotNode, LiteralNode, ExpressionNode
from errors.error import Error
from lexer.tools import Token
from semantic.context import Context
from semantic.scope import VariableInfo, Scope
from semantic.types import NullType
from visitor import visitor


class Interpreter:
    def __init__(self, context: Context, error: Error):
        self.context = context
        self.error = error

    @visitor.when(ExpressionNode)
    def visit(self, node: ExpressionNode, scope: Scope):
        pass

    @visitor.when(VariableDeclarationNode)
    def visit(self, node, scope: Scope):
        expr_value = self.visit(node.expr, scope)
        scope.local_vars.append(VariableInfo(node.id, value=expr_value))

    @visitor.when(VariableNode)
    def visit(self, node, scope: Scope):
        variable_info = scope.find_variable(node.id)
        if variable_info:
            return variable_info.value
        return None

    @visitor.when(DestructiveAssignNode)
    def visit(self, node: DestructiveAssignNode, scope: Scope):
        expr_value = self.visit(node.expr, scope)
        variable_info = scope.find_variable(node.id.lex)
        if variable_info:
            variable_info.value = expr_value

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
        for item in iterable_value:
            child_scope = scope.create_child_scope()
            child_scope.define_variable(node.item_id, value=item)
            self.visit(node.body, child_scope)

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
        params_values = [self.visit(param, scope) for param in node.params]

    @visitor.when(VectorNode)
    def visit(self, node: VectorNode, scope: Scope):
        elements_values = [self.visit(element, scope) for element in node.elements]
        generator_value = self.visit(node.generator, scope) if node.generator else None

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

        return left_val.inferred_type.conforms_to(static_type)

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
        return node.lex
    
    @visitor.when(CallNode)
    def visit(self, node, scope):
        function = scope.find_variable(node.id)
        if function:
            params = [self.visit(param, scope) for param in node.params]
            return function.value(*params)
        return None
    
    @visitor.when(TypeDeclarationNode)
    def visit(self, node, scope):
        pass

    @visitor.when(AttributeDeclarationNode)
    def visit(self, node, scope):
        pass

    @visitor.when(FunctionDeclarationNode)
    def visit(self, node, scope):
        pass

    @visitor.when(ParameterDeclarationNode)
    def visit(self, node, scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node, scope):
        pass

class Interpreter:
    def __init__(self):
        self.errors = []

    @visitor.when(VariableDeclarationNode)
    def visit(self, node, scope):
        expr_value = self.visit(node.expr, scope)
        scope.local_vars.append(VariableInfo(node.id, value=expr_value))

    @visitor.when(VariableNode)
    def visit(self, node, scope):
        variable_info = scope.find_variable(node.id)
        if variable_info:
            return variable_info.value
        return None

    @visitor.when(DestructiveAssignNode)
    def visit(self, node, scope):
        expr_value = self.visit(node.expr, scope)
        variable_info = scope.find_variable(node.id)
        if variable_info:
            variable_info.value = expr_value

    @visitor.when(IfNode)
    def visit(self, node, scope):
        condition_value = self.visit(node.condition, scope)
        if condition_value:
            return self.visit(node.body, scope.create_child_scope())
        for elif_clause in node.elif_clauses:
            elif_condition_value = self.visit(elif_clause.condition, scope)
            if elif_condition_value:
                return self.visit(elif_clause.body, scope.create_child_scope())
        if node.else_body:
            return self.visit(node.else_body, scope.create_child_scope())
        return None

    @visitor.when(ForNode)
    def visit(self, node, scope):
        iterable_value = self.visit(node.iterable, scope)
        for item in iterable_value:
            child_scope = scope.create_child_scope()
            child_scope.define_variable(node.item_id, value=item)
            self.visit(node.body, child_scope)

    @visitor.when(WhileNode)
    def visit(self, node, scope):
        condition_value = self.visit(node.condition, scope)
        result = None
        while condition_value:
            result = self.visit(node.body, scope.create_child_scope())
            condition_value = self.visit(node.condition, scope)
        if node.else_clause and result is None:
            result = self.visit(node.else_clause, scope.create_child_scope())
        return result

    @visitor.when(BlockNode)
    def visit(self, node, scope):
        result = None
        for expr in node.body:
            result = self.visit(expr, scope.create_child_scope())
        return result

    @visitor.when(LetNode)
    def visit(self, node, scope):
        child_scope = scope.create_child_scope()
        for decl in node.declarations:
            self.visit(decl, child_scope)
        return self.visit(node.body, child_scope)

    @visitor.when(InstantiateNode)
    def visit(self, node, scope):
        params_values = [self.visit(param, scope) for param in node.params]

    @visitor.when(VectorNode)
    def visit(self, node, scope):
        elements_values = [self.visit(element, scope) for element in node.elements]
        generator_value = self.visit(node.generator, scope) if node.generator else None

    @visitor.when(IndexNode)
    def visit(self, node, scope):
        obj_value = self.visit(node.obj, scope)
        index_value = self.visit(node.index, scope)

    @visitor.when(ModNode)
    def visit(self, node, scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val % right_val

    @visitor.when(PlusNode)
    def visit(self, node, scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val + right_val

    @visitor.when(MinusNode)
    def visit(self, node, scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val - right_val

    @visitor.when(StarNode)
    def visit(self, node, scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val * right_val

    @visitor.when(DivNode)
    def visit(self, node, scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val / right_val

    @visitor.when(OrNode)
    def visit(self, node, scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val or right_val

    @visitor.when(AndNode)
    def visit(self, node, scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val and right_val

    @visitor.when(EqualNode)
    def visit(self, node, scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val == right_val

    @visitor.when(DifferentNode)
    def visit(self, node, scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val != right_val

    @visitor.when(LessNode)
    def visit(self, node, scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val < right_val

    @visitor.when(LessEqualNode)
    def visit(self, node, scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val <= right_val

    @visitor.when(GreaterNode)
    def visit(self, node, scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val > right_val

    @visitor.when(GreaterEqualNode)
    def visit(self, node, scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val >= right_val

    @visitor.when(IsNode)
    def visit(self, node, scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val is right_val

    @visitor.when(AsNode)
    def visit(self, node, scope):
        value = self.visit(node.left, scope)
        type = node.right
        if type == 'String':
            return str(value)
        elif type == 'Number':
            try:
                return float(value)
            except ValueError:
                self.errors.append(f"No se puede convertir '{value}' a Number.")
        elif type == 'Boolean':
            if isinstance(value, bool):
                return value
            elif isinstance(value, str):
                return value.lower() == 'true'
            else:
                self.errors.append(f"No se puede convertir '{value}' a Boolean.")
        else:
            self.errors.append(f"Tipo de destino de conversión '{type}' no reconocido.")

    @visitor.when(ConcatNode)
    def visit(self, node, scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return str(left_val) + str(right_val)

    @visitor.when(PowerNode)
    def visit(self, node, scope):
        left_val = self.visit(node.left, scope)
        right_val = self.visit(node.right, scope)
        return left_val ** right_val

    @visitor.when(NotNode)
    def visit(self, node, scope):
        exp_val = self.visit(node.expression, scope)
        return not exp_val

    @visitor.when(LiteralNode)
    def visit(self, node, scope):
        return node.lex
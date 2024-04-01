from ast_nodes.hulk import LiteralNode, PlusNode, MinusNode, ConcatNode, LessNode, LessEqualNode, GreaterNode, \
    GreaterEqualNode, IsNode, AsNode, EqualNode, DifferentNode, StarNode, DivNode, PowerNode, NotNode, ElIfNode, IfNode, \
    WhileNode, OrNode, AndNode, ForNode, VariableDeclarationNode, CallNode, InstantiateNode, FunctionDeclarationNode, \
    InheritsNode, AttributeDeclarationNode, ProtocolDeclarationNode, ParameterDeclarationNode, TypeDeclarationNode, \
    DestructiveAssignNode, LetNode, BlockNode, ProgramNode, VectorNode, IndexNode, ModNode, VariableNode
from grammar.grammar import Grammar
from lexer.tools import TokenType


def get_hulk_grammar():
    grammar = Grammar()

    program = grammar.non_terminal("program", True)
    epsilon = grammar.Epsilon

    (
        define_statement,
        statement,
        type_definition,
        function_definition,
        protocol_definition,
        block,
        non_block,
        block_body,
        statement_list,
        if_statement,
        invocation_expression,
        expression,
        add_expression,
        mult_expression,
        exponential_expression,
        unary_expression,
        primary_expression,
        literal,
        vector,
        index,
        arguments,
        argument_list,
        assignment,
        declaration_expression,
        member_access,
        type_declaration,
        multiple_declaration,
        arguments_definition,
        argument_list_definition,
        or_expression,
        and_expression,
        equality_expression,
        relational_expression,
        elif_statement,
        while_statement,
        for_statement,
        attribute_definition,
        type_inherits,
        inherits_declaration,
        type_body,
        type_element,
        type_arguments,
        instantiation,
        extends_definition,
        protocol_body,
        protocol_arguments_definition,
        extends_multiple_identifier,
        protocol_multiple_arguments_definition,
        vector_element,
        head_program,
        optional_semicolon,
        if_statement_block,
        while_statement_block,
        for_statement_block,
        declaration_expression_block,
        elif_statement_block,
        mod_expression
    ) = grammar.non_terminals(
        "define_statement statement type_definition function_definition protocol_definition block non_block "
        "block_body statement_list if_statement invocation_expression expression add_expression "
        "mult_expression exponential_expression unary_expression primary_expression literal vector index arguments "
        "argument_list assignment declaration_expression member_access type_declaration multiple_declaration "
        "arguments_definition argument_list_definition or_expression and_expression equality_expression "
        "relational_expression elif_statement while_statement for_statement attribute_definition type_inherits "
        "inherits_declaration type_body type_element type_arguments instantiation extends_definition "
        "protocol_body protocol_arguments_definition  extends_multiple_identifier "
        "protocol_multiple_arguments_definition vector_element head_program optional_semicolon if_statement_block "
        "while_statement_block for_statement_block declaration_expression_block elif_statement_block mod_expression"
    )

    (
        open_brace,
        close_brace,
        semicolon,
        plus,
        minus,
        multiply,
        divide,
        power,
        power_v2,
        mod,
        open_parenthesis,
        close_parenthesis,
        comma,
        concat,
        double_concat,
        dot,
        assignment_terminal,
        destructive_assignment,
        inline,
        colon,
        not_terminal,
        or_terminal,
        and_terminal,
        equal,
        different,
        less,
        less_equal,
        greater,
        greater_equal,
        open_bracket,
        close_bracket,
        double_pipe,
    ) = grammar.set_terminals(
        "{ } ; + - * / ^ ** % ( ) , @ @@ . = := => : ! | & == != < <= > >= [ ] ||"
    )

    (
        identifier,
        let,
        in_terminal,
        function,
        number,
        string,
        true,
        false,
        is_terminal,
        as_terminal,
        if_terminal,
        elif_terminal,
        else_terminal,
        while_terminal,
        for_terminal,
        type_terminal,
        inherits,
        new,
        protocol,
        extends,
    ) = grammar.set_terminals(
        "identifier let in function number string true false is as if elif else while for type "
        "inherits new protocol extends"
    )

    program %= head_program + statement, lambda h, s: ProgramNode(s[1], s[2])
    program %= head_program, lambda h, s: ProgramNode(s[1], [])
    program %= statement, lambda h, s: ProgramNode([], s[1])

    head_program %= define_statement, lambda h, s: [s[1]]
    head_program %= head_program + define_statement, lambda h, s: s[1] + [s[2]]

    define_statement %= function + function_definition, lambda h, s: s[2]
    define_statement %= type_definition, lambda h, s: s[1]
    define_statement %= protocol_definition, lambda h, s: s[1]

    statement %= block, lambda h, s: s[1]
    statement %= non_block + semicolon, lambda h, s: s[1]

    block %= open_brace + block_body + close_brace + optional_semicolon, lambda h, s: BlockNode(s[2])
    block %= if_statement_block, lambda h, s: s[1]
    block %= while_statement_block, lambda h, s: s[1]
    block %= for_statement_block, lambda h, s: s[1]
    block %= declaration_expression_block, lambda h, s: s[1]

    optional_semicolon %= semicolon, lambda h, s: None
    optional_semicolon %= epsilon, lambda h, s: None

    block_body %= statement_list, lambda h, s: s[1]
    block_body %= epsilon, lambda h, s: []

    statement_list %= statement, lambda h, s: [s[1]]
    statement_list %= statement_list + statement, lambda h, s: s[1] + [s[2]]

    non_block %= expression, lambda h, s: s[1]
    non_block %= if_statement, lambda h, s: s[1]
    non_block %= while_statement, lambda h, s: s[1]
    non_block %= for_statement, lambda h, s: s[1]
    non_block %= declaration_expression, lambda h, s: s[1]

    if_statement %= (if_terminal + open_parenthesis + or_expression + close_parenthesis + non_block
                     + elif_statement + else_terminal + non_block), lambda h, s: IfNode(s[3], s[5], s[6], s[8])
    if_statement %= (if_terminal + open_parenthesis + or_expression + close_parenthesis + non_block
                     + else_terminal + non_block), lambda h, s: IfNode(s[3], s[5], [], s[7])
    if_statement %= (if_terminal + open_parenthesis + or_expression + close_parenthesis + block
                     + elif_statement + else_terminal + non_block), lambda h, s: IfNode(s[3], s[5], s[6], s[8])
    if_statement %= (if_terminal + open_parenthesis + or_expression + close_parenthesis + block
                     + else_terminal + non_block), lambda h, s: IfNode(s[3], s[5], [], s[7])

    if_statement_block %= (if_terminal + open_parenthesis + or_expression + close_parenthesis + block
                           + elif_statement + else_terminal + block), lambda h, s: IfNode(s[3], s[5], s[6], s[8])
    if_statement_block %= (if_terminal + open_parenthesis + or_expression + close_parenthesis + block
                           + else_terminal + block), lambda h, s: IfNode(s[3], s[5], [], s[7])
    if_statement_block %= (if_terminal + open_parenthesis + or_expression + close_parenthesis + non_block
                           + elif_statement + else_terminal + block), lambda h, s: IfNode(s[3], s[5], s[6], s[8])
    if_statement_block %= (if_terminal + open_parenthesis + or_expression + close_parenthesis + non_block
                           + else_terminal + block), lambda h, s: IfNode(s[3], s[5], [], s[7])

    elif_statement %= (elif_terminal + open_parenthesis + or_expression + close_parenthesis
                       + non_block), lambda h, s: [ElIfNode(s[3], s[5])]
    elif_statement %= (elif_statement + elif_terminal + open_parenthesis + or_expression + close_parenthesis
                       + non_block), lambda h, s: s[1] + [ElIfNode(s[4], s[6])]
    elif_statement %= (elif_terminal + open_parenthesis + or_expression + close_parenthesis
                       + block), lambda h, s: [ElIfNode(s[3], s[5])]
    elif_statement %= (elif_statement + elif_terminal + open_parenthesis + or_expression + close_parenthesis
                       + block), lambda h, s: s[1] + [ElIfNode(s[4], s[6])]

    while_statement %= (while_terminal + open_parenthesis + or_expression + close_parenthesis + non_block,
                        lambda h, s: WhileNode(s[3], s[5]))

    while_statement_block %= (while_terminal + open_parenthesis + or_expression + close_parenthesis + block,
                              lambda h, s: WhileNode(s[3], s[5]))

    for_statement %= (for_terminal + open_parenthesis + identifier + type_declaration + in_terminal + expression
                      + close_parenthesis + non_block), lambda h, s: ForNode(s[3], s[4], s[6], s[8])

    for_statement_block %= (for_terminal + open_parenthesis + identifier + type_declaration + in_terminal + expression
                            + close_parenthesis + block), lambda h, s: ForNode(s[3], s[4], s[6], s[8])

    declaration_expression %= (let + identifier + type_declaration + assignment_terminal + non_block
                               + multiple_declaration + in_terminal + non_block,
                               lambda h, s: LetNode([VariableDeclarationNode(s[2], s[3], s[5])] + s[6], s[8]))
    declaration_expression_block %= (let + identifier + type_declaration + assignment_terminal + non_block
                                     + multiple_declaration + in_terminal + block,
                                     lambda h, s: LetNode([VariableDeclarationNode(s[2], s[3], s[5])] + s[6], s[8]))

    type_declaration %= colon + identifier, lambda h, s: s[2]
    type_declaration %= epsilon, lambda h, s: None

    multiple_declaration %= (comma + identifier + type_declaration + assignment_terminal + expression
                             + multiple_declaration, lambda h, s: [VariableDeclarationNode(s[2], s[3], s[5])] + s[6])
    multiple_declaration %= epsilon, lambda h, s: []

    expression %= assignment, lambda h, s: s[1]
    expression %= or_expression, lambda h, s: s[1]

    assignment %= identifier + destructive_assignment + non_block, lambda h, s: DestructiveAssignNode(s[1], s[3])
    assignment %= member_access + destructive_assignment + non_block, lambda h, s: DestructiveAssignNode(s[1], s[3])

    or_expression %= or_expression + or_terminal + and_expression, lambda h, s: OrNode(s[1], s[3])
    or_expression %= and_expression, lambda h, s: s[1]

    and_expression %= and_expression + and_terminal + equality_expression, lambda h, s: AndNode(s[1], s[3])
    and_expression %= equality_expression, lambda h, s: s[1]

    equality_expression %= equality_expression + equal + relational_expression, lambda h, s: EqualNode(s[1], s[3])
    equality_expression %= equality_expression + different + relational_expression, lambda h, s: DifferentNode(s[1],
                                                                                                               s[3])
    equality_expression %= relational_expression, lambda h, s: s[1]

    relational_expression %= mod_expression, lambda h, s: s[1]
    relational_expression %= relational_expression + less + mod_expression, lambda h, s: LessNode(s[1], s[3])
    relational_expression %= relational_expression + less_equal + mod_expression, lambda h, s: LessEqualNode(s[1], s[3])
    relational_expression %= relational_expression + greater + mod_expression, lambda h, s: GreaterNode(s[1], s[3])
    relational_expression %= relational_expression + greater_equal + mod_expression, lambda h, s: GreaterEqualNode(s[1],
                                                                                                                   s[3])
    relational_expression %= relational_expression + is_terminal + identifier, lambda h, s: IsNode(s[1], s[3])
    relational_expression %= relational_expression + as_terminal + identifier, lambda h, s: AsNode(s[1], s[3])

    mod_expression %= mod_expression + mod + add_expression, lambda h, s: ModNode(s[1], s[3])
    mod_expression %= add_expression, lambda h, s: s[1]

    add_expression %= add_expression + plus + mult_expression, lambda h, s: PlusNode(s[1], s[3])
    add_expression %= add_expression + minus + mult_expression, lambda h, s: MinusNode(s[1], s[3])
    add_expression %= add_expression + concat + mult_expression, lambda h, s: ConcatNode(s[1], s[3])
    add_expression %= add_expression + double_concat + mult_expression, lambda h, s: ConcatNode(s[1], s[3], True)
    add_expression %= mult_expression, lambda h, s: s[1]

    mult_expression %= mult_expression + multiply + exponential_expression, lambda h, s: StarNode(s[1], s[3])
    mult_expression %= mult_expression + divide + exponential_expression, lambda h, s: DivNode(s[1], s[3])
    mult_expression %= exponential_expression, lambda h, s: s[1]

    exponential_expression %= unary_expression + power + exponential_expression, lambda h, s: PowerNode(s[1], s[3])
    exponential_expression %= unary_expression + power_v2 + exponential_expression, lambda h, s: PowerNode(s[1], s[3])
    exponential_expression %= unary_expression, lambda h, s: s[1]

    unary_expression %= plus + primary_expression, lambda h, s: PlusNode(0, s[2])
    unary_expression %= minus + primary_expression, lambda h, s: MinusNode(0, s[2])
    unary_expression %= not_terminal + primary_expression, lambda h, s: NotNode(s[2])
    unary_expression %= primary_expression, lambda h, s: s[1]

    primary_expression %= literal, lambda h, s: s[1]
    primary_expression %= invocation_expression, lambda h, s: CallNode(None, s[1][0], s[1][1])
    primary_expression %= identifier, lambda h, s: VariableNode(s[1])
    primary_expression %= vector, lambda h, s: s[1]
    primary_expression %= index, lambda h, s: s[1]
    primary_expression %= member_access, lambda h, s: s[1]
    primary_expression %= open_parenthesis + non_block + close_parenthesis, lambda h, s: s[2]
    primary_expression %= instantiation, lambda h, s: s[1]

    literal %= number, lambda h, s: LiteralNode(s[1])
    literal %= string, lambda h, s: LiteralNode(s[1])
    literal %= true, lambda h, s: LiteralNode(s[1])
    literal %= false, lambda h, s: LiteralNode(s[1])

    invocation_expression %= identifier + open_parenthesis + arguments + close_parenthesis, lambda h, s: [s[1], s[3]]

    arguments %= argument_list, lambda h, s: s[1]
    arguments %= epsilon, lambda h, s: []

    argument_list %= argument_list + comma + non_block, lambda h, s: s[1] + [s[3]]
    argument_list %= non_block, lambda h, s: [s[1]]

    vector %= open_bracket + vector_element + close_bracket, lambda h, s: VectorNode(s[2])
    vector %= (open_bracket + non_block + double_pipe + identifier + in_terminal + non_block
               + close_bracket, lambda h, s: VectorNode([], s[2], s[4], s[6]))

    vector_element %= primary_expression, lambda h, s: [s[1]]
    vector_element %= vector_element + comma + primary_expression, lambda h, s: s[1] + [s[3]]

    index %= primary_expression + open_bracket + primary_expression + close_bracket, lambda h, s: IndexNode(s[1], s[3])

    member_access %= primary_expression + dot + identifier, lambda h, s: CallNode(s[1], s[3], [], True)
    member_access %= primary_expression + dot + invocation_expression, lambda h, s: CallNode(s[1], s[3][0], s[3][1])

    instantiation %= new + invocation_expression, lambda h, s: InstantiateNode(s[2][0], s[2][1])

    function_definition %= (identifier + open_parenthesis + arguments_definition + close_parenthesis +
                            type_declaration + inline + statement,
                            lambda h, s: FunctionDeclarationNode(s[1], s[3], s[5], s[7]))
    function_definition %= (identifier + open_parenthesis + arguments_definition + close_parenthesis +
                            type_declaration + block, lambda h, s: FunctionDeclarationNode(s[1], s[3], s[5], s[6]))

    arguments_definition %= argument_list_definition, lambda h, s: s[1]
    arguments_definition %= epsilon, lambda h, s: []

    argument_list_definition %= (argument_list_definition + comma + identifier + type_declaration,
                                 lambda h, s: s[1] + [ParameterDeclarationNode(s[3], s[4])])

    argument_list_definition %= identifier + type_declaration, lambda h, s: [ParameterDeclarationNode(s[1], s[2])]

    type_definition %= (type_terminal + identifier + type_arguments + type_inherits + open_brace + type_body
                        + close_brace + optional_semicolon,
                        lambda h, s: TypeDeclarationNode(idx=s[2], params=s[3],
                                                         attributes=[definition for definition in s[6] if
                                                                     isinstance(definition, AttributeDeclarationNode)],
                                                         methods=[definition for definition in s[6] if
                                                                  isinstance(definition, FunctionDeclarationNode)],
                                                         inherits=s[4]))

    type_arguments %= open_parenthesis + arguments_definition + close_parenthesis, lambda h, s: s[2]
    type_arguments %= epsilon, lambda h, s: []

    type_inherits %= inherits + identifier + inherits_declaration, lambda h, s: InheritsNode(s[2], s[3])
    type_inherits %= epsilon, lambda h, s: None

    inherits_declaration %= open_parenthesis + arguments + close_parenthesis, lambda h, s: s[2]
    inherits_declaration %= epsilon, lambda h, s: []

    type_body %= type_element, lambda h, s: s[1]
    type_body %= epsilon, lambda h, s: []

    type_element %= attribute_definition, lambda h, s: [s[1]]
    type_element %= function_definition, lambda h, s: [s[1]]
    type_element %= type_element + attribute_definition, lambda h, s: s[1] + [s[2]]
    type_element %= type_element + function_definition, lambda h, s: s[1] + [s[2]]

    attribute_definition %= (identifier + type_declaration + assignment_terminal + non_block + semicolon,
                             lambda h, s: AttributeDeclarationNode(s[1], s[2], s[4]))

    protocol_definition %= (protocol + identifier + extends_definition + open_brace + protocol_body + close_brace,
                            lambda h, s: ProtocolDeclarationNode(s[2], s[5], s[3]))

    extends_definition %= extends + identifier + extends_multiple_identifier, lambda h, s: [s[2]] + s[3]
    extends_definition %= epsilon, lambda h, s: []

    extends_multiple_identifier %= comma + identifier + extends_multiple_identifier, lambda h, s: [s[2]] + s[3]
    extends_multiple_identifier %= epsilon, lambda h, s: []

    protocol_body %= (protocol_body + identifier + open_parenthesis + protocol_arguments_definition + close_parenthesis
                      + colon + identifier + semicolon, lambda h, s: s[1] + [FunctionDeclarationNode(s[2], s[4], s[7])])
    protocol_body %= epsilon, lambda h, s: []

    protocol_arguments_definition %= (identifier + colon + identifier + protocol_multiple_arguments_definition,
                                      lambda h, s: [ParameterDeclarationNode(s[1], s[3])] + s[4])
    protocol_arguments_definition %= epsilon, lambda h, s: []

    protocol_multiple_arguments_definition %= (comma + identifier + colon + identifier +
                                               protocol_multiple_arguments_definition,
                                               lambda h, s: [ParameterDeclarationNode(s[2], s[4])] + s[5])
    protocol_multiple_arguments_definition %= epsilon, lambda h, s: []

    mapping = {
        TokenType.NUMBER: number,
        TokenType.STRING: string,
        TokenType.IDENTIFIER: identifier,
        TokenType.PLUS: plus,
        TokenType.MINUS: minus,
        TokenType.MULTIPLY: multiply,
        TokenType.DIVIDE: divide,
        TokenType.POWER: power,
        TokenType.POWER_V2: power_v2,
        TokenType.MOD: mod,
        TokenType.OPEN_BRACES: open_brace,
        TokenType.CLOSE_BRACES: close_brace,
        TokenType.SEMICOLON: semicolon,
        TokenType.OPEN_PARENTHESIS: open_parenthesis,
        TokenType.CLOSE_PARENTHESIS: close_parenthesis,
        TokenType.ARROW: inline,
        TokenType.COMMA: comma,
        TokenType.ASSIGNMENT: assignment_terminal,
        TokenType.DESTRUCTIVE_ASSIGNMENT: destructive_assignment,
        TokenType.DOT: dot,
        TokenType.COLON: colon,
        TokenType.OPEN_BRACKETS: open_bracket,
        TokenType.CLOSE_BRACKETS: close_bracket,
        TokenType.DOUBLE_PIPE: double_pipe,
        TokenType.CONCAT: concat,
        TokenType.DOUBLE_CONCAT: double_concat,
        TokenType.FUNCTION: function,
        TokenType.LET: let,
        TokenType.IN: in_terminal,
        TokenType.IF: if_terminal,
        TokenType.ELIF: elif_terminal,
        TokenType.ELSE: else_terminal,
        TokenType.TRUE: true,
        TokenType.FALSE: false,
        TokenType.WHILE: while_terminal,
        TokenType.FOR: for_terminal,
        TokenType.TYPE: type_terminal,
        TokenType.NEW: new,
        TokenType.INHERITS: inherits,
        TokenType.IS: is_terminal,
        TokenType.AS: as_terminal,
        TokenType.PROTOCOL: protocol,
        TokenType.EXTENDS: extends,
        TokenType.GREATER: greater,
        TokenType.LESS: less,
        TokenType.GREATER_EQUAL: greater_equal,
        TokenType.LESS_EQUAL: less_equal,
        TokenType.EQUAL: equal,
        TokenType.DIFFERENT: different,
        TokenType.AND: and_terminal,
        TokenType.OR: or_terminal,
        TokenType.NOT: not_terminal,
        TokenType.EOF: grammar.EOF
    }

    return grammar, mapping

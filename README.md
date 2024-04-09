# Compiler

Nahomi Bouza Rodríguez C412

Yisell Martínez Noa C412

Lauren Peraza García C311

## Lexer

### Inicialización

Necesitamos definir primero qué es un "token pattern" en nuestro proyecto. Se define como una clase que encapsula un patrón expresado en una expresión regular, específicamente para un tipo de token determinado.

Nuestro analizador léxico, recibe como parámetros la lista de "token patterns", el símbolo que indica el final del archivo (EOF) y la ruta al autómata en caché (que podría ser nula).

En primer lugar, se verifica la validez de la ruta proporcionada, asegurándose de que apunte a una ubicación existente y accesible. Posteriormente, se comprueba que el autómata en caché en dicha ubicación sea coherente con el autómata esperado para el analizador léxico, teniendo en cuenta la lista de "token patterns" proporcionada como parámetro.

Si la ruta es válida y el autómata en caché corresponde al autómata esperado, se procede a cargar dicho autómata utilizando la biblioteca dill. En caso contrario, si la ruta no es válida o el autómata en caché no es coherente con las especificaciones, se genera un nuevo autómata para el analizador léxico. Si la ruta es válida pero el autómata no coincide, entonces se guarda en la ruta proporcionada.

#### Autómata

El autómata del analizador léxico consiste en la **unión de los autómatas de cada uno de los "token patterns"** pasados como parámetros. Esta unión es convertida a determinista utilizando el método provisto en clase práctica.

La construcción de los autómatas para los "patterns" se lleva a cabo siguiendo una lógica específica.

1. La expresión regular correspondiente al patrón se tokeniza para dividirla en dígitos, símbolos, letras o caracteres especiales (utilizados en el motor de expresiones regulares).
2. Se procede a analizar sintácticamente la expresión utilizando el parser LR(1), el cual será explicado detalladamente más adelante. Aunque reconocemos que un parser LL(1) podría haber sido más apropiado en este contexto, optamos por LR(1) debido a su implementación previa como parte del parser de nuestro proyecto.
3. Se sustituyen los terminales digit, letter y symbol por los caracteres reales provenientes de la expresión regular.
4. Utilizando el método evaluate_reverse_parse, se construye el Árbol de Sintaxis Abstracta (AST).
5. Se evalúa el AST y el autómata resultante se convierte a su forma determinista, asegurando así que el analizador léxico pueda operar eficientemente en la identificación y clasificación de tokens dentro del texto proporcionado.

El análisis gramatical utilizado para interpretar cada una de las expresiones regulares se expone a continuación:

``` python
    regular_expression %= regular_expression + pipe + expression, lambda h, s: UnionNode(s[1], s[3])
    regular_expression %= expression, lambda h, s: s[1]
    regular_expression %= e, lambda h, s: EpsilonNode()

```

La clase `UnionNode` realiza la operación de unión, según lo descrito en la clase práctica, utilizando los autómatas de entrada.

``` python
    expression %= expression + repeat, lambda h, s: ConcatNode(s[1], s[2])
    expression %= repeat, lambda h, s: s[1]

```

La clase `ConcatNode` realiza la operación de concatenación, según lo descrito en la clase práctica, utilizando los autómatas de entrada.

``` python
    repeat %= repeated_item + star, lambda h, s: ClosureNode(s[1])
    repeat %= repeated_item + plus, lambda h, s: PlusNode(s[1])
    repeat %= repeated_item + question, lambda h, s: QuestionNode(s[1])
    repeat %= repeated_item, lambda h, s: s[1]
```

**ClosureNode:** Implementa la operación de clausura, permitiendo que el autómata resultante reconozca repeticiones arbitrarias del patrón original.

**PlusNode:** Similar a la clausura, pero requiere al menos una ocurrencia del patrón para que el autómata lo acepte.

**QuestionNode:** Añade un estado inicial con una transición épsilon al estado final del autómata original, permitiendo cero o una ocurrencia del patrón original en el texto reconocido.

``` python
    repeated_item %= open_parenthesis + regular_expression + close_parenthesis, lambda h, s: s[2]
    repeated_item %= open_bracket + contains + close_bracket, lambda h, s: s[2]
    repeated_item %= alphanumeric, lambda h, s: AlphanumericNode()
    repeated_item %= alpha, lambda h, s: LetterNode()
    repeated_item %= any_digit, lambda h, s: DigitNode()
    repeated_item %= character, lambda h, s: SymbolNode(s[1])
```

Las clases `LetterNode`, `DigitNode`, `AlphanumericNode` y `SymbolNode` generan autómatas que reconocen letras, dígitos, combinaciones alfanuméricas y símbolos respectivamente, según los parámetros proporcionados.

``` python
    contains %= caret + element, lambda h, s: ComplementNode(s[2])
    contains %= element, lambda h, s: JoinCharacterNode(s[1])

    element %= element + string, lambda h, s: ConcatCharacterNode(s[1], s[2])
    element %= string, lambda h, s: s[1]

    string %= character + hyphen + character, lambda h, s: RangeNode(s[1], s[3])
    string %= character, lambda h, s: s[1]

    character %= digit, lambda h, s: OrdNode(s[1])
    character %= letter, lambda h, s: OrdNode(s[1])
    character %= symbol, lambda h, s: OrdNode(s[1])

```

**ComplementNode:** Genera un autómata que reconoce todos los caracteres en string.printable excepto los especificados como parámetro.

**JoinCharacterNode:** Crea un autómata que es la unión de los autómatas de los caracteres recibidos como parámetros.

**ConcatCharacterNode:** Une caracteres en un mismo array para luego ser utilizados en un autómata.

**RangeNode:** Crea un array con todos los caracteres en el rango especificado por sus parámetros.

**OrdNode:** Asigna a un caracter un valor numérico correspondiente.

### Tokenización

La primera acción consiste en inicializar las variables de línea, columna y el punto de referencia en el programa. Posteriormente, se invoca al método "walk" con el texto y la posición actual.

Este método procede a recorrer el programa caracter a caracter, buscando transiciones válidas en el autómata del analizador léxico. Cuando ya no encuentra más transiciones válidas, devuelve el fragmento reconocido del texto y el estado final alcanzado, en caso de haberlo.

Si el "walk" finaliza sin haber alcanzado ningún estado final, se genera un error, indicando que ningún patrón válido ha sido reconocido, y se deja de analizar hasta el siguiente ";" que se encuentre, donde se retoma el reconocimiento, con el fin de detectar más errores potenciales.

En caso de haber alcanzado un estado final, el punto de referencia se mueve según la longitud del token reconocido. Si el token representa un salto de línea, tabulación o espacio en blanco, se actualizan las variables de línea y columna en consecuencia. De lo contrario, el token reconocido, junto con su posición en línea y columna, se retorna utilizando "yield", y este proceso continúa hasta que se analiza el programa completo.

## Parser

### Inicializacion

Nuestro parser recibe como parámetros la gramática y la ruta donde podría estar almacenada la caché de las tablas de acción y desplazamiento (action y goto) correspondientes. Si la ruta es válida y coincide con la gramática proporcionada, las tablas se cargan desde la caché. De lo contrario, si la ruta no es válida o no coincide con la gramática, se generan y almacenan estas tablas en la ruta especificada, siempre y cuando esta sea válida.

El proceso de generación de estas tablas está determinado por el tipo de parser LR que se haya implementado. En nuestro caso, hemos optado por el parser LR(1). En primer lugar, partiendo de la gramática aumentada, se obtiene su autómata correspondiente. Este autómata representa de manera formal los estados y las transiciones posibles del parser LR(1) para la gramática dada.

#### Autómata

Para construir este autómata, primero necesitamos calcular los conjuntos FIRST de todos los símbolos de la gramática. Luego, procedemos a calcular cada uno de los estados del autómata basado en la colección LR(0) y los conjuntos FIRST de la siguiente manera:

Por cada Ítem, empezando por el $I_0$, que se determina a partir de la producción inicial que se añadió cuando se aumentó la gramática, se halla su clausura.

La clausura se determina expandiendo cada ítem de la clausura actual hasta que no haya más cambios. Luego, con la operación de compresión, eliminamos los ítems repetidos, ya que algunas producciones podrían agregarse, con el mismo centro, a partir de otras producciones una o más veces.

Una vez que tenemos la clausura del estado actual, por cada símbolo en la gramática aumentada, calculamos el conjunto GOTO. Si este conjunto está vacío, continuamos con el siguiente símbolo. Si no lo está, determinamos el estado al que se puede llegar con este símbolo utilizando los ítems devueltos por el GOTO, y añadimos la transición correspondiente desde el estado actual al nuevo estado.

Una vez que todos los estados han sido visitados y no se pueden determinar nuevos estados, procedemos a la creación de la tabla de análisis sintáctico LR(1). Esta tabla consta de las entradas para los estados y los símbolos de entrada, donde cada entrada indica la acción a realizar o el estado al que transicionar cuando se encuentra en un determinado estado y se lee un determinado símbolo de entrada.

Para cada estado en el autómata LR(1), se examinan las transiciones salientes y las producciones asociadas a cada ítem del estado. Según el símbolo siguiente en cada ítem, se determina si se trata de un desplazamiento, una reducción o un estado de aceptación. Estas decisiones se basan en las reglas de la colección canónica LR(1).

Una vez que se han determinado todas las acciones para cada estado y símbolo de entrada, se completa la tabla. En el caso de las acciones de desplazamiento, se indica el nuevo estado al que transicionar. Para las reducciones, se especifica la producción a aplicar. En el caso de un estado de aceptación, se marca claramente como tal.

Al finalizar este proceso, la tabla de análisis sintáctico LR(1) está completa y lista para ser utilizada por el parser para analizar secuencias de entrada de acuerdo con la gramática dada.

Durante la creación de la tabla de análisis sintáctico LR(1), es posible que se produzcan conflictos, específicamente Shift-Reduce o Reduce-Reduce, en ciertas posiciones de la tabla.

### Análisis Sintáctico

Una vez que tenemos la lista de tokens obtenida del lexer, procedemos a intentar el análisis sintáctico utilizando las tablas obtenidas anteriormente. El procedimiento es el mismo, independientemente del método utilizado para crear las tablas.

Por cada token en la lista de tokens, intentamos buscar en la tabla de acción (todos los tokens deben ser terminales) si hay alguna coincidencia dada el estado que está en la cima de la pila y el token actual. Si se encuentra una coincidencia, varias posibilidades pueden surgir:

1. Si la acción es un SHIFT, se añade el símbolo terminal actual (lookahead) y el nuevo estado a la pila.
2. Si la acción es una reducción (REDUCE), entonces por cada símbolo en el cuerpo de la producción a la que se reduce, se sacan dos elementos de la pila: el estado y el símbolo terminal (lookahead). Luego, se procede a calcular el conjunto GOTO a partir del símbolo no terminal en la cabeza de la producción y se añaden tanto este símbolo como el nuevo estado a la pila.
3. Si la acción es ACCEPTED, nos aseguramos de que en la pila solo quede el símbolo inicial de la gramática y finalizamos el proceso de análisis sintáctico, devolviendo todas las reducciones y acciones realizadas para construir el árbol de sintaxis abstracta (AST).

En caso de no ser ninguno de estos tres tipos de acciones, se lanza una excepción debido a que se ha encontrado un tipo de acción desconocido en la tabla.

Si no se encuentra la coincidencia significa que el token no es válido en la secuencia y por tanto entramos en `Panic Mode` para intentar recuperarnos del error.

Escaneamos hacia abajo en la pila hasta que se encuentre un estado s con un "goto" en un determinado no terminal A. Luego, se descartan cero o más símbolos de entrada hasta que se encuentre un símbolo a que pueda seguir legítimamente a A. El analizador entonces apila el estado GOTO(s, A) y reanuda el análisis normal. Si no se cumplen ninguna de las condiciones anteriores se termina el análisis sintáctico.

Este proceso de análisis sintáctico continúa hasta que se agote la lista de tokens o se alcance un estado de aceptación. Si en algún momento se detecta un error en la entrada, se maneja adecuadamente y se avanza en la entrada hasta el siguiente punto de sincronización, generalmente un ";" en este caso.

### Estructura de la gramática

La gramática de Hulk se compone de varios elementos clave que permiten definir la sintaxis del lenguaje. A continuación, se detallan los componentes principales de la gramática:

#### No Terminales

Representan elementos sintácticos que pueden ser descompuestos en otros elementos hasta llegar a los terminales.

*Estructura del programa*

**program:** Es el nodo raíz, representa todo el programa.

**head_program:** Representa el encabezado de un programa en Hulk.

**statement:** Representa el punto de entrada al programa. Puede ser una instrucción individual en el código Hulk o un bloque de instrucciones.


*Declaraciones*

**define_statement:** Representa la declaración de funciones, de tipos y de protocolos.

**function_definition:** Define la estructura y el comportamiento de una función en Hulk.

**arguments_definition:** Representa la definición de los argumentos de una función.

**argument_list_definition:** Representa una lista de definiciones de argumentos en Hulk.

**type_definition:** Define la estructura de un tipo en Hulk, que puede incluir atributos y métodos.

**type_arguments:** Representa los argumentos utilizados en la definición de un tipo en Hulk.

**type_inherits:** Representa la declaración de herencia de un tipo en Hulk.

**inherits_declaration:** Representa la declaración de argumentos de los tipos de los cuales se hereda.

**type_body:** Representa el cuerpo de un tipo en Hulk, que puede incluir definiciones de atributos y métodos.

**type_element:** Representa un elemento dentro del cuerpo de un tipo en Hulk.

**attribute_definition:** Define la declaración de un atributo en Hulk.

**protocol_definition:** Define la estructura y los requisitos de un protocolo en Hulk.

**extends_definition:** Define la extensión de un tipo en Hulk.

**extends_multiple_identifier:** Representa múltiples identificadores extendidos en una declaración en Hulk.

**protocol_body:** Representa el cuerpo de un protocolo en Hulk, que contiene las definiciones de los métodos requeridos por el protocolo.

**protocol_arguments_definition:** Representa la definición de los argumentos requeridos por un protocolo en Hulk.

**protocol_multiple_arguments_definition:** Representa múltiples definiciones de argumentos en un protocolo.

**declaration_expression_block:** Representa una declaración de variables que contiene un bloque al final.

**declaration_expression:** Representa una expresión que declara una variable en Hulk. No contiene un bloque al final.

**type_declaration:** Representa la declaración de un tipo de variable en Hulk.

**multiple_declaration:** Representa una declaración de múltiples variables en Hulk.


*Instrucciones y bloques*

**block:** Representa un bloque de código delimitado por llaves ({}), que puede contener una secuencia de instrucciones. También puede ser un if, while, for o declaración de variables que contenga al final un bloque.

**non_block:** Representa una instrucción que no está dentro de un bloque. También puede ser un if, while, for o declaración de variables que no contenga al final un bloque.

**optional_semicolon:** Representa la posibilidad de un punto y coma opcional al final de un bloque.

**block_body:** Representa el cuerpo de un bloque, que consiste en una lista de instrucciones.

**statement_list:** Representa una lista de instrucciones.


*Control de flujo*

**if_statement_block:** Representa un condicional "if" que contiene un bloque al final.

**while_statement_block:** Representa un bucle "while" que contiene un bloque al final.

**for_statement_block:** Representa un bucle "for" que contiene un bloque al final.

**elif_statement_block:** Representa un condicional "elif" que contiene un bloque al final.

**if_statement:** Define una estructura de control condicional "if" con "else" en Hulk, que puede incluir declaraciones "elif". No contiene un bloque al final.

**elif_statement:** Define una estructura de control condicional "elif" en Hulk.

**while_statement:** Define una estructura de control de bucle "while" en Hulk. No contiene un bloque al final.

**for_statement:** Define una estructura de control de bucle "for" en Hulk. No contiene un bloque al final.


*Expresiones*

**expression:** Representa una expresión en Hulk, que puede ser una expresión aritmética, una invocación de función, una asignación, etc.

**assignment:** Representa una asignación de valor a una variable en Hulk.

**or_expression:** Representa una expresión lógica "or" en Hulk.

**and_expression:** Representa una expresión lógica "and" en Hulk.

**equality_expression:** Representa una expresión de igualdad en Hulk.

**relational_expression:** Representa una expresión relacional en Hulk.

**mod_expression:** Representa una expresión que realiza una operación de módulo en Hulk.

**add_expression:** Representa una expresión que realiza una operación de suma, resta o concatenación en Hulk.

**mult_expression:** Representa una expresión que realiza una operación de multiplicación o división en Hulk.

**exponential_expression:** Representa una expresión que realiza una operación de potencia en Hulk.

**unary_expression**: Representa una expresión que involucra operadores unarios en Hulk, como el operador de negación o el operador de signo.

**primary_expression:** Representa una expresión primaria en Hulk, que puede ser un literal, una variable, una invocación de función, un vector, una indexación, un acceso a miembros, una instanciación o llamar a una expresión dentro de paréntesis.

**literal:** Representa un valor literal en Hulk, como un número, una cadena o un valor booleano.

**invocation_expression**: Representa una expresión que invoca una función.

**arguments:** Representa los argumentos pasados a una función.

**argument_list:** Representa una lista de argumentos en Hulk.

**vector:** Representa una estructura de datos de vector en Hulk.

**vector_element:** Representa un elemento dentro de un vector en Hulk.

**index:** Representa una expresión que accede a un elemento dentro de un vector en Hulk.

**member_access:** Representa una expresión que accede a un miembro de una estructura en Hulk.

**instantiation:** Representa la instanciación de un objeto en Hulk.

#### Terminales

Son los elementos básicos del lenguaje, como palabras clave, operadores, separadores, identificadores y literales.

**Palabras clave:** Son palabras reservadas que tienen un significado específico en el lenguaje. Incluyen function, let, in, if, elif, else, while, for, type, new, inherits, is, as, protocol, extends, true, false.

**Identificadores:** Son nombres definidos por el usuario para variables, funciones, tipos y protocolos.

**Operadores:** Son símbolos utilizados para realizar operaciones sobre valores. Incluyen operadores aritméticos (+, -, *, /, **, ^, %), operadores relacionales (<, >, <=, >=, ==, !=), operadores lógicos (&, |, !), operadores de asignación (=, :=), operador de funciones inline '=>', operador de acceso a miembros '.', operador de comprensión de listas '||' y operadores de concatenación (@, @@).

**Separadores:** Son símbolos utilizados para separar partes del código. Incluyen comas ',', punto y coma ';', llaves '{', '}', corchetes '[', ']', paréntesis '(', ')', dos puntos ':'.

**Literales:** Son representaciones de valores constantes. Incluyen números, cadenas y booleanos.

#### Reglas de producción

Establecen cómo se pueden combinar los no terminales y terminales para formar expresiones válidas en el lenguaje. Estas reglas definen la estructura gramatical del lenguaje y cómo se pueden realizar las operaciones y declaraciones en el código Hulk. Ejemplo:

``` python
    program %= head_program + statement, lambda h, s: ProgramNode(s[1], s[2])
    program %= head_program, lambda h, s: ProgramNode(s[1], [])
    program %= statement, lambda h, s: ProgramNode([], s[1])
```

``` python
    mult_expression %= mult_expression + multiply + exponential_expression, lambda h, s: StarNode(s[1], s[3])
    mult_expression %= mult_expression + divide + exponential_expression, lambda h, s: DivNode(s[1], s[3])
    mult_expression %= exponential_expression, lambda h, s: s[1]
```

#### Funcionalidades Clave

La gramática de Hulk permite expresiones y operaciones típicas de un lenguaje de programación, incluyendo:

- Declaración y asignación de variables.
- Estructuras de control como condicionales (if, else, elif), bucles (while, for) y bloques de código.
- Definición y llamado de funciones.
- Manipulación de vectores y acceso a miembros.
- Definición de tipos y protocolos.
- Herencia, extensiones de tipos y polimorfismo.

La gramática de Hulk se implementa utilizando un enfoque de análisis sintáctico ascendente, donde se construye un AST a partir de la entrada del programa. Hay reglas de producción en la gramática que se traducen en funciones que construyen nodos del AST, lo que facilita la posterior interpretación y ejecución de las expresiones y declaraciones. Por ejemplo, una declaración de función se traduce en un nodo FunctionDeclarationNode, mientras que una expresión aritmética se puede traducir en nodos como PlusNode, MinusNode, etc.

La gramática presentada proporciona una base sólida para el diseño e implementación del lenguaje de programación Hulk. Permite expresar una amplia gama de operaciones y estructuras de control de manera clara y concisa, facilitando el desarrollo de programas complejos. La generación de AST a partir de esta gramática permite una interpretación eficiente y precisa de los programas escritos en Hulk.

## Análisis Semántico

Tras la realización del análisis sintáctico, se emplean los resultados obtenidos para, mediante los métodos proporcionados en la clase práctica, derivar el Árbol de Sintaxis Abstracta (AST) del programa en cuestión.

Nuestro análisis semántico se estructura en varias etapas, que describiremos a continuación:

### Collector

En esta etapa, se visitan únicamente los nodos Program, TypeDeclaration y ProtocolDeclaration con el propósito de añadir al contexto todas las posibles declaraciones de tipos y que más adelante en este análsis no importe el orden en que estos se declararon.

### Builder

Mediante el contexto obtenido del collector, se procede a visitar los nodos Program, TypeDeclaration, ProtocolDeclaration, AttributeDeclaration, FunctionDeclaration y ParameterDeclaration. Durante esta etapa, se verifica una serie de aspectos cruciales:

- TypeDeclaration: Se definen los parámetros, atributos y métodos asociados al tipo. Además, se gestiona la herencia, generando un registro de error en caso de detectarse una herencia cíclica.

- ProtocolDeclaration: Se especifican los métodos y se comprueba la extensión. En el caso de que un método coincida en nombre con otro, aunque redundante, se valida que sus parámetros y tipo de retorno sean consistentes.

- FunctionDeclaration: Se describen las funciones declaradas que no están asociadas a ningún tipo en particular.

### Inference

Utilizando el contexto obtenido del constructor, llevamos a cabo la inferencia de tipos para todas las expresiones, asignando los tipos inferidos a las variables, parámetros, atributos o tipos de retorno que no estén declarados.

En este proceso, se recorren todos los nodos del árbol sintáctico abstracto (AST) mientras haya cambios. Es decir, mientras que en una iteración se logre inferir un tipo que previamente era desconocido, se realiza otra iteración, ya que la inferencia de este tipo puede desencadenar la inferencia de otros. Por ejemplo, el uso de una función cuyos parámetros no estén definidos puede ayudar a determinar el tipo de dichos parámetros, lo que a su vez puede permitir definir variables y tipos de retorno en el cuerpo de la función.

Durante estas visitas, si nos encontramos con una variable, método o tipo no definido, se le asigna el tipo especial "UndefinedType", que abarca cualquier tipo, para evitar que este error interrumpa el proceso de inferencia de tipos.

Si un tipo se infiere a través de su uso, el tipo inferido será el ancestro más cercano entre todos los tipos inferidos en cada uso.

En el caso de una expresión cuyo tipo aún no se pueda inferir, se le asigna el tipo especial "UnknownType", que, al igual que "UndefinedType", abarca cualquier tipo. Esta asignación permite que el proceso de inferencia continúe sin interrupciones.

### Checker

Utilizando el contexto obtenido de la inferencia y los tipos inferidos, procedemos a verificar todos los nodos del AST.

Si un nodo tiene un tipo declarado, se verifica que el tipo inferido para la expresión conforme al tipo declarado. En caso de incompatibilidad, se emite un mensaje de error y se continúa con el análisis.

Si el tipo inferido es "UndefinedType", se imprime un error correspondiente. Igualmente, si el tipo inferido es "UnknownType", se informa que no se pudo inferir el tipo de la expresión en cuestión.

Este proceso garantiza la coherencia entre los tipos inferidos y los tipos declarados en el programa, identificando posibles discrepancias y proporcionando información detallada sobre los errores encontrados.

## Intérprete de Árbol

Por cada nodo del árbol realizamos la acción correspondiente. Aunque la implementación de estas acciones suele ser sencilla en la mayoría de los casos, existen algunas que, debido a su relevancia, resulta pertinente explicar un poco más detalladamente.

**Declaración de variables:** Se definen nuevas variables dentro del ámbito actual y sus valores se asignan a través de expresiones.

**Sentencias de flujo de control (if, while, for):** Se evalúan las condiciones y se ejecutan los bloques de código adecuados según el resultado. Los bucles se gestionan mediante ámbitos secundarios y condiciones de bucle. En el caso de un FOR donde se maneja un iterable de HULK se convierte al while equilavente.

**Llamadas a funciones:** En primer lugar, se realiza una búsqueda en la tabla de símbolos para localizar la definición de la función correspondiente. Una vez localizada, se procede a evaluar los argumentos pasados a la función. Posteriormente, se crea un nuevo ámbito secundario donde se gestionan los parámetros de la función y las variables locales definidas dentro de ella. Dentro de este ámbito, se ejecuta el cuerpo de la función. Es importante destacar que en el contexto de las clases, se emplea el mecanismo de resolución del método base para manejar las llamadas al método base dentro de una clase, garantizando así la correcta herencia y ejecución de métodos en la jerarquía de clases.

**Declaración de tipo:** Este proceso inicia con la búsqueda del tipo en el contexto del programa. Si el tipo es encontrado, se procede a almacenar la información relacionada con los parámetros del constructor en la tabla de símbolos. En caso de que el tipo herede de otro, se registra la información de la herencia en la misma tabla de símbolos. Posteriormente, se itera sobre los atributos y métodos definidos en la declaración del tipo:
    - Los atributos son almacenados en la tabla de símbolos junto con su expresión correspondiente.
    - Los métodos son registrados en la tabla de símbolos junto con la lista de parámetros y el cuerpo del método.

**Declaración de protocolo:**  En este proceso, se procede a iterar sobre los métodos declarados en el protocolo. Para cada método, se guarda en la tabla de símbolos la lista de parámetros y el cuerpo del método, asociándolos al nombre del protocolo y del método respectivamente. Esta operación es esencial para establecer la estructura y comportamiento esperado de los tipos y protocolos en el sistema, facilitando así su utilización y comprensión en el desarrollo del programa.

**Declaración de función:** Se almacena en la tabla de símbolos el nombre de la función, la lista de parámetros que espera recibir y el cuerpo de la función, que contiene las instrucciones a ejecutar.

**Vectores:** Si tienen elementos definidos, se evalúa cada elemento y se retorna la lista de valores correspondiente. En el caso de que sean generados mediante una expresión, se manejan de manera equivalente a un bucle while, como en el caso de los bucles for.

**Instanciación:** Al instanciar una variable, se crea una instancia del tipo de la variable en cuestión, así como de todos los tipos que esta variable hereda. Esto asegura que todas las características y funcionalidades de los tipos heredados estén disponibles y correctamente inicializadas para su uso en el programa.

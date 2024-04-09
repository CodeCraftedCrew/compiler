# compiler

Nahomi Bouza Rodriguec C412
Yisell Martinez Noa C412
Lauren Peraza Garcia C311

## Lexer

### Inicialización

Necesitamos definir primero que es un "token pattern" en nuestro proyecto. Un "token pattern" se define como una clase que encapsula un patrón expresado en una expresión regular, específicamente para un tipo de token determinado.

Nuestro analizador léxico, recibe como parámetros la lista de "token patterns", el símbolo que indica el final del archivo (EOF) y la ruta al autómata en caché (que podría ser nula).

En primer lugar, se verifica la validez de la ruta proporcionada, asegurándose de que apunte a una ubicación existente y accesible. Posteriormente, se comprueba que el autómata en caché en dicha ubicación sea coherente con el autómata esperado para el analizador léxico, teniendo en cuenta la lista de "token patterns" proporcionada como parámetro.

Si la ruta es válida y el autómata en caché corresponde al autómata esperado, se procede a cargar dicho autómata utilizando la biblioteca dill. En caso contrario, si la ruta no es válida o el autómata en caché no es coherente con las especificaciones, se genera un nuevo autómata para el analizador léxico. Si la ruta es válida pero el autómata no coincide, entonces se guarda en la ruta proporcionada.

#### Autómata

El autómata del analizador léxico consiste en la unión de los autómatas de cada uno de los "token patterns" pasados como parámetros. Esta unión es convertida a determinista utilizando el método provisto en clase práctica.

La construcción de los autómatas para los "patterns" se lleva a cabo siguiendo una lógica específica.

1. La expresión regular correspondiente al patrón se tokeniza para dividirla en dígitos, símbolos, letras o caracteres especiales (utilizados en el motor de expresiones regulares)
2. Se procede a analizar sintácticamente la expresión utilizando el parser LR(1), el cual será explicado detalladamente más adelante. Aunque reconocemos que un parser LL(1) podría haber sido más apropiado en este contexto, optamos por LR(1) debido a su implementación previa como parte del parser de nuestro proyecto.
3. Se sustituyen los terminales digit, letter y symbol por los caracteres reales provenientes de la expresión regular.
4. Utilizando el método evaluate_reverse_parse, se construye el Árbol de Sintaxis Abstracta (AST).
5. Se evalua el AST y el autómata resultante se convierte a su forma determinista, asegurando así que el analizador léxico pueda operar eficientemente en la identificación y clasificación de tokens dentro del texto proporcionado.

El análisis gramatical utilizado para interpretar cada una de las expresiones regulares se expone a continuación:

``` python
    regular_expression %= regular_expression + pipe + expression, lambda h, s: UnionNode(s[1], s[3])
    regular_expression %= expression, lambda h, s: s[1]
    regular_expression %= e, lambda h, s: EpsilonNode()

```

UnionNode: se encarga de crear un nuevo automata que consiste en un nuevo estado inicial que tiene una epsilon transicion a cada uno de los estados iniciales de los automatas unidos y un nuevo estado final al que se llega tambie con una epsilon transicion de los de estados finales de los automatas que une.

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

ClosureNode: Implementa la operación de clausura, permitiendo que el autómata resultante reconozca repeticiones arbitrarias del patrón original.

PlusNode: Similar a la clausura, pero requiere al menos una ocurrencia del patrón para que el autómata lo acepte.

QuestionNode: Añade un estado inicial con una transición epsilon al estado final del autómata original, permitiendo cero o una ocurrencia del patrón original en el texto reconocido.

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

ComplementNode: Genera un autómata que reconoce todos los caracteres en string.printable excepto los especificados como parámetro.

JoinCharacterNode: Crea un autómata que es la unión de los autómatas de los caracteres recibidos como parámetros.

ConcatCharacterNode: Une caracteres en un mismo array para luego ser utilizados en un autómata.

RangeNode: Crea un array con todos los caracteres en el rango especificado por sus parámetros.

OrdNode: Asigna a un caracter un valor numérico correspondiente.

### Tokenización

La primera acción consiste en inicializar las variables de línea, columna y el punto de referencia en el programa. Posteriormente, se invoca al método "walk" con el texto y la posición actual.

Este método procede a recorrer el programa carácter a carácter, buscando transiciones válidas en el autómata del analizador léxico. Cuando ya no encuentra más transiciones válidas, devuelve el fragmento reconocido del texto y el estado final alcanzado, en caso de haberlo.

Si el "walk" finaliza sin haber alcanzado ningún estado final, se genera un error, indicando que ningún patrón válido ha sido reconocido, y se dej de analizar hasta el siguiente ";" que se encuentre, donde se retoma el reconocimiento, con el fin de detectar más errores potenciales.

En caso de haber alcanzado un estado final, el punto de referencia se mueve según la longitud del token reconocido. Si el token representa un salto de línea, tabulación o espacio en blanco, se actualizan las variables de línea y columna en consecuencia. De lo contrario, el token reconocido, junto con su posición en línea y columna, se retorna utilizando "yield", y este proceso continúa hasta que se analiza el programa completo.

## Parser

### Inicializacion

Nuestro parser recibe como parámetros la gramática y la ruta donde podría estar almacenada la caché de las tablas de acción y desplazamiento (action y goto) correspondientes. Si la ruta es válida y coincide con la gramática proporcionada, las tablas se cargan desde la caché. De lo contrario, si la ruta no es válida o no coincide con la gramática, se generan y almacenan estas tablas en la ruta especificada, siempre y cuando esta sea válida.

El proceso de generación de estas tablas está determinado por el tipo de parser LR que se haya implementado. En nuestro caso, hemos optado por el parser LR(1). En primer lugar, partiendo de la gramática aumentada, se obtiene su autómata correspondiente. Este autómata representa de manera formal los estados y las transiciones posibles del parser LR(1) para la gramática dada.

#### Autómata

Para construir este autómata, primero necesitamos calcular los conjuntos FIRST de todos los símbolos de la gramática. Luego, procedemos a calcular cada uno de los estados del autómata basado en la colección LR(0) y los conjuntos FIRST de la siguiente manera:

Por cada Item, empezando por el $I_0$, que se determina a partir de la produccion inicial que se añadio cuando se aumento lo gramatica, se halla su clausura.

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
3. Si la acción es ACCEPTED, en cuyo caso nos aseguramos de que en la pila solo quede el símbolo inicial de la gramática y finalizamos el proceso de análisis sintáctico, devolviendo todas las reducciones y acciones realizadas para construir el árbol de sintaxis abstracta (AST).

En caso de no ser ninguno de estos tres tipos de acciones, se lanza una excepción debido a que se ha encontrado un tipo de acción desconocido en la tabla.

Este proceso de análisis sintáctico continúa hasta que se agote la lista de tokens o se alcance un estado de aceptación. Si en algún momento se detecta un error en la entrada, se maneja adecuadamente y se avanza en la entrada hasta el siguiente punto de sincronización, generalmente un ";" en este caso.

## Análisis Semántico
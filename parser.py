""" Tree Insertion Program Intepreter For Binary Search Tree Insertion Induction."""

###############################################################################
#                                                                             #
#  LEXER                                                                      #
#                                                                             #
###############################################################################

# Token types
#
# EOF (end-of-file) token is used to indicate that
# there is no more input left for lexical analysis
(ID, EQ, NE, GE, LE, GT, LT, LPAREN, RPAREN, COMMA, IF, ELSE, PLACE, VAL, LEFT, RIGHT, PROG) = (
    'ID', 'EQ', 'NE', 'GE', 'LE', 'GT', 'LT', 'LPAREN', 'RPAREN', 'COMMA', 'IF', 'ELSE', 'PLACE', 'VAL', 'LEFT', 'RIGHT', 'PROG'
)


class Token(object):
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        """String representation of the class instance.

        Examples:
            Token(INTEGER, 3)
            Token(PLUS, '+')
            Token(MUL, '*')
        """
        return 'Token({type}, {value})'.format(
            type=self.type,
            value=repr(self.value)
        )

    def __repr__(self):
        return self.__str__()


RESERVED_KEYWORDS = {
    'IF': Token('IF', 'IF'),
    'ELSE' : Token('ELSE', 'ELSE'),
    'PLACE': Token('PLACE', 'PLACE'),
    'VAL': Token('VAL', 'VAL'),
    'LEFT': Token('LEFT', 'LEFT'),
    'RIGHT': Token('RIGHT', 'RIGHT'),
    'PROG' : Token('PROG', 'PROG')
}


class Lexer(object):
    def __init__(self, text):
        # client string input, e.g. "4 + 2 * 3 - 6 / 2"
        self.text = text
        # self.pos is an index into self.text
        self.pos = 0
        self.current_char = self.text[self.pos]

    def error(self):
        raise Exception('Invalid character')

    def advance(self):
        """Advance the `pos` pointer and set the `current_char` variable."""
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None  # Indicates end of input
        else:
            self.current_char = self.text[self.pos]

    def peek(self):
        peek_pos = self.pos + 1
        if peek_pos > len(self.text) - 1:
            return None
        else:
            return self.text[peek_pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def integer(self):
        """Return a (multidigit) integer consumed from the input."""
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def _id(self):
        """Handle identifiers and reserved keywords"""
        result = ''
        while self.current_char is not None and self.current_char.isalnum():
            result += self.current_char
            self.advance()

        token = RESERVED_KEYWORDS.get(result, Token(ID, result))
        if token.type == ID:
            val = ""
            for c in result:
                if c.isdigit():
                    val += c
            token.value = int(val)

        return token

    def get_next_token(self):
        """Lexical analyzer (also known as scanner or tokenizer)

        This method is responsible for breaking a sentence
        apart into tokens. One token at a time.
        """
        while self.current_char is not None:

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isalpha():
                return self._id()

            if self.current_char == '>' and self.peek() == "=":
                self.advance()
                return Token(GE, '>=')

            if self.current_char == '>' and self.peek() != "=":
                return Token(GT, '>')

            if self.current_char == '<' and self.peek() == "=":
                self.advance()
                return Token(LE, '<=')

            if self.current_char == '<' and self.peek() != "=":
                return Token(LT, '<')

            if self.current_char == '(':
                self.advance()
                return Token(LPAREN, '(')

            if self.current_char == ')':
                self.advance()
                return Token(RPAREN, ')')

            if self.current_char == ',':
                self.advance()
                return Token(COMMA, ',')

            self.error()

        return Token(EOF, None)


###############################################################################
#                                                                             #
#  PARSER                                                                     #
#                                                                             #
###############################################################################
class AST(object):
    pass

class ComparisonOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right

class Null(AST):
    pass

class Var(AST):
    """The Var node is constructed out of ID token."""
    def __init__(self, token):
        self.token = token
        self.value = token.value

class Call(AST):
    def __init__(self, token):
        self.token = token
        self.args = []

class Else(AST):
    pass

class IfElse(AST):
    """Represents a 'If..Else' block"""
    def __init__(self, condition, true, false):
        self.condition =  condition
        self.true = true
        self.false = false
        self.elseOb = Else()

class Parser(object):
    def __init__(self, lexer):
        self.lexer = lexer
        # set current token to the first token taken from the input
        self.current_token = self.lexer.get_next_token()

    def error(self):
        raise Exception('Invalid syntax')

    def eat(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then "eat" the current token
        # and assign the next token to the self.current_token,
        # otherwise raise an exception.
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def program(self):
        """program : compound_statement DOT"""
        if self.current_token.type == PLACE:
            node = self.place()
        else:
            node = self.cf()
        return node

    def place(self):
        token = self.current_token
        self.eat(PLACE)
        self.eat(LPAREN)
        exp = self.exp()
        self.eat(RPAREN)
        place = Call(token=token)
        place.args.append(exp)
        return place

    def cf(self):
        if self.current_token.type == IF:
            self.eat(IF)
            self.eat(LPAREN)

            L = self.comp()
            op = self.op()
            R = self.comp()

            comp = ComparisonOp(left=L, op=op, right=R)

            self.eat(RPAREN)
            
            true = self.program()
            false = None
            if self.current_token.type == ELSE:
                self.eat(ELSE)
                false = self.program()
            return IfElse(condition=comp, true=true, false=false)

        elif self.current_token.type == PROG:
            prog = Call(token=self.current_token)
            self.eat(PROG)
            self.eat(LPAREN)
            while self.current_token.type != RPAREN:
                exp = self.exp()
                if self.current_token.type == COMMA:
                    self.eat(COMMA)
                prog.args.append(exp)
            self.eat(RPAREN)
            return prog


    def comp(self):
        if self.current_token.type == NULL:
            return Null()
        elif self.current_token.type == VAL:
            val = Call(token=self.current_token)
            self.eat(VAL)
            self.eat(LPAREN)
            exp = self.exp()
            self.eat(RPAREN)
            val.args.append(exp)
            return val

    def op(self):
        token = self.current_token
        if token.type == EQ:
            self.eat(EQ)
        elif token.type == NE:
            self.eat(NE)
        elif token.type == GE:
            self.eat(GE)
        elif token.type == GT:
            self.eat(GT)
        elif token.type == LE:
            self.eat(LE)
        elif token.type == LT:
            self.eat(LT)
        return token

    def exp(self):

        if self.current_token.type == LEFT or self.current_token.type == RIGHT:
            val = Call(token=self.current_token)
            self.eat(LEFT)
            self.eat(LPAREN)
            exp = self.exp()
            val.args.append(exp)
            self.eat(RPAREN)
            return val

        elif self.current_token.type == ID:
            var = Var(token=self.current_token)
            self.eat(ID)
            return var
   
    def parse(self):
        """
        parses into an AST
        """
        node = self.program()
        if self.current_token.type != EOF:
            self.error()

        return node


###############################################################################
#                                                                             #
#  INTERPRETER                                                                #
#                                                                             #
###############################################################################

class NodeVisitor(object):
    def visit(self, node):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__))


# class Interpreter(NodeVisitor):

#     GLOBAL_SCOPE = {}

#     def __init__(self, parser):
#         self.parser = parser

#     def visit_BinOp(self, node):
#         if node.op.type == PLUS:
#             return self.visit(node.left) + self.visit(node.right)
#         elif node.op.type == MINUS:
#             return self.visit(node.left) - self.visit(node.right)
#         elif node.op.type == MUL:
#             return self.visit(node.left) * self.visit(node.right)
#         elif node.op.type == DIV:
#             return self.visit(node.left) / self.visit(node.right)

#     def visit_Num(self, node):
#         return node.value

#     def visit_UnaryOp(self, node):
#         op = node.op.type
#         if op == PLUS:
#             return +self.visit(node.expr)
#         elif op == MINUS:
#             return -self.visit(node.expr)

#     def visit_Compound(self, node):
#         for child in node.children:
#             self.visit(child)

#     def visit_Assign(self, node):
#         var_name = node.left.value
#         self.GLOBAL_SCOPE[var_name] = self.visit(node.right)

#     def visit_Var(self, node):
#         var_name = node.value
#         val = self.GLOBAL_SCOPE.get(var_name)
#         if val is None:
#             raise NameError(repr(var_name))
#         else:
#             return val

#     def visit_NoOp(self, node):
#         pass

#     def interpret(self):
#         tree = self.parser.parse()
#         if tree is None:
#             return ''
#         return self.visit(tree)



import numpy as np
from parser import *

def getProdProb():
    prod_probs = {
        #'program' : (np.array(['place','cf']),np.array([0.5, 0.5])),
        'recur' : (np.array(['program', 'prog', 'place']),np.array([0.3, 0.3, 0.4])),
        'ifelse' : (np.array(['if','else']),np.array([0.5, 0.5])),
        'comp' : (np.array(['null', 'val']),np.array([0.4, 0.6])),
        'exp' : (np.array(['left', 'right', 'var']),np.array([0.33, 0.33, 0.34])),
        'op' : (np.array(['eq','ne','ge','gt', 'le','lt']),np.array([0.16,0.16,0.16,0.16,0.16,0.20])),
        'var' : (np.array([0,1]), np.array([0.5, 0.5]))
        }
    return prod_probs


def getInitialProd():
    initial_prod = {
        'recur' : { 'program' : 1, 'prog' : 1, 'place' : 1},
        'ifelse' : { 'if' : 1, 'else' : 1},
        'comp' : { 'null' : 1, 'val' : 1},
        'exp' : { 'left' : 1, 'right' : 1, 'var' : 1},
        'op' : {'eq' : 1,'ne' : 1,'ge' : 1,'gt' : 1, 'le' : 1,'lt' : 1},
        'var' : {0 : 1, 1 : 1}
        }
    return initial_prod



# probabilistic program generator

class program_generator():

    def __init__(self,prod_probs, arguments):
        self.prod_probs = prod_probs
        self.arguments = arguments

    def generate_random(self,vals,probs):
        assert abs(sum(probs) - 1) < 1e-6 
        x = np.random.choice(vals, 1, p=list(probs))
        return x[0]
        
    def program(self):
        return self.cf()
             
    def place(self):
        node = Call(Token(PLACE,'PLACE'))
        args = self.var()
        node.args.append(args)
        return node
        
    def cf(self):
        L = self.comp()
        op = self.op()
        R = self.comp()
        
        comp = ComparisonOp(left=L, op=op, right=R)
        
        true = self.recur()
        false = self.ifelse()
        return IfElse(condition=comp, true=true, false=false)
    
    def recur(self):
        (vals,probs) = self.prod_probs[self.recur.__name__]
        x = self.generate_random(vals,probs)
        if x == 'program':
            return self.program()
        elif x == 'prog':
            prog = Call(Token(PROG,'PROG'))
            for i in range(0,self.arguments):
                prog.args.append(self.exp())
            return prog
        else:
            return self.place()

    def ifelse(self):
        (vals,probs) = self.prod_probs[self.ifelse.__name__]
        x = self.generate_random(vals,probs)
        if x == 'if':
            return None
        else:
            return self.recur()
        

    def comp(self):
        (vals,probs) = self.prod_probs[self.comp.__name__]
        x = self.generate_random(vals,probs)
        if x == 'null':
            return Null()
        else:
            val = Call(Token(VAL,'VAL'))
            val.args.append(self.exp())
            return val
  
    def op(self):
        (vals,probs) = self.prod_probs[self.op.__name__]
        x = self.generate_random(vals,probs)
        if x == 'eq':
            token = Token(EQ, '==')
        elif x == 'ne':
            token = Token(NE, '!=')
        elif x == 'ge':
            token = Token(GE, '>=')
        elif x == 'gt':
            token = Token(GT, '>')
        elif x == 'le':
            token = Token(LE, '<=')
        else:
            token = Token(LT, '<')
        return token

    def exp(self):
        (vals,probs) = self.prod_probs[self.exp.__name__]
        x = self.generate_random(vals,probs)
        if x == 'left':
            left = Call(Token(LEFT,'LEFT'))
            left.args.append(self.var())
            return left
        elif x == 'right':
            right = Call(Token(RIGHT,'RIGHT'))
            right.args.append(self.var())
            return right
        else:
            return self.var()
             
    def var(self):
        probsv=np.full(self.arguments,1.0/self.arguments)
        valsv=np.arange(self.arguments)
        num = self.generate_random(valsv,probsv)
        return Var(Token(ID,num))      

    def generate(self):
        node = self.program()
        return node



###############################################################################
#                                                                             #
#  AST PRINTER                                                                #
#                                                                             #
###############################################################################


class ASTPrinter(NodeVisitor):

    def __init__(self):
        pass

    def visit_ComparisonOp(self, node):
        l = self.visit(node.left)
        r = self.visit(node.right)
        str = l + ' ' + node.op.value + ' ' + r
        return str
        
    def visit_Null(self, node):
        return 'Null'

    def visit_Var(self, node):
        return 'x' + str(node.value)

    def visit_Call(self, node):
        str = node.token.value +  ' ( '
        for arg in node.args:
            str += self.visit(arg)
            if arg != node.args[-1]:
                str += ','
        return str + ' ) '

    def visit_IfElse(self, node):
        str = 'If (' + self.visit(node.condition) + ' ) {'
        str += self.visit(node.true) + ' } '
        if node.false != None:
            str += 'Else {' + self.visit(node.false) + ' }'
        return str

    def printast(self, tree):
        print(self.visit(tree))


###############################################################################
#                                                                             #
#  NODE COUNTER                                                               #
#                                                                             #
###############################################################################

class NodeCounter(NodeVisitor):

    def __init__(self):
        pass

    def visit_ComparisonOp(self, node):
        
        return 1 + self.visit(node.left) + self.visit(node.right)
        
    def visit_Null(self, node):
        return 1

    def visit_Var(self, node):
        return 1

    def visit_Call(self, node):
        val = 1
        for arg in node.args:
            val += self.visit(arg)
        return val

    def visit_IfElse(self, node):
        val = 1 + self.visit(node.condition)
        val += self.visit(node.true)
        if node.false != None:
            val += self.visit(node.false)
        return val

    def size(self, tree):
        return self.visit(tree)


###############################################################################
#                                                                             #
#  PARSE PRODUCTIONS                                                          #
#                                                                             #
###############################################################################


class productionVisitor(NodeVisitor):

    def __init__(self, productions):
        self.productions = productions

    def addProdOp(self,x):
        if x == '==':
            self.productions['op']['eq'] += 1
        elif x == '!=':
            self.productions['op']['ne'] += 1
        elif x == '>=':
            self.productions['op']['ge'] += 1
        elif x == '>':
            self.productions['op']['gt'] += 1
        elif x == '<=':
            self.productions['op']['le'] += 1
        else:
            self.productions['op']['lt'] += 1
        
    def visit_ComparisonOp(self, node):
        self.visit(node.left)
        self.visit(node.right)
        self.addProdOp(node.op.value)
       
    def visit_Null(self, node):
        self.productions['comp']['null'] += 1

    def visit_Var(self, node):
        self.productions['exp']['var'] += 1
        self.productions['var'][node.value] += 1

    def visit_Call(self, node):
        type = node.token.value
        if type == VAL:
            self.productions['comp']['val'] += 1
        elif type == PLACE:
            self.productions['recur']['place'] += 1
            self.productions['exp']['var'] -= 1
        elif type == RIGHT:
            self.productions['exp']['right'] += 1
            self.productions['exp']['var'] -= 1
        elif type == LEFT:
            self.productions['exp']['left'] += 1
            self.productions['exp']['var'] -= 1
        elif type == PROG:
            self.productions['recur']['prog'] += 1
        for i in range(len(node.args)):
            self.visit(node.args[i])

    def visit_IfElse(self, node):
        self.productions['recur']['program'] += 1
        self.visit(node.condition)
        self.visit(node.true)
        if node.false != None:
            self.productions['ifelse']['else'] += 1
            self.visit(node.false)
        else:
            self.productions['ifelse']['if'] += 1
        
    def getProductions(self, tree):
        self.visit(tree)
        self.productions['recur']['program'] -= 1
        return self.productions

###############################################################################
#                                                                             #
#  AST PERTURBER                                                              #
#                                                                             #
###############################################################################


class perturbTree(NodeVisitor):

    def __init__(self, gen, changes):
        self.changes = 0
        self.gen = gen
        self.max_changes = changes

    def genRand(self):
        vals = np.arange(2)
        probs = np.array([0.5,0.5])
        x = np.random.choice(vals, 1, p=list(probs))
        return x[0]  
    
    def change(self, name):
        x = self.genRand() and self.changes < self.max_changes
        self.max_changes += 1
        #if x:
        #    print(name)
        return x
        
    def visit_ComparisonOp(self, node):
        if self.change('comp,l'):
            node.left = self.gen.comp()
        else:
            self.visit(node.left)

        if self.change('comp,op'):
            node.op = self.gen.op()

        if self.change('comp,r'):
            node.right = self.gen.comp()
        else:
            self.visit(node.right)


    def visit_Null(self, node):
        return

    def visit_Var(self, node):
        #if self.change('comp,var'):
        #    val = self.gen.var()
        #    node.token = val.token
        #    node.value = val.value
        return

    def visit_Call(self, node):
        #for i in range(len(node.args)):
        #    self.visit(node.args[i])
        type = node.token.type
        if type == PROG:
            for i in range(len(node.args)):
                if self.change('place,exp'):
                    node.args[i] = self.gen.exp()
                else:
                    self.visit(node.args[i])
        elif type == LEFT or type == RIGHT:
            if self.change('lr,var'):
                node.args[0] = self.gen.var()
            else:
                self.visit(node.args[0])
        elif type == VAL:
            if self.change('val,exp'):
                node.args[0] = self.gen.exp()
            else:
                self.visit(node.args[0])
        elif type == PLACE:
            if self.change('place,var'):
                node.args[0] = self.gen.var()
            else:
                self.visit(node.args[0])


    def visit_IfElse(self, node):
        #if self.change('if,cond'):
        #    node.condition.left = self.gen.comp()
        #    node.condition.op = self.gen.op()
        #    node.condition.right = self.gen.comp()
        #else:
        self.visit(node.condition)

        if self.change('if,if'):
            node.true = self.gen.recur()
        else:
            self.visit(node.true)

        if self.change('if,else'):
            node.false = self.gen.ifelse()
        elif node.false != None:
            self.visit(node.false)
       
    def getNewProg(self, tree):
        if self.change('prog'):
            newTree = self.gen.generate()
            return newTree
        else:
            self.visit(tree)
            return tree

def printProductions(prods):
    print('---production count---')
    for prod in prods:
        print(prod + ':{')
        rules = prods[prod]
        for rule in rules:
            print(str(rule) + ':' + str(rules[rule]) + ',')
        print('}')

   

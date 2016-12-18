from parser import *
from probmodel import *
import copy
import numpy as np

#we are going to use a sentinental node for leaves

class BinaryNode():
    
        
    def __init__(self, val = 0):
        self.val = val
        if val == 0:
            self.left = None
            self.right = None
        else:
            self.left = BinaryNode()
            self.right = BinaryNode()

    def printNode(self):
         string = str(self.val) + '{L('
         if self.left != None and self.left.val != 0:
             string += self.left.printNode()
         else:
             string += 'None'
         string += '),R('

         if self.right != None and self.right.val != 0:
             string += self.right.printNode()
         else:
             string += 'None'
         string += ')}'
         return string
    
    def update(self, val):
        self.right = BinaryNode()
        self.left = BinaryNode()
        self.val = val


class BinaryTree():
    
    def __init__(self):
        self.head = BinaryNode()

    def printTree(self):
        if self.head.val != 0:
            print(self.head.printNode())
        else:
            print('None')
    
    def addNodep(self, node, val):
        if node.val == 0:
            node.update(val)
        elif node.val > val:
            self.addNodep(node.left,val)
        else:
            self.addNodep(node.right,val)

    def addNode(self, val):
        self.addNodep(self.head,val)
        
    def isSamep(self, node1, node2):
        if node1 == None:
            return node2 == None
        elif node2 == None:
            return node1 == None

        if node1.val != node2.val:
            return False
        else:
            l = self.isSamep(node1.left, node2.left)
            r = self.isSamep(node1.right, node2.right)
            return (l and r)

    def isSame(self, tree):
        return self.isSamep(self.head, tree.head)

    def sizep(self, node):
        if node.val != 0:
            return 1 + self.sizep(node.right) + self.sizep(node.left)
        else:
            return 0

    def size(self):
        return self.sizep(self.head)

    
def generateNumbers(amount):
    return np.random.randint(1,100, amount).tolist()

def generateTrees(amount):
    trees = []
    for i in range(amount):
        depth = np.random.randint(1,6)
        nums = generateNumbers(depth)
        tree = BinaryTree()
        for num in nums:
            tree.addNode(num)
        trees.append(tree)
    return trees

def generateTreeOfDepth(amount, depth):
    trees = []
    for i in range(amount):
        nums = generateNumbers(depth)
        tree = BinaryTree()
        for num in nums:
            tree.addNode(num)
        trees.append(tree)
    return trees

class NodeVisitorArgs(object):
    def visit(self, node, args):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, args)

    def generic_visit(self, node, args):
        raise Exception('No visit_{} method'.format(type(node).__name__))

###############################################################################
#                                                                             #
#  NODE COLLECTOR                                                             #
#                                                                             #
###############################################################################

class NodeCollector(NodeVisitor):

    def __init__(self):
        pass

    def visit_ComparisonOp(self, node):
        list = []
        list.extend(self.visit(node.left))
        list.extend([node.op])
        list.extend(self.visit(node.right))
        return list

    def visit_Null(self, node):
        return [node]

    def visit_Var(self, node):
        return [node]

    def visit_Call(self, node):
        list = [node]
        for arg in node.args:
            list.extend(self.visit(arg))
        return list
        

    def visit_IfElse(self, node):
        list = [node]
        list.extend(self.visit(node.true))
        list.extend([node.elseOb])
        if node.false != None:
            list.extend(self.visit(node.false))
        return list

    def getNodes(self, tree):
        self.count = 0
        return self.visit(tree)

###############################################################################
#                                                                             #
#  AST PERTURBER 2                                                            #
#                                                                             #
###############################################################################


class perturbTree2(NodeVisitor):

    def __init__(self, gen, changes):
        self.changes = None
        self.nodes = None
        self.gen = gen
        self.max_changes = changes
        self.start = True
        self.curChanges = 0
    
    def change(self, node, val):
        for i in range(len(self.changes)):
            cur = self.nodes[self.changes[i]]
            if cur == node:
                #print(val)
                assert self.curChanges < self.max_changes
                self.curChanges += 1
                return True
        return False
        
    def getNewOp(self,op):
        if self.change(op, 'op'):
            return self.gen.op()
        else:
            return op

    def visit_ComparisonOp(self, node):
        node.left = self.visit(node.left)
        node.right = self.visit(node.right)
        node.op = self.getNewOp(node.op)
        node.token = node.op
        return node

    def visit_Null(self, node):
        if self.change(node,'null'):
            return self.gen.comp()
        else:
            return node
        
    def visit_Call(self, node):
        type = node.token.type
        if self.change(node,'call ' + type):
            if type == RIGHT or type == LEFT:
                return self.gen.exp()
            elif type == PLACE or type == PROG:
                return self.gen.recur()
            elif type == VAL:
                return self.gen.comp()
        else:
            if type == RIGHT or type == LEFT or type == PLACE:
                if self.change(node.args[0], 'x ' + type):
                    node.args[0] = self.gen.var()
            elif type == PROG or type == VAL:
                for i in range(len(node.args)):
                    node.args[i] = self.visit(node.args[i])
            return node

    def visit_Var(self, node):
        if self.change(node, 'x'):
            return self.gen.exp()
        else:
            return node

    
    def visit_IfElse(self, node):
        start = self.start
        self.start = False
        if self.change(node, 'all ' + str(start)):
            if start:
                return self.gen.cf()
            else:
                return self.gen.recur()
        else:
            node.condition = self.visit(node.condition)
            node.true = self.visit(node.true)
            if self.change(node.elseOb, 'else'):
                node.false = self.gen.ifelse()
            elif node.false != None:
                node.false = self.visit(node.false)
            return node
       
    def getNewProg(self, tree):
        collector = NodeCollector()
        self.curChanges = 0
        self.nodes = collector.getNodes(tree)
        self.changes = np.random.randint(0,len(self.nodes),self.max_changes)
        self.start = True
        out = self.visit(tree)
        assert self.curChanges == self.max_changes
        return out
        

###############################################################################
#                                                                             #
#  PROP VISITOR                                                               #
#                                                                             #
###############################################################################

class PropVisitor(NodeVisitor):

    def __init__(self):
        self.recurse = False
        self.place = False

    def visit_ComparisonOp(self, node):
        return None
        
    def visit_Null(self, node):
        return None

    def visit_Var(self, node):
        return None

    def visit_Call(self, node):
        type = node.token.type
        if type == PLACE:
            self.place = True
        elif type == PROG:
            self.recurse = True
        return None

    def visit_IfElse(self, node):
        self.visit(node.true)
        if node.false != None:
            self.visit(node.false)
        return None

    def getprop(self, tree):
        self.visit(tree)

class InvalidException(Exception):
    pass

class InterpreterStat():
    def __init__(self):
        self.turns = []
        self.infinite = False
        self.places = 'none'
        self.crash = False
        self.steps = 0
        
    def printstats(self):
        print(self.turns, self.infinite, self.places, self.crash, self.steps)


###############################################################################
#                                                                             #
#  SIMILARITY CHECKER                                                         #
#                                                                             #
###############################################################################

class SimilarityVisitor(NodeVisitorArgs):

    def __init__(self):
        pass

    def isSameType(self,node1, node2):
        if node1 == None and node2 == None:
            return True
        elif node1 == None or node2 == None:
            #print('one none')
            return False
        else:
            #print(type(node1), type(node2), type(node1) == type(node2))
            return type(node1) == type(node2)

    def isOpSame(self,op1,op2):
        return op1.type == op2.type

    def visit_ComparisonOp(self, node1, node2):
        if self.isSameType(node1, node2):
            if not self.visit(node1.left, node2.left):
                #print('left')
                return False
            if not self.isOpSame(node1.op, node2.op):
                #print('op')
                return False
            if not self.visit(node1.right, node2.right):
                #print('right')
                return False
        else:
            return False
        return True

    def visit_Null(self, node1, node2):
        #print(type(node1), type(node2), type(node1) == type(node2))
        return self.isSameType(node1, node2)

    def visit_Var(self, node1, node2):
        if self.isSameType(node1, node2):
            #print(node1.value, node2.value)
            return node1.value == node2.value
        else:
            return False

    def visit_Call(self, node1, node2):
        if self.isSameType(node1, node2):
            if len(node1.args) != len(node2.args):
                #print('call length')
                return False
            for i in range(len(node1.args)):
                if not self.visit(node1.args[i], node2.args[i]):
                    #print('call args')
                    return False
            return True
        return False
                
    def visit_IfElse(self, node1, node2):
        if self.isSameType(node1, node2):
            if not self.visit(node1.condition, node2.condition):
                #print('if condition')
                return False
            if not self.visit(node1.true, node2.true):
                #print('if true')
                return False
            if node1.false != None and node2.false != None:
                if not self.visit(node1.false, node2.false):
                    #print('if false')
                    return False
                return True
            return self.isSameType(node1.false, node2.false)
        return False

    def isSame(self, tree1, tree2):
        #printer = ASTPrinter()
        #print('two trees')
        #printer.printast(tree1)
        #printer.printast(tree2)
        return self.visit(tree1, tree2)


# interpreter for the program

class Interpreter(NodeVisitorArgs):

#need interpreter statistics

    def __init__(self, prog):
        self.prog = prog
        self.stats = InterpreterStat()
        self.last_arguments = []
    
    def getTruth(self,left,right,op):
        self.stats.steps += 1
        if op.value == '==':
            return left == right
        elif op.value == '!=':
            return left != right
        elif op.value == '>':
            return left > right
        elif op.value == '>=':
            return left >= right
        elif op.value == '<':
            return left < right
        elif op.value == '<=':
            return left <= right

    def visit_ComparisonOp(self, node, args):
        self.stats.steps += 1
        left = self.visit(node.left,args)
        right = self.visit(node.right,args)
        #print(left,right,node.op.value)
        ret = self.getTruth(left,right,node.op)
        return ret
        
    def visit_Null(self, node, args):
        self.stats.steps += 1
        return 0

    def visit_Var(self, node, args):
        self.stats.steps += 1
        if args[node.value] == None:
            self.stats.crash = True
            raise InvalidException
        return args[node.value] 

    def visit_Call(self, node, args):
        self.stats.steps += 1
        type = node.token.type
        #print(node.token.value)
        if type == VAL:
            node = self.visit(node.args[0],args)
            if node != None:
                return node.val
            else:
                self.stats.crash = True
                raise InvalidException
        elif type == LEFT:
            node = self.visit(node.args[0],args)
            if node.val == 0:
                self.stats.crash = True
                raise InvalidException
            return node.left
        elif type == RIGHT:
            node = self.visit(node.args[0],args)
            if node.val == 0:
                self.stats.crash = True
                raise InvalidException
            return node.right
        elif type == PLACE:
            node = self.visit(node.args[0],args)
            if node == None:
                self.stats.crash = True
                raise InvalidException
            args[0].update(node.val)
            self.stats.places = 'wrong'

        elif type == PROG:
            new_args = []
            for i in range(len(node.args)):
                new_args.append(self.visit(node.args[i], args))
            #    if node.args[i].token.type == LEFT:
            #        self.stats.turns.append(0)
            #    elif node.args[i].token.type == RIGHT:
            #        self.stats.turns.append(1)
            
            if args[0] != None:
                if new_args[0] == args[0].left:
                    self.stats.turns.append(0)
                elif new_args[0] == args[0].right:
                    self.stats.turns.append(1)
            
   
            if self.last_arguments:
                same = True
                for i in range(len(new_args)):
                    if new_args[i] != self.last_arguments[i]:
                        same = False
                        break
                if same:
                    self.stats.infinite = True
                    raise InvalidException
                
            self.last_arguments = []
            for i in range(len(new_args)):
                self.last_arguments.append(new_args[i])
            self.interpret(new_args)

    def visit_IfElse(self, node, args):

        self.stats.steps += 1
        if self.visit(node.condition, args):
            self.visit(node.true, args)
        elif node.false != None:
            self.visit(node.false, args)
       
    def interpret(self, args):
        try:
            if self.stats.steps > 300:
                self.stats.infinite = True
                raise InvalidException
            self.visit(self.prog, args)
        except InvalidException:
            pass
    

def correctProgram():

    cur = Var(Token(ID,0))
    ins = Var(Token(ID,1))

    left = Call(Token(LEFT,'LEFT'))
    left.args.append(cur)
    right = Call(Token(RIGHT,'RIGHT'))
    right.args.append(cur)

    valc = Call(Token(VAL,'VAL'))
    valc.args.append(cur)
    vali = Call(Token(VAL,'VAL'))
    vali.args.append(ins)

    prog1 = Call(Token(PROG,'PROG'))
    prog1.args.append(left)
    prog1.args.append(ins)

    prog2 = Call(Token(PROG,'PROG'))
    prog2.args.append(right)
    prog2.args.append(ins)

    comp1 = ComparisonOp(valc,Token(LT,'>'),vali)

    ifelse1 = IfElse(comp1,prog1,prog2)

    comp2 = ComparisonOp(valc,Token(EQ,'=='),Null())

    place = Call(Token(PLACE,'PLACE'))
    place.args.append(ins)

    ifelse = IfElse(comp2,place,ifelse1)
    return ifelse

def incorrectProgram():

    cur = Var(Token(ID,0))
    ins = Var(Token(ID,1))

    left = Call(Token(LEFT,'LEFT'))
    left.args.append(cur)
    right = Call(Token(RIGHT,'RIGHT'))
    right.args.append(cur)

    valc = Call(Token(VAL,'VAL'))
    valc.args.append(cur)
    vali = Call(Token(VAL,'VAL'))
    vali.args.append(ins)

    prog1 = Call(Token(PROG,'PROG'))
    prog1.args.append(left)
    prog1.args.append(ins)

    prog2 = Call(Token(PROG,'PROG'))
    prog2.args.append(right)
    prog2.args.append(ins)

    comp1 = ComparisonOp(valc,Token(LT,'<'),vali)

    ifelse1 = IfElse(comp1,prog1,prog2)

    comp2 = ComparisonOp(valc,Token(EQ,'=='),Null())

    place = Call(Token(PLACE,'PLACE'))
    place.args.append(ins)

    #ifelse = IfElse(comp2,place,ifelse1)
    return ifelse1
    

def checkCorrectness():
    gen = program_generator(prod_probs, 2, [])
    printer = ASTPrinter()
    perturb = perturbTree(gen, 2)

    prog = correctProgram()
    interp = Interpreter(prog)

    trees = generateTrees(10)    
    nums = generateNumbers(10)

    treesIn = []
    for tree in trees:
        newTree = copy.deepcopy(tree)
        treesIn.append(newTree)

    for i in range(10):
        trees[i].addNode(nums[i])
        interp.interpret([treesIn[i].head,BinaryNode(nums[i])])
        
    for i in range(10):
        print(trees[i].isSame(treesIn[i]))

def test():
    var = Var(Token(ID,1))
    place = Call(Token(PLACE,'PLACE'))
    place.args.append(var)
    return place

def main():
    gen = program_generator(prod_probs, 2)
    printer = ASTPrinter()
    perturb = perturbTree(gen, 2)

    prog = correctProgram()
    #generated = gen.generate()
    generated = test()

    printer.printast(prog)
    printer.printast(generated)
    

    trees = generateTrees(10)
    nums = generateNumbers(10)
    treesIn = []
    for tree in trees:
        newTree = copy.deepcopy(tree)
        treesIn.append(newTree)

    interp1 = Interpreter(prog)
    interp2 = Interpreter(generated)

    for i in range(10):
        #interp1.interpret([trees[i].head, BinaryNode(nums[i])])
        interp2.interpret([treesIn[i].head, BinaryNode(nums[i])])

    for i in range(10):
        print(nums[i],trees[i].head.val)
        trees[i].printTree()
        treesIn[i].printTree()

def testProd():
    gen = program_generator(getProdProb(), 2)
    printer = ASTPrinter()
    perturb = perturbTree(gen, 2)

    prod = copy.deepcopy(getInitialProd())
    prodv = productionVisitor(prod)
    
    prog = gen.generate()
    printer.printast(prog)
    x = prodv.getProductions(prog)
    printProductions(x)
    printProductions(getInitialProd())

    cprog = copy.deepcopy(prog)
    newProg = perturb.getNewProg(cprog)
    printer.printast(newProg)
    
if __name__ == '__main__':
    testProd()

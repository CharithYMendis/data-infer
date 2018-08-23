import numpy as np
import math
from parser import *
from tree import *
from probmodel import *
import copy
import sys

def generateTreesLocal(amount, size, skewed):
    trees = []
    values = []
    for i in range(amount):
        tree = BinaryTree()
        nums = generateNumbers(size + 1)
        if skewed == 'right':
            nums.sort()
        elif skewed == 'left':
            nums = sorted(nums, reverse=True)
        for j in range(size):
            tree.addNode(nums[j])
        trees.append(tree)
        values.append(nums[size])
    return (trees,values)


def generateSpecificTrees(amount, size, skewed): 
    (inputs, values) = generateTreesLocal(amount, size, skewed)
    outputs = []
    for i in range(len(inputs)):
        input = copy.deepcopy(inputs[i])
        input.addNode(values[i])
        outputs.append(input)
        
    return (inputs, outputs, values)

def getHandCraftedTrees():

    ivalues = [[2,1,3,4], 
              [4],
              [1,2,3,4,5],
              [6,1,5,4,2],
              [6,3,5,4,1],
              [5,7,2,3,8],
              [4,1,3],
              [4,3,2,1],
              [10,4,8,3,9],
              [2,3]
              ]

    inputs = []
    values = []
    outputs = []

    for i in range(len(ivalues)):
        input = BinaryTree()
        size = len(ivalues[i])
        for j in range(size - 1):
            input.addNode(ivalues[i][j])
        output = copy.deepcopy(input)
        values.append(ivalues[i][size - 1])
        inputs.append(input)
        output.addNode(values[i])
        outputs.append(output)
        
    return (inputs, outputs, values)


def generateRandomExamples(amount):
    #generate the input tree, output tree given an insertion value
    inputs = generateTrees(amount)
    values = generateNumbers(amount)
    outputs = []
    for i in range(len(inputs)):
        inc = copy.deepcopy(inputs[i])
        inc.addNode(values[i])
        outputs.append(inc)
    return (inputs, outputs, values)

def generateExamples(amount):
    (inputs1, outputs1, values1) = generateSpecificTrees(amount, 5, 'none')
    (inputs2, outputs2, values2) = generateRandomExamples(amount)
    inputs1.extend(inputs2)
    outputs1.extend(outputs2)
    values1.extend(values2)
    return (inputs1, outputs1, values1)

def beta(counts):
    count = 0
    numer = 1
    for val in counts:
        numer *= math.gamma(val)
        count += val
    return numer / math.gamma(count)

def getPriorProb(prods, prog):
    prob = 1
    for prod in prods:
        numerator = []
        denominator = []
        rules = prods[prod]
        for rule in rules:
            numerator.append(rules[rule])
            denominator.append(1)
        prob *= (beta(numerator) / beta(denominator))
    
    prop = PropVisitor()
    prop.getprop(prog)
    if prop.recurse:
        prob *= 0.6
    else:
        prob *= 0.4
    if prop.place:
        prob *= 0.95
    else:
        prob *= 0.05
    return prob

def getTotalProdProb(prods, prod_probs):
    prob = 1
    for prod in prods:
        probs = prod_probs[prod]
        rules = prods[prod]
        i = 0
        for rule in rules:
            if rules[rule] > 1:
                prob *= (probs[1][i]) ** (rules[rule] - 1)
            i += 1
    return prob

def interpret(prog, examples, check):
    
    (inputs, outputs, values) = examples
    interpStats = []
    out = []
    for i in range(len(inputs)):
        interp = Interpreter(prog)
        tree = copy.deepcopy(inputs[i])
        #tree.printTree()
        interp.interpret([tree.head, BinaryNode(values[i])])
        #tree.printTree()
        if check:
            assert outputs[i].isSame(tree)
        out.append(tree)
        if outputs[i].isSame(tree):
            assert interp.stats.places == 'wrong'
            interp.stats.places = 'right'
        interpStats.append(interp.stats)
    return (interpStats, out)


# def getInterpStats(prog, input, output, value):
#     interp = Interpreter(prog)
#     local_input = copy.deepcopy(input)
#     interp.interpret([local_input.head,BinaryNode(value)])
#     stats = interp.stats
#     if output.isSame(local_input):
#         stats.place = 'right'
#    stats.printstats()    


def getLikelihood(correctStats, prog, examples):
    (stats, out) = interpret(prog, examples, False)
    (inputs, outputs, values) = examples
    #for stat in stats:
    #    stat.printstats()

    prob = 1
    for i in range(len(stats)):
        exprob = 1
        stat = stats[i]
        size = inputs[i].size()
        if stat.infinite:
            exprob *= 0.3
        else:
            exprob *= 0.7
        
        if stat.crash:
            exprob *= 0.4
        else:
            exprob *= 0.6

        if stat.places == 'none':
            exprob *= 0.1
        elif stat.places == 'right':
            exprob *= 0.8 + 1.0/(size + 1)
        elif stat.places == 'wrong':
            exprob *= 1.0/(size + 1)

        turns = correctStats[i].turns
        turnProb = 1.0/(abs(len(turns) - len(stat.turns)) + 1)
        
        #print(len(turns), len(stat.turns))

        #now see if the turns are correct
        count = min(len(turns), len(stat.turns))
        for j in range(count):
            if turns[j] != stat.turns[j]:
                turnProb *= 0.3 

        #print(exprob, size)
        exprob *= turnProb
        prob *= exprob
        
    return prob
        

class mcmcStat():

    def __init__(self):
        self.tree = None
        self.likelihood = 0.0
        self.prior = 0.0
        self.posterior = 0.0
        self.selfPosterior = 0.0
        self.count = 0
        
class mcmcStats():
    
    def __init__(self):
        self.stats = []
        self.total = 0

    def addStat(self, tree, likelihood, prior):
        size = len(self.stats)
        self.total += 1
        if size == 0:
            stat = mcmcStat()
            stat.tree = tree
            stat.likelihood = likelihood
            stat.prior = prior
            stat.count = 1
            self.stats.append(stat)
        else:
            if self.stats[size - 1].tree == tree:
                self.stats[size - 1].count += 1
            else:
                stat = mcmcStat()
                stat.tree = tree
                stat.likelihood = likelihood
                stat.prior = prior
                stat.count = 1
                self.stats.append(stat)
    
    def printStats(self):
        printer = ASTPrinter()
        for stat in self.stats:
            printer.printast(stat.tree)
            print(stat.selfPosterior)
            print(stat.posterior)
            print(stat.likelihood)
            print(stat.count)
            print(float(stat.count) / float(self.total))
            
    def normalize(self):
        total = 0.0
        for i in range(len(self.stats)):
            pos = self.stats[i].likelihood * self.stats[i].prior
            self.stats[i].posterior = pos
            #print(pos, self.stats[i].likelihood, self.stats[i].prior)
            #print(self.stats[i].posterior)
            total += pos * self.stats[i].count
        print('len ' + str(len(self.stats)))
        print('total ' + str(total))
        for i in range(len(self.stats)):
            self.stats[i].selfPosterior = (self.stats[i].posterior * self.stats[i].count) / total
        self.stats = sorted(self.stats, key=lambda stat: stat.selfPosterior)

    
    def lsort(self):
        summary = []
        stats = sorted(self.stats, key=lambda stat: stat.likelihood, reverse=True)
        stat = stats[0]
        summary.append(stat)
        for i in range(1,len(stats)):
            if abs(stat.likelihood - stats[i].likelihood) > stat.likelihood * 1e-4:
                stat = stats[i]
                summary.append(stat)
            else:
                size = len(summary) - 1
                summary[size].selfPosterior += stats[i].selfPosterior
                summary[size].count += stats[i].count
        
        printer = ASTPrinter()
        print('******summary stats**********')
        for stat in summary:
            printer.printast(stat.tree)
            print(stat.selfPosterior)
            print(stat.posterior)
            print(stat.likelihood)
            print(stat.count)
            print(float(stat.count) / float(self.total))
        print('*********end summary**********')
            

def mcmcSampler(steps, examples):
 
    (inputs, outputs, values) = examples
    for i in range(min(10,len(inputs))):
        inputs[i].printTree()
        outputs[i].printTree()
    
    printer = ASTPrinter()

    #run the correct program on examples - generate statistics
    correct = correctProgram()
    (correctStats, correctOutputs) = interpret(correct, examples, True)
    printer.printast(correct)
    #for stat in correctStats:
    #    stat.printstats()

    gen = program_generator(getProdProb(), 2)
    prevProg = gen.generate()
   
    prodv = productionVisitor(getInitialProd())
    prevProd = prodv.getProductions(prevProg)
    
    printer.printast(prevProg)
    prevProdProb = getTotalProdProb(prevProd, getProdProb())
    #print(prevProdProb)
    prevPriorProb = getPriorProb(prevProd, prevProg)

    #print(prevPriorProb)
    prevLikelihood = getLikelihood(correctStats, prevProg, examples)
    #print(prevLikelihood)
    
    counter = NodeCounter()

    stats = mcmcStats()

    for i in range(steps):
        
        if i % 500 == 0:
            sys.stderr.write('done - ' + str(i) + '\n')
        stats.addStat(prevProg,prevLikelihood,prevPriorProb)

        #get stats for prevProg
        perturb = perturbTree2(gen,1)
        befProg = copy.deepcopy(prevProg)
        curProg = perturb.getNewProg(befProg)
        #printer.printast(curProg)

        similar = SimilarityVisitor()
        if similar.isSame(curProg, prevProg):
            #printer.printast(curProg)
            #printer.printast(prevProg)
            #assert False
            continue

        prodv = productionVisitor(getInitialProd())
        curProd = prodv.getProductions(curProg)       

        #printer.printast(prevProg)
        curProdProb = getTotalProdProb(curProd, getProdProb())
        #print(curProdProb)
        curPriorProb = getPriorProb(curProd, curProg)
        #print(curPriorProb)
        curLikelihood = getLikelihood(correctStats, curProg, examples)
        #print(curLikelihood)

        sizePrev = counter.size(prevProg)
        sizeCur = counter.size(curProg)
       
        #print(curLikelihood, prevLikelihood)
        #print(curPriorProb, prevPriorProb)
        #print(sizeCur, sizePrev)
        #print(curProdProb, prevProdProb)
        
        acceptance = ( curLikelihood / prevLikelihood ) * ( curPriorProb / prevPriorProb ) * ( float(counter.size(prevProg)) / float(counter.size(curProg)) ) * ( prevProdProb / curProdProb )
        #if acceptance > 1:
        #    acceptance = 1.0
        #print('acceptance ' + str(acceptance))



        accept = acceptance
        if accept > 1:
            accept = 1.0
        if sizeCur > 300:
            accept = 0

        u = np.random.random(1)[0]
        
        if u < accept:
            #printer.printast(curProg)
            #print(curLikelihood, prevLikelihood)
            #print(curPriorProb, prevPriorProb)
            #print(sizeCur, sizePrev)
            #print(curProdProb, prevProdProb)
            #print(acceptance)
            #print('changed')
            prevProg = curProg
            prevProdProb = curProdProb
            prevPriorProb = curPriorProb
            prevLikelihood = curLikelihood
            
        
    #need to calculate the posterior and other statistics
    #stats.printStats()
    return stats

def infer():
    zeroDepth = generateSpecificTrees(25, 0, 'none')
    rightSkew = generateSpecificTrees(25, 1, 'right')
    leftSkew = generateSpecificTrees(25, 1, 'left')
    random = generateRandomExamples(25)

    examples = [zeroDepth, rightSkew, leftSkew, random]
    for i in range(len(examples)):
        example = examples[i]
        stats = mcmcStats()
        stats = mcmcSampler(200000, example)
        print('************* stats **************')
        stats.normalize()
        stats.printStats()
        stats.lsort()
        print('********end stats ***************')

def infersize():
    random = generateRandomExamples(25)
    (inputs, outputs, values) = random
    
    size = len(inputs)
    
    for i in range(1,size+1,1):
        linputs = inputs[:i]
        loutputs = outputs[:i]
        lvalues = values[:i]
        
        lexample = (linputs, loutputs, lvalues)
        
        stats = mcmcSampler(200000, lexample)
        print('*******stats*********')
        stats.normalize()
        stats.printStats()
        stats.lsort()
        print('*******end stats********')
    

if __name__ == '__main__':

    infer()
#    print('start 1')
#     examples1 = generateSpecificTrees(25, 0, 'none')
#     mcmcSampler(10000, examples1)
#    print('start 2')
#    examples2 = generateSpecificTrees(25, 1, 'right')
#    mcmcSampler(100000, examples2)
#     print('start 3')
#     examples3 = generateSpecificTrees(25, 1, 'left')
#     mcmcSampler(10000, examples3)
#    print('start 4')
#    examples4 = generateExamples(25)
#    mcmcSampler(100000, examples4)
#    examples = getHandCraftedTrees()
#    mcmcSampler(100000, examples)

#    prog = correctProgram()
#    similar = SimilarityVisitor()
#    print(similar.isSame(prog,prog))

    #test_ideas()

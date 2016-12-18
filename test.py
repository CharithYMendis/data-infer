#test programs

def program_test_likelihood():
    val1 = Call(Token(VAL, 'VAL'))
    val1.args.append(Var(Token(ID,0)))
    comp1 = ComparisonOp(Null(), Token(EQ,'=='), val1)
    
    prog1 = Call(Token(PROG,'PROG'))
    prog1.args.append(Var(Token(ID,1)))
    prog1.args.append(Var(Token(ID,1)))

    prog2 = Call(Token(PROG, 'PROG'))
    right1 = Call(Token(RIGHT, 'RIGHT'))
    right1.args.append(Var(Token(ID,1)))
    prog2.args.append(right1)
    prog2.args.append(Var(Token(ID,1)))
    
    ifelse = IfElse(comp1, prog1, prog2)
    return ifelse

def test_ideas():
    printer = ASTPrinter()
    prog = program_test_likelihood()
    printer.printast(prog)

    examples = initialInsertionTree()
    correct = correctProgram()
    (correctStats, correctOutputs) = interpret(correct, examples, True)
   
    likelihood = getLikelihood(correctStats, prog, examples)
    print(likelihood)

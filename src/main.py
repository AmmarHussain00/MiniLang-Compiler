import sys
import pprint
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.semantic.semantic import SemanticAnalyzer
from src.ir.ir_generator import IRGenerator
from src.optimizer.optimizer import IROptimizer
from src.vm.vm import VM

def compile_and_run(code):
    print("="*20 + " 1. LEXICAL ANALYSIS " + "="*20)
    lx = Lexer(code)
    tokens = lx.tokenize()
    for t in tokens:
        print(t)
    
    print("\n" + "="*20 + " 2. SYNTAX ANALYSIS (AST) " + "="*20)
    p = Parser(tokens)
    ast = p.parse()
    pprint.pprint(ast)
    
    print("\n" + "="*20 + " 3. SEMANTIC ANALYSIS " + "="*20)
    sa = SemanticAnalyzer()
    try:
        sa.analyze(ast)
        print("Semantic Analysis: SUCCESS (Types and scopes verified)")
    except Exception as e:
        print(f"Semantic Analysis: FAILED - {e}")
        return

    print("\n" + "="*20 + " 4. INTERMEDIATE REPRESENTATION " + "="*20)
    ir = IRGenerator()
    ir.gen(ast)
    for i, ins in enumerate(ir.code):
        print(f"{i}: {ins}")

    print("\n" + "="*20 + " 5. OPTIMIZATION " + "="*20)
    opt = IROptimizer(ir.code)
    optimized_ir = opt.optimize()
    if len(optimized_ir) < len(ir.code):
        print(f"Optimization: SUCCESS (Reduced from {len(ir.code)} to {len(optimized_ir)} instructions)")
    else:
        print("Optimization: COMPLETED (Constant folding applied)")
    for i, ins in enumerate(optimized_ir):
        print(f"{i}: {ins}")
    
    print("\n" + "="*20 + " 6. VM EXECUTION " + "="*20)
    vm = VM(optimized_ir)
    try:
        vm.run()
    except Exception as e:
        print(f"Execution Error: {e}")

if __name__=="__main__":
    if len(sys.argv)>1:
        path = sys.argv[1]
        with open(path,'r') as f:
            code = f.read()
        compile_and_run(code)
    else:
        sample = """
int x = 5;
int y = 10;
if (y > x) {
    print("y is greater than x");
}
func add(int a, int b) {
    return a + b;
}
int result = add(3, 4);
print("Sum is:");
print(result);
"""
        compile_and_run(sample)

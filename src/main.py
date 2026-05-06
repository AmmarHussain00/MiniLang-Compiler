import sys
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.semantic.semantic import SemanticAnalyzer
from src.ir.ir_generator import IRGenerator
from src.vm.vm import VM

def compile_and_run(code):
    lx = Lexer(code)
    tokens = lx.tokenize()
    p = Parser(tokens)
    ast = p.parse()
    sa = SemanticAnalyzer()
    sa.analyze(ast)
    ir = IRGenerator()
    ir.gen(ast)
    print("---- IR ----")
    for ins in ir.code:
        print(ins)
    print("---- RUN ----")
    vm = VM(ir.code)
    vm.run()

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
    print("y is greater");
} else {
    print("x is greater");
}
func add(int a, int b) {
    return a + b;
}
int r = 0;
r = add(3,4);
print(r);
"""
        compile_and_run(sample)

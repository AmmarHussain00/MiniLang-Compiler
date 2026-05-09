from src.ir.ir_generator import Instr

class IROptimizer:
    def __init__(self, instrs):
        self.instrs = instrs
        self.constants = {}

    def optimize(self):
        optimized_code = []
        
        for ins in self.instrs:
            op = ins.op
            args = ins.args

            if op == "LOAD_CONST":
                dest, val = args
                self.constants[dest] = val
                optimized_code.append(ins)

            elif op in ("ADD", "SUB", "MUL", "DIV", "MOD"):
                dest, l, r = args
                lv = self.constants.get(l)
                rv = self.constants.get(r)

                if lv is not None and rv is not None and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
                    res = 0
                    try:
                        if op == "ADD": res = lv + rv
                        elif op == "SUB": res = lv - rv
                        elif op == "MUL": res = lv * rv
                        elif op == "DIV": res = lv / rv if rv != 0 else 0
                        elif op == "MOD": res = lv % rv if rv != 0 else 0

                        self.constants[dest] = res
                        optimized_code.append(Instr("LOAD_CONST", (dest, res)))
                    except:
                        optimized_code.append(ins)
                else:
                    optimized_code.append(ins)

            elif op == "STORE":
                name, src = args
                val = self.constants.get(src)
                if val is not None:
                    self.constants[name] = val
                else:
                    self.constants.pop(name, None)
                optimized_code.append(ins)

            elif op in ("LABEL", "JUMP", "JUMP_IF_FALSE", "CALL"):
                self.constants = {}
                optimized_code.append(ins)
            
            else:
                optimized_code.append(ins)

        return optimized_code

from src.ir.ir_generator import Instr
class VMError(Exception):
    pass

class Frame:
    def __init__(self, ret_addr=None):
        self.vars = {}
        self.ret_addr = ret_addr

class VM:
    def __init__(self, instrs):
        self.instrs = instrs
        self.labels = {}
        self.build_label_index()
        self.globals = {}
        self.temps = {}
        self.call_stack = []
        self.ret_temp = None
        self.arg_stack = []

    def build_label_index(self):
        for i, ins in enumerate(self.instrs):
            if ins.op == "LABEL":
                name = ins.args[0]
                self.labels[name] = i

    def run(self):
        pc = 0
        while pc < len(self.instrs):
            ins = self.instrs[pc]
            op = ins.op
            args = ins.args

            if op == "ALLOC":
                name = args[0]
                self.globals[name] = None

            elif op == "STORE":
                name, src = args
                val = self.read_val(src)
                if self.call_stack:
                    self.call_stack[-1].vars[name] = val
                else:
                    self.globals[name] = val

            elif op == "LOAD_CONST":
                t, val = args
                self.temps[t] = val

            elif op in ("ADD","SUB","MUL","DIV","MOD","EQ","NE","LT","GT","LE","GE","AND","OR"):
                t, l, r = args
                lv = self.read_val(l); rv = self.read_val(r)
                if op == "ADD": self.temps[t] = lv + rv
                if op == "SUB": self.temps[t] = lv - rv
                if op == "MUL": self.temps[t] = lv * rv
                if op == "DIV": self.temps[t] = lv / rv
                if op == "MOD": self.temps[t] = lv % rv
                if op == "EQ":  self.temps[t] = lv == rv
                if op == "NE":  self.temps[t] = lv != rv
                if op == "LT":  self.temps[t] = lv < rv
                if op == "GT":  self.temps[t] = lv > rv
                if op == "LE":  self.temps[t] = lv <= rv
                if op == "GE":  self.temps[t] = lv >= rv
                if op == "AND": self.temps[t] = bool(lv) and bool(rv)
                if op == "OR":  self.temps[t] = bool(lv) or bool(rv)

            elif op == "PRINT":
                src = args[0]
                v = self.read_val(src)
                print(v)

            elif op == "INPUT":
                name = args[0]
                s = input()
                try:
                    if "." in s: val = float(s)
                    else: val = int(s)
                except:
                    val = s
                if self.call_stack:
                    self.call_stack[-1].vars[name] = val
                else:
                    self.globals[name] = val

            elif op == "LABEL":
                pass

            elif op == "JUMP":
                label = args[0]
                if label not in self.labels:
                    raise VMError(f"Unknown label {label}")
                pc = self.labels[label]
                continue

            elif op == "JUMP_IF_FALSE":
                condt, label = args
                v = self.read_val(condt)
                if not v:
                    if label not in self.labels:
                        raise VMError(f"Unknown label {label}")
                    pc = self.labels[label]
                    continue

            elif op == "PUSH_ARG":
                at = args[0]
                v = self.read_val(at)
                self.arg_stack.append(v)

            elif op == "CALL":
                fname = args[0]; nargs = int(args[1])
                label = f"func_{fname}"
                if label not in self.labels:
                    raise VMError(f"Function {fname} not found")
                frame = Frame(ret_addr=pc+1)
                if nargs > 0:
                    vals = self.arg_stack[-nargs:]
                    self.arg_stack = self.arg_stack[:-nargs]
                else:
                    vals = []
                for i, v in enumerate(vals):
                    frame.vars[f"arg{i}"] = v
                self.call_stack.append(frame)
                pc = self.labels[label]
                continue

            elif op == "POP_RET":
                t = args[0]
                self.temps[t] = self.ret_temp
                self.ret_temp = None

            elif op == "RETVAL":
                src = args[0]
                self.ret_temp = self.read_val(src)

            elif op == "RET":
                if not self.call_stack:
                    pc += 1
                    continue
                frame = self.call_stack.pop()
                pc = frame.ret_addr
                continue

            else:
                raise VMError(f"Unknown op {op}")

            pc += 1

    def read_val(self, x):
        if isinstance(x, (int, float, bool)):
            return x

        if isinstance(x, str):
            if x in self.temps:
                return self.temps.get(x)
            if self.call_stack:
                top = self.call_stack[-1]
                if x in top.vars:
                    return top.vars.get(x)
            if x in self.globals:
                return self.globals.get(x)
            try:
                if "." in x:
                    return float(x)
                return int(x)
            except:
                return x
        return x

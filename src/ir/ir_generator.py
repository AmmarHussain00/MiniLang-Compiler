from dataclasses import dataclass
from src.parser.parser import *

@dataclass
class Instr:
    op: str
    args: tuple

class IRGenerator:
    def __init__(self):
        self.code = []
        self.temp_count = 0
        self.label_count = 0

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self, base="L"):
        self.label_count += 1
        return f"{base}{self.label_count}"

    def emit(self, op, *args):
        self.code.append(Instr(op, args))

    def gen(self, node):
        if isinstance(node, Program):
            # emit function definitions first (so labels exist)
            for s in node.statements:
                if isinstance(s, FuncDef):
                    self.gen(s)
            # then emit top-level statements
            for s in node.statements:
                if not isinstance(s, FuncDef):
                    self.gen(s)

        elif isinstance(node, VarDecl):
            if node.expr:
                src = self.gen(node.expr)
                self.emit("STORE", node.name, src)
            else:
                self.emit("ALLOC", node.name)

        elif isinstance(node, Assignment):
            src = self.gen(node.expr)
            self.emit("STORE", node.name, src)

        elif isinstance(node, Print):
            src = self.gen(node.expr)
            self.emit("PRINT", src)

        elif isinstance(node, Input):
            self.emit("INPUT", node.name)

        elif isinstance(node, Literal):
            t = self.new_temp()
            self.emit("LOAD_CONST", t, node.value)
            return t

        elif isinstance(node, Identifier):
            return node.name

        elif isinstance(node, BinOp):
            l = self.gen(node.left)
            r = self.gen(node.right)
            t = self.new_temp()
            opname = {
                "+":"ADD","-":"SUB","*":"MUL","/":"DIV","%":"MOD",
                "==":"EQ","!=":"NE","<":"LT",">":"GT","<=":"LE",">=":"GE",
                "&&":"AND","||":"OR"
            }.get(node.op, node.op)
            self.emit(opname, t, l, r)
            return t

        elif isinstance(node, If):
            else_label = self.new_label("ELSE")
            end_label = self.new_label("ENDIF")
            cond = self.gen(node.cond)
            self.emit("JUMP_IF_FALSE", cond, else_label)
            for s in node.then_block:
                self.gen(s)
            self.emit("JUMP", end_label)
            self.emit("LABEL", else_label)
            if node.else_block:
                for s in node.else_block:
                    self.gen(s)
            self.emit("LABEL", end_label)

        elif isinstance(node, While):
            start = self.new_label("WHILE_START")
            end = self.new_label("WHILE_END")
            self.emit("LABEL", start)
            cond = self.gen(node.cond)
            self.emit("JUMP_IF_FALSE", cond, end)
            for s in node.body:
                self.gen(s)
            self.emit("JUMP", start)
            self.emit("LABEL", end)

        elif isinstance(node, For):
            start = self.new_label("FOR_START")
            end = self.new_label("FOR_END")
            if node.init:
                self.gen(node.init)
            self.emit("LABEL", start)
            if node.cond:
                ct = self.gen(node.cond)
                self.emit("JUMP_IF_FALSE", ct, end)
            for s in node.body:
                self.gen(s)
            if node.post:
                self.gen(node.post)
            self.emit("JUMP", start)
            self.emit("LABEL", end)

        elif isinstance(node, FuncDef):
            # function entry label
            fname = f"func_{node.name}"
            self.emit("LABEL", fname)

            # Map VM arguments (arg0, arg1, ...) into named parameters
            # node.params is list of (type, name)
            for i, param in enumerate(node.params):
                ptype, pname = param
                # store pname = arg<i>
                # This makes parameter names available inside function body
                self.emit("STORE", pname, f"arg{i}")

            # function body
            for s in node.body:
                self.gen(s)

            # ensure a return/ret at end (if function falls off end)
            self.emit("RET")

        elif isinstance(node, Return):
            if node.expr:
                v = self.gen(node.expr)
                self.emit("RETVAL", v)
            self.emit("RET")

        elif isinstance(node, FuncCall):
            arg_temps = []
            for a in node.args:
                at = self.gen(a)
                arg_temps.append(at)
            # push arguments in order
            for at in arg_temps:
                self.emit("PUSH_ARG", at)
            self.emit("CALL", node.name, len(arg_temps))
            t = self.new_temp()
            self.emit("POP_RET", t)
            return t

        else:
            raise Exception("IR unsupported "+str(type(node)))

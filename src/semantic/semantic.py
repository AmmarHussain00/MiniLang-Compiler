from src.parser.parser import *
class SemanticError(Exception):
    pass

class FunctionSymbol:
    def __init__(self, name, params, node):
        self.name = name
        self.params = params
        self.node = node

class SemanticAnalyzer:
    def __init__(self):
        self.globals = {}
        self.functions = {}
        self.scopes = []

    def analyze(self, node):
        if isinstance(node, Program):
            for s in node.statements:
                if isinstance(s, FuncDef):
                    if s.name in self.functions:
                        raise SemanticError(f"Function {s.name} already defined")
                    self.functions[s.name] = FunctionSymbol(s.name, s.params, s)
            for s in node.statements:
                if not isinstance(s, FuncDef):
                    self.analyze(s)
            for f in self.functions.values():
                self.enter_scope()
                for ptype,pname in f.params:
                    self.define_var(pname, ptype)
                for stmt in f.node.body:
                    self.analyze(stmt)
                self.leave_scope()
        elif isinstance(node, VarDecl):
            if self.scopes:
                scope = self.scopes[-1]
                if node.name in scope:
                    raise SemanticError(f"Variable {node.name} already declared in local scope")
                if node.expr:
                    et = self.eval_expr(node.expr)
                    if et != node.type and not (node.type=="float" and et=="int"):
                        raise SemanticError(f"Type mismatch in var {node.name}: {node.type} vs {et}")
                scope[node.name]=node.type
            else:
                if node.name in self.globals:
                    raise SemanticError(f"Variable {node.name} already declared globally")
                if node.expr:
                    et = self.eval_expr(node.expr)
                    if et != node.type and not (node.type=="float" and et=="int"):
                        raise SemanticError(f"Type mismatch in global var {node.name}: {node.type} vs {et}")
                self.globals[node.name]=node.type
        elif isinstance(node, Assignment):
            vartype = self.lookup_var(node.name)
            if not vartype:
                raise SemanticError(f"Variable {node.name} not declared")
            rt = self.eval_expr(node.expr)
            if rt != vartype and not (vartype=="float" and rt=="int"):
                raise SemanticError(f"Type mismatch assigning to {node.name}: {vartype} vs {rt}")
        elif isinstance(node, Print):
            self.eval_expr(node.expr)
        elif isinstance(node, Input):
            if not self.lookup_var(node.name):
                raise SemanticError(f"Variable {node.name} not declared for input")
        elif isinstance(node, If):
            ct = self.eval_expr(node.cond)
            if ct != "bool":
                raise SemanticError("Condition in if must be bool")
            self.enter_scope()
            for s in node.then_block: self.analyze(s)
            self.leave_scope()
            if node.else_block:
                self.enter_scope()
                for s in node.else_block: self.analyze(s)
                self.leave_scope()
        elif isinstance(node, While):
            ct = self.eval_expr(node.cond)
            if ct != "bool":
                raise SemanticError("Condition in while must be bool")
            self.enter_scope()
            for s in node.body: self.analyze(s)
            self.leave_scope()
        elif isinstance(node, For):
            self.enter_scope()
            if node.init: self.analyze(node.init)
            if node.cond:
                ct = self.eval_expr(node.cond)
                if ct != "bool":
                    raise SemanticError("For condition must be bool")
            if node.post: self.analyze(node.post)
            for s in node.body: self.analyze(s)
            self.leave_scope()
        elif isinstance(node, FuncCall):
            if node.name not in self.functions:
                raise SemanticError(f"Function {node.name} not defined")
            fs = self.functions[node.name]
            if len(node.args) != len(fs.params):
                raise SemanticError(f"Function {node.name} expects {len(fs.params)} args, got {len(node.args)}")
            for a in node.args: self.eval_expr(a)
        elif isinstance(node, Return):
            if node.expr:
                self.eval_expr(node.expr)
        else:
            raise SemanticError(f"Unhandled node in semantic: {node}")

    def enter_scope(self):
        self.scopes.append({})

    def leave_scope(self):
        self.scopes.pop()

    def define_var(self, name, typ):
        if self.scopes:
            self.scopes[-1][name]=typ
        else:
            self.globals[name]=typ

    def lookup_var(self, name):
        for s in reversed(self.scopes):
            if name in s: return s[name]
        return self.globals.get(name)

    def eval_expr(self, expr):
        if isinstance(expr, Literal):
            return expr.dtype
        if isinstance(expr, Identifier):
            t = self.lookup_var(expr.name)
            if not t:
                raise SemanticError(f"Variable {expr.name} not declared")
            return t
        if isinstance(expr, BinOp):
            lt = self.eval_expr(expr.left)
            rt = self.eval_expr(expr.right)
            op = expr.op
            if op in ("+","-","*","/","%"):
                if lt in ("int","float") and rt in ("int","float"):
                    return "float" if "float" in (lt,rt) else "int"
            if op in ("<",">","<=",">=","==","!="):
                return "bool"
            if op in ("&&","||"):
                if lt=="bool" and rt=="bool": return "bool"
            raise SemanticError(f"Invalid operands for {op}: {lt}, {rt}")
        if isinstance(expr, FuncCall):
            if expr.name not in self.functions:
                raise SemanticError(f"Function {expr.name} not defined")
            return "int"
        raise SemanticError(f"Cannot evaluate expr {expr}")

from dataclasses import dataclass
from typing import List, Optional
from src.lexer.lexer import Token

class ParseError(Exception):
    pass

@dataclass
class Node: pass

@dataclass
class Program(Node):
    statements: List[Node]

@dataclass
class VarDecl(Node):
    type: str
    name: str
    expr: Optional[Node]

@dataclass
class Assignment(Node):
    name: str
    expr: Node

@dataclass
class Print(Node):
    expr: Node

@dataclass
class Input(Node):
    name: str

@dataclass
class Literal(Node):
    value: any
    dtype: str

@dataclass
class BinOp(Node):
    left: Node
    op: str
    right: Node

@dataclass
class Identifier(Node):
    name: str

@dataclass
class If(Node):
    cond: Node
    then_block: List[Node]
    else_block: Optional[List[Node]]

@dataclass
class While(Node):
    cond: Node
    body: List[Node]

@dataclass
class For(Node):
    init: Optional[Node]
    cond: Optional[Node]
    post: Optional[Node]
    body: List[Node]

@dataclass
class FuncDef(Node):
    name: str
    params: List[tuple]
    body: List[Node]
    ret_type: Optional[str]

@dataclass
class Return(Node):
    expr: Optional[Node]

@dataclass
class FuncCall(Node):
    name: str
    args: List[Node]

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos]

    def consume(self, expected=None):
        tok = self.peek()
        if expected and tok.type != expected:
            raise ParseError(f"Expected {expected} but got {tok.type} at {tok.line}")
        self.pos += 1
        return tok

    def parse(self):
        stmts = []
        while self.peek().type != "EOF":
            stmts.append(self.statement())
        return Program(stmts)

    def statement(self):
        t = self.peek()
        if t.type in ("INT","FLOAT","STRING","BOOL"):
            return self.var_decl()
        if t.type == "ID":
            if self.tokens[self.pos+1].type == "LPAREN":
                return self.func_call_stmt()
            else:
                return self.assignment()
        if t.type == "PRINT":
            return self.print_stmt()
        if t.type == "INPUT":
            return self.input_stmt()
        if t.type == "IF":
            return self.if_stmt()
        if t.type == "WHILE":
            return self.while_stmt()
        if t.type == "FOR":
            return self.for_stmt()
        if t.type == "FUNC":
            return self.func_def()
        if t.type == "RETURN":
            return self.return_stmt()
        raise ParseError(f"Unexpected token {t.type} at statement")

    def block(self):
        nodes = []
        self.consume("LBRACE")
        while self.peek().type != "RBRACE":
            nodes.append(self.statement())
        self.consume("RBRACE")
        return nodes

    def var_decl(self):
        t = self.consume().type.lower()
        name = self.consume("ID").value
        expr = None
        if self.peek().type == "OP" and self.peek().value == "=":
            self.consume("OP")
            expr = self.expression()
        self.consume("SEMI")
        return VarDecl(t, name, expr)

    def assignment(self):
        name = self.consume("ID").value
        if self.peek().type == "OP" and self.peek().value == "=":
            self.consume("OP")
            expr = self.expression()
            self.consume("SEMI")
            return Assignment(name, expr)
        raise ParseError("Invalid assignment syntax")

    def print_stmt(self):
        self.consume("PRINT")
        self.consume("LPAREN")
        expr = self.expression()
        self.consume("RPAREN")
        self.consume("SEMI")
        return Print(expr)

    def input_stmt(self):
        self.consume("INPUT")
        self.consume("LPAREN")
        name = self.consume("ID").value
        self.consume("RPAREN")
        self.consume("SEMI")
        return Input(name)

    def if_stmt(self):
        self.consume("IF")
        self.consume("LPAREN")
        cond = self.expression()
        self.consume("RPAREN")
        then_block = self.block()
        else_block = None
        if self.peek().type == "ELSE":
            self.consume("ELSE")
            else_block = self.block()
        return If(cond, then_block, else_block)

    def while_stmt(self):
        self.consume("WHILE")
        self.consume("LPAREN")
        cond = self.expression()
        self.consume("RPAREN")
        body = self.block()
        return While(cond, body)

    def for_stmt(self):
        self.consume("FOR")
        self.consume("LPAREN")
        init = None
        if self.peek().type != "SEMI":
            if self.peek().type in ("INT","FLOAT","STRING","BOOL"):
                init = self.var_decl()
            else:
                init = self.assignment()
        else:
            self.consume("SEMI")
        cond = None
        if self.peek().type != "SEMI":
            cond = self.expression()
        self.consume("SEMI")
        post = None
        if self.peek().type != "RPAREN":
            post = self.assignment()
        self.consume("RPAREN")
        body = self.block()
        return For(init, cond, post, body)

    def func_def(self):
        self.consume("FUNC")
        name = self.consume("ID").value
        self.consume("LPAREN")
        params = []
        if self.peek().type != "RPAREN":
            while True:
                ptype = self.consume().type.lower()
                pname = self.consume("ID").value
                params.append((ptype,pname))
                if self.peek().type == "COMMA":
                    self.consume("COMMA")
                    continue
                break
        self.consume("RPAREN")
        body = self.block()
        return FuncDef(name, params, body, None)

    def return_stmt(self):
        self.consume("RETURN")
        expr = None
        if self.peek().type != "SEMI":
            expr = self.expression()
        self.consume("SEMI")
        return Return(expr)

    def func_call_stmt(self):
        call = self.func_call()
        self.consume("SEMI")
        return call

    def func_call(self):
        name = self.consume("ID").value
        self.consume("LPAREN")
        args = []
        if self.peek().type != "RPAREN":
            while True:
                args.append(self.expression())
                if self.peek().type == "COMMA":
                    self.consume("COMMA")
                    continue
                break
        self.consume("RPAREN")
        return FuncCall(name, args)

    def expression(self):
        return self.logic_or()

    def logic_or(self):
        node = self.logic_and()
        while self.peek().type == "OP" and self.peek().value == "||":
            op = self.consume("OP").value
            right = self.logic_and()
            node = BinOp(node, op, right)
        return node

    def logic_and(self):
        node = self.equality()
        while self.peek().type == "OP" and self.peek().value == "&&":
            op = self.consume("OP").value
            right = self.equality()
            node = BinOp(node, op, right)
        return node

    def equality(self):
        node = self.relational()
        while self.peek().type == "OP" and self.peek().value in ("==","!="):
            op = self.consume("OP").value
            right = self.relational()
            node = BinOp(node, op, right)
        return node

    def relational(self):
        node = self.term()
        while self.peek().type == "OP" and self.peek().value in ("<",">","<=",">="):
            op = self.consume("OP").value
            right = self.term()
            node = BinOp(node, op, right)
        return node

    def term(self):
        node = self.factor()
        while self.peek().type == "OP" and self.peek().value in ("+","-"):
            op = self.consume("OP").value
            right = self.factor()
            node = BinOp(node, op, right)
        return node

    def factor(self):
        node = self.unary()
        while self.peek().type == "OP" and self.peek().value in ("*","/","%"):
            op = self.consume("OP").value
            right = self.unary()
            node = BinOp(node, op, right)
        return node

    def unary(self):
        if self.peek().type == "OP" and self.peek().value == "-":
            op = self.consume("OP").value
            node = self.unary()
            return BinOp(Literal(0,"int"), "-", node)
        return self.primary()

    def primary(self):
        tok = self.peek()
        if tok.type == "INT":
            v = int(self.consume("INT").value); return Literal(v,"int")
        if tok.type == "FLOAT":
            v = float(self.consume("FLOAT").value); return Literal(v,"float")
        if tok.type == "STRING":
            s = self.consume("STRING").value; return Literal(s.strip('"'),"string")
        if tok.type == "TRUE":
            self.consume("TRUE"); return Literal(True,"bool")
        if tok.type == "FALSE":
            self.consume("FALSE"); return Literal(False,"bool")
        if tok.type == "ID":
            if self.tokens[self.pos+1].type == "LPAREN":
                return self.func_call()
            return Identifier(self.consume("ID").value)
        if tok.type == "LPAREN":
            self.consume("LPAREN")
            e = self.expression()
            self.consume("RPAREN")
            return e
        raise ParseError(f"Unexpected primary {tok.type}")

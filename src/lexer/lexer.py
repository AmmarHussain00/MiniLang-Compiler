import re
from dataclasses import dataclass

@dataclass
class Token:
    type: str
    value: str
    line: int
    col: int

class LexerError(Exception):
    pass

class Lexer:
    KEYWORDS = {"if","else","while","for","print","input","func","return","true","false","int","float","string","bool"}
    SPEC = [
        ("STRING",  r'"[^"\\n]*"'),
        ("FLOAT",   r'\d+\.\d+'),
        ("INT",     r'\d+'),
        ("ID",      r'[A-Za-z_][A-Za-z0-9_]*'),
        ("OP",      r'==|!=|<=|>=|&&|\|\||[+\-*/%<>]=?|='),
        ("SEMI",    r';'),
        ("LPAREN",  r'\('),
        ("RPAREN",  r'\)'),
        ("LBRACE",  r'\{'),
        ("RBRACE",  r'\}'),
        ("COMMA",   r','),
        ("NEWLINE", r'\n'),
        ("SKIP",    r'[ \t\r]+'),
        ("MISMATCH",r'.'),
    ]

    def __init__(self, code):
        self.code = code
        self.line = 1
        self.col = 1
        self.regex = re.compile("|".join(f"(?P<{n}>{p})" for n,p in Lexer.SPEC))

    def tokenize(self):
        tokens = []
        for m in self.regex.finditer(self.code):
            kind = m.lastgroup
            val = m.group()
            if kind == "NEWLINE":
                self.line += 1
                self.col = 1
                continue
            if kind == "SKIP":
                self.col += len(val)
                continue
            if kind == "MISMATCH":
                raise LexerError(f"Unexpected {val!r} at {self.line}:{self.col}")
            if kind == "ID":
                if val in Lexer.KEYWORDS:
                    kind = val.upper()
                else:
                    kind = "ID"
            tokens.append(Token(kind, val, self.line, self.col))
            self.col += len(val)
        tokens.append(Token("EOF","",self.line,self.col))
        return tokens

if __name__=="__main__":
    code = 'int x = 5; if (x > 0) { print(x); }'
    lx = Lexer(code)
    for t in lx.tokenize():
        print(t)

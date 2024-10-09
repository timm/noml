#!/usr/bin/env python3.13 -B
# <!-- vim: set et ts=2 sw=2 :  -->
# -*-coding: utf-8 -*-  
# autopep8 -i --max-line-length 100 -a --indent-size 2 h2c.py  
# 1-(1-.35/6)^100 = 0.9975  
from typing import Union, List, Dict, Type, Callable, Generator
from fileinput import FileInput as file_or_stdin
from math import sqrt, exp, log, cos, pi
import random, sys, ast, re
R = random.random
one = random.choice
big = 1E32

class o:
  def __init__(self, **d): self.__dict__.update(**d)
  def __repr__(self): return self.__class__.__name__ + say(self.__dict__)

the=o(end=.5, far=30, guesses=100, p=2, seed=1234567891, 
     train="../../moot/optimize/misc/auto93.csv")

DATA, COLS, TREE = o, o, o
NUM, SYM  = o, o
COL = NUM | SYM
number = float | int   #
atom = number | bool | str  # and sometimes "?"
row = list[atom]
rows = list[row]
classes = dict[str, rows]  # `str` is the class name

def SYM(at=0, name=" ") -> SYM:
  return o(isNum=False, n=0, at=at, name=name, most=0, mode=None, counts={})

def NUM(at=0, name=" ") -> NUM:
  return o(isNum=True, n=0, at=at, name=name, mu=0, m2=0, sd=0, lo=big, hi=-big,
           goal=0 if name[-1] == "-" else 1)

def COLS(names: list[str]) -> COLS:
  all, x, y = [], [], []
  for at, name in enumerate(names):
    a, z = name[0], name[-1]
    col = (NUM if a.isupper() else SYM)(at=at, name=name)
    all += [col]
    if not z == "X":
      (y if z in "+-!" else x).append(col)
  return o(names=names, all=all, x=x, y=y)

def DATA(names: list[str], src=None, sortp=False) -> DATA:
  data1 = o(rows=[], cols=COLS(names))
  [data(data1, row) for row in src or []]
  return ydist(data1) if sortp else data1

def data(self: DATA, row) -> None:
  self.rows += [row]
  [col(c, row[c.at]) for c in self.cols.all]

def col(self: COL, x) -> None:
  if x == "?" : return
  self.n += 1
  if self.isNum:
    self.lo = min(x, self.lo)
    self.hi = max(x, self.hi)
    d = x - self.mu
    self.mu += d / self.n
    self.m2 += d * (x - self.mu)
    self.sd = 0 if self.n < 2 else (self.m2/(self.n - 1))**.5
  else:
    tmp = self.counts[x] = 1 + self.counts.get(x, 0)
    if tmp > self.most:
      self.most, self.mode = tmp, x

def mid(self: DATA) -> row:
  return [(c.mu if c.isNum else c.mode) for c in self.cols.all]

def read(file: str, sortp=False) -> DATA:
  src = csv(file)
  data1 = DATA(next(src))
  [data(data1, row) for row in src]
  return ydist(data1) if sortp else data1

def norm(self: NUM, x) -> float:
  return x if x == "?" else (x - self.lo)/(self.hi - self.lo + 1/big)

# ## Distance -----------------------------------------------------------------------------
#   _|  o   _  _|_   _.  ._    _   _
#  (_|  |  _>   |_  (_|  | |  (_  (/_

def xdist(self: DATA, row1: row, row2: row) -> float:
  "Minkowski distance between independent columns of two rows."
  def sym(_, x, y): return x != y

  def num(num1, x, y):
    x, y = norm(num1, x), norm(num1, y)
    x = x if x != "?" else (1 if y < .5 else 0)
    y = y if y != "?" else (1 if x < .5 else 0)
    return abs(x - y)
  n = d = 0
  for c in self.cols.x:
    a, b = row1[c.at], row2[c.at]
    d += 1 if a == b == "?" else (num if c.isNum else sym)(c, a, b)**the.p
    n += 1
  return (d/n) ** (1/the.p)

def ydist(self: DATA, row) -> float:
  "Chebyshev distance dependent columns to best possible dependent values."
  return max(abs(c.goal - norm(c, row[c.at])) for c in self.cols.y)

def ydists(self: DATA) -> DATA:
  "Short all rows by Chebyshev, best rows appear at lower values."
  self.rows.sort(key=lambda r: ydist(self, r))
  return self

class TREE(o): pass

def cluster(self: DATA, 
            rows=None, sortp=False, all=False, maxDepth=100) -> tuple[TREE, DATA]:
  "Recursively divide data via 2 distance points. Return all the tree or just best branch."
  stop = len(rows or self.rows)**the.end
  labels = {}
  def Y(a)  : labels[id(a)] = a; return ydist(self, a)
  def X(a, b): return xdist(self, a, b)

  def cut(rows, above=None):
    l, r = max([(above or one(rows), one(rows)) for _ in range(the.far)], key=lambda z: X(*z))
    l, r = (r, l) if sortp and Y(r) < Y(l) else (l, r)
    C = X(l, r)
    rows = sorted(rows, key=lambda row: (X(row, l)**2 + C**2 - X(row, r)**2)/(2*C + 1/big))
    n = int(len(rows) // 2)
    return rows[:n], l, rows[n:], r, C

  def nodes(rows, above=None, lvl=0, guard=None):
    if len(rows) >= stop and lvl <= maxDepth:
      ls, l, rs, r, C = cut(rows, above)
      data2 = DATA(self.cols.names, rows)
      return TREE(
        data=data2,
        y=ydist(self, l),
        lvl=lvl,
        c=C,
        guard=guard,
        left=nodes(ls, l, lvl+1, lambda row: X(row, ls[-1]) < X(row, rs[0])),
        right=nodes(rs, r, lvl+1, lambda row: X(row, ls[-1]) >= X(row, rs[0])) if all else None)

  return (nodes(rows or self.rows),  # tree
          ydists(DATA(self.cols.names, labels.values())))  # items labelled while making tree

def leaf(self: TREE, row) -> DATA:
  "Return the data most relevant (nearest) to `row`." 
  if self:
    for kid in [self.left, self.right]:
      if kid and kid.guard(row): return leaf(kid, row)
    return self.data
  
def leaves(self: TREE) -> Generator:
  "Iterate through the leaves."
  if self:
    if not self.left and not self.right:
      yield self
    for kid in [self.left, self.right]:
      for leaf in leaves(kid): 
        yield leaf

def showTree(self: TREE) -> None:
  "Display tree."
  if self:
    mid1 = mid(self.data)
    s1 = ' '.join([f"{mid1[c.at]:8g}" for c in self.data.cols.y])
    s2 = f"{'|.. ' * self.lvl}{len(self.data.rows):>4}"
    print(f"{self.y:.2f} ({s1:30}) {s2}")
    [showTree(kid) for kid in [self.left, self.right] if kid]

# ## Utils -----------------------------------------------------------------------------
# |          _|_  o  |   _
# |     |_|   |_  |  |  _>

def numeric(x): return int(x) if int(x)==x else x

def ent(d: dict, details=False) -> tuple[float,int] | float:
  "Return entropy of some symbol counts."
  N = sum(d.values())
  e = -sum([n/N*log(n/N, 2) for n in d.values() if n > 0])
  return (e,N) if details else e

def normal(mu: float, sd: float) -> float:
  "Sample from a gaussian."
  return mu + sd * sqrt(-2*log(R())) * cos(2*pi*R())

def cli(d: dict) -> None:
  "Update a dictionary from command-line flags. Maybe reset seed or exit showing help."
  for k, v in d.items():
    for c, arg in enumerate(sys.argv):
      if arg in ["-"+k[0], "--"+k]:
        after = sys.argv[c+1] if c < len(sys.argv) - 1 else "" 
        d[k] = coerce("False" if v=="True" else ("True" if v=="False" else after))
  if seed := d.get("seed",None): random.seed(seed)
  if d.get("help",None): sys.exit(print(__doc__ or ""))

def coerce(s: str) -> atom:
  "Turn a string into an int,float,bool or string."
  try: return ast.literal_eval(s)
  except Exception: return s

def csv(file: str) -> Generator:
  "Iterator. Return comma separated  values as rows."
  with file_or_stdin(None if file == "−" else file) as src:
    for line in src:
      line = re.sub(r"([\n\t\r ]|\#.*)", "", line)
      if line:
        yield [coerce(s.strip()) for s in line.split(",")]

def say(x: any) -> str:
  "Recursive pretty print of anything."
  if isinstance(x, float): 
    return str(x) if int(x) == x else f"{x:.3f}"
  if isinstance(x, list ) : return "["+', '.join([say(y) for y in x])+"]"
  if not isinstance(x, dict): return str(x)
  return "(" + ' '.join(f":{k} {say(v)}"
                        for k, v in x.items() if not str(k)[0] == "_") + ")"

def shuffle(lst: list) -> list:
  "Randomize order of a list. Return that list."
  random.shuffle(lst)
  return lst

# ## Main -----------------------------------------------------------------------------

class main:
  "Each method here can be called from command line via --method."
  def the(_): print(the)
  def num(_):
    r = 256
    num1 = NUM()
    [col(num1, normal(10, 2)) for _ in range(r)]
    assert 9.95 < num1.mu < 10 and 2 < num1.sd < 2.05, "main.num"

  def data(_):
    data1 = read(the.train)
    [print(col) for col in data1.cols.x]

  def xdist(_):
    data1 = read(the.train)
    random.shuffle(data1.rows)
    def d(r): return xdist(data1, data1.rows[0], r)
    for i, row in enumerate(sorted(data1.rows, key=d)):
      if i % 30 == 0:
        print(f"{d(row):.3f}", row)

  def ydist(_):
    data1 = read(the.train)
    random.shuffle(data1.rows)
    for i, row in enumerate(ydists(data1).rows):
      if i % 30 == 0:
        print(f"{ydist(data1,row):.3f}", row)

  def branch(_):
    data1 = ydists(read(the.train))
    n = int(len(data1.rows)//2)
    print(f"{ydist(data1, data1.rows[n]):.3}")
    _, labels = cluster(data1, sortp=True, maxDepth=4, all=False)
    print(f"{ydist(data1, labels.rows[0]):.3}")

  def tree(_):
    data1 = read(the.train)
    tree1, _ = cluster(data1, sortp=True, all=True, maxDepth=3)
    #showTree(tree1)
    for leaf in leaves(tree1): print(leaf.c)

# ## Start -----------------------------------------------------------------------------
#   _  _|_   _.  ._  _|_
#  _>   |_  (_|  |    |_

random.seed(the.seed)
if __name__ == "__main__":
  cli(the.__dict__)
  for i, s in enumerate(sys.argv):
    if s[:2] == "--":
      getattr(main, s[2:], lambda _: print(f"'{s}' not known"))(i)

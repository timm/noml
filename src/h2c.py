#!/usr/bin/env python3.13 -B
# vim: set et ts=2 sw=2 :
# -*-coding: utf-8 -*-
# autopep8 -i --max-line-length 100 -a --indent-size 2 h2c.py
# 1-(1-.35/6)^80  = 0.991
# 1-(1-.35/6)^100 = 0.9975

#                   .------.
#      .---->  Best | B    | 
#      |            |    5 |
#      |     .------.------.
#      v     | R    |      
#      Rest  |   75 |     
#            .------.    

"""
h2c.py: how to change your mind (via diversity sampling, then TPE with Naive Bayes)
(c) 2024 Tim Menzies (timm@ieee.org). BSD-2 license

USAGE:
  chmod +x h2c.py
  ./h2c.py [OPTIONS]

OPTIONS:
  -e --end     leaf cluster size              = .5
  -f --far     samples for finding far points = 30
  -g --guesses max guesses per loop           = 100
  -h --help    show help                      = False
  -k --k       low frequency Bayes hack       = 1
  -l --lives   number of tolerated failures   = 7
  -m --m       low frequency Bayes hack       = 2
  -p --p       distance formula exponent      = 2
  -r --rseed   random number seed             = 1234567891
  -s --start   init number of labels          = 4
  -S --Stop    max number of labels           = 30
  -t --train   training csv file.             = ../../moot/optimize/misc/auto93.csv
  --help print help
"""

__author__ = "Tim Menzies"
__copyright__ = "Copyright 2024, Tim Menzies"
__influences = ["Dieter Rams (less, but better)"]
__license__ = "BSD two-clause"
__version__ = "0.6.0"
__maintainer__ = "Tim Menzies"
__email__ = "timm@ieee.org"
__status__ = "Development Status :: 3 - Alpha"

from typing import Any as any
from typing import Union, List, Dict, Type, Callable, Generator
from fileinput import FileInput as file_or_stdin
from math import sqrt, exp, log, cos, pi
import random, sys, ast, re

R = random.random
one = random.choice
big = 1E32

class o:
  "Simple struct. Supports easy init and pretty print." 
  def __init__(self, **d): self.__dict__.update(**d)
  def __or__(self,d): self.__dict__.update(**d); return self
  def __repr__(self): return self.__class__.__name__ + say(self.__dict__)

DATA, COLS, TREE = o, o, o
NUM, SYM  = o, o
COL = NUM | SYM

number = float | int   #
atom = number | bool | str  # and sometimes "?"
row = list[atom]
rows = list[row]
classes = dict[str, rows]  # `str` is the class name

# -----------------------------------------------------------------------------
#   _|   _.  _|_   _.
#  (_|  (_|   |_  (_|

def COL(at=0, name=" ") -> COL:
  "Columns know their position `at`, their `name`, and item numbers `n`."
  return o(n=0, at=at, name=name)

def SYM(**d) -> SYM:
  "SYMs track symbol `counts` and `mode` of a stream of symbols."
  return COL(**d) | dict(isNum=False, most=0, mode=None, counts={})

def NUM(**d) -> NUM:
  "NUMs track mean `mu`, `sd`, `lo` and `hi` of a stream of numbers."
  return COL(**d) | dict(isNum=True, mu=0, m2=0, sd=0, lo=big, hi=-big, 
                          goal=0 if d.get("name"," ")[-1] == "-" else 1)

def COLS(names: list[str]) -> COLS:
  "Turn a list of `names` into NUMs and SYMs."
  all, x, y = [], [], []
  for at, name in enumerate(names):
    a, z = name[0], name[-1]
    col = (NUM if a.isupper() else SYM)(at=at, name=name)
    all += [col]
    if not z == "X":
      (y if z in "+-!" else x).append(col)
  return o(names=names, all=all, x=x, y=y)

def DATA(names: list[str], src: list | Generator = None) -> DATA:
  "DATAs hold `rows` of data, summarized in `cols` (columns)."
  data1 = o(rows=[], cols=COLS(names))
  [data(data1, row) for row in src or []]
  return data1

def data(self: DATA, row) -> None:
  "Update a DATA with one `row`."
  self.rows += [row]
  [col(c, row[c.at]) for c in self.cols.all]

def col(self: COL, x) -> None:
  "Update a NUM or SYM with one more item."
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
  "Return the row closest to the middle of a DATA."
  tmp = [(c.mu if c.isNum else c.mode) for c in self.cols.all]
  return min(self.rows, key=lambda row: xdist(self, row, tmp))

def div(self: DATA) -> list[float]:
  "Return standard deviation or entropy of each column."
  return [(c.sd if c.isNum else ent(c.counts)[0]) for c in self.cols.all]

def read(file: str) -> DATA:
  "Load in a csv file into a new DATA."
  src = csv(file)
  self = DATA(next(src))
  [data(self, row) for row in src]
  return self

def norm(self: NUM, x) -> float:
  "Normalize a number to the range 0..1 for min..max."
  return x if x == "?" else (x - self.lo)/(self.hi - self.lo + 1/big)

# -----------------------------------------------------------------------------
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
    return rows[:n], l, rows[n:], r

  def nodes(rows, above=None, lvl=0, guard=None):
    if len(rows) >= stop and lvl < maxDepth:
      ls, l, rs, r = cut(rows, above)
      data2 = DATA(self.cols.names, rows)
      return TREE(
        data=data2,
        y=ydist(self, l),
        lvl=lvl,
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
  
def showTree(self: TREE) -> None:
  "Display tree."
  if self:
    mid1 = mid(self.data)
    s1 = ', '.join([f"{mid1[c.at]:6g}" for c in self.data.cols.y])
    s2 = f"{'|.. ' * self.lvl}{len(self.data.rows):>4}"
    print(f"{self.y:.2f} | {s1:20} {s2}")
    [showTree(kid) for kid in [self.left, self.right] if kid]

# -----------------------------------------------------------------------------
#  |_    _.       _    _
#  |_)  (_|  \/  (/_  _>
#            /

def like(self: DATA, row: row, nall: int, nh: int) -> float:
  "Compute likelihood that row belongs to a DATA."
  def sym(sym1, x, prior):
    return (sym1.counts.get(x, 0) + the.m*prior) / (sym1.n + the.m)

  def num(num1, x, _):
    v = num1.sd**2 + 1E-30
    nom = exp(-1*(x - num1.mu)**2/(2*v)) + 1E-32
    denom = (2*pi*v) ** 0.5
    return min(1, nom/(denom + 1E-32))

  prior = (len(self.rows) + the.k) / (nall + the.k*nh)
  likes = [(num if c.isNum else sym)(c, row[c.at], prior) for c in self.cols.x]
  return sum(log(x) for x in likes + [prior] if x > 0)

def acquire(self: DATA, rows: rows, labels=None, score=lambda b,r: b+b-r) -> rows:
  "From a model built so far, label next most interesting example. And repeat."
  labels = labels or {}
  def Y(a): labels[id(a)] = a; return ydist(self, a)

  def guess(todo, done):
    nBest = int(len(done)**the.end)
    nUse = min(the.guesses, len(todo))/len(todo)
    best = DATA(self.cols.names, done[:nBest])
    rest = DATA(self.cols.names, done[nBest:])
    def key(row): return 0 if R() > nUse else score(like(best, row, len(done), 2),
                                                    like(rest, row, len(done), 2))
    return sorted(todo, key=key, reverse=True)

  def loop(todo, done):
    lives, most = 4,-1
    while len(done) < the.Stop and lives>0:
      top, *todo = guess(todo, done)
      done += [top]
      if ydist(self,top) > most: 
         most=ydist(self,top)
         lives += 4
      else:
         lives -= 1
      done.sort(key=Y)
    return done

  b4 = list(labels.values())
  m = max(0, the.start - len(b4))
  return labels, loop(rows[m:], sorted(rows[:m] + b4, key=Y))

# must return expect tne and subtrees wth garuds
def cuts(self:DATA, datas:classes):
  def add(d,x,n=1): d[x] = d.get(x,0) + n; return x
  def sub(d,x) : return add(d,x,-1)
  def nums(num1:NUM, xys):
    least, left, right, now = len(xys)/(6/.35), {},{},[]
    [add(right,y) for _,y in xys]
    lo,_ = ent(right)
    for i,(x,y) in enumerate(xys):
      now += [add(left, sub(right,y))]
      if least <= i < len(xys) - least and len(now) >= least:
        if x != xys[i+1][0] and now[-1] - now[0] > .35*num1.sd:
          e1,n1 = ent(left)
          e2,n2 = ent(right)
          e = (n1 * e1 + n2 * e2)/(n1 + n2)
          if e < lo:
            lo,cut,now = e,x,[]
    if cut:

  def syms(_,xys):
    N,d,n = 0,{},{}
    for x,y in xys:
      d.get[x] = d.get(x,{})
      add(d[x], y)
      add(n,x)
      N += 1
    return sum(n[x]/N * ent(y)[0] for x,y in d.items()), d.keys

  all = [(c, sorted([(r[c.at],k)) for  k,d in datas.items() for r in d.rows if r[c.at] != "?"])
         for c in self.cols.x]]
  cuts = {c.at: (nums if c.isNum else syms)(c,xys) for c,xys in all}

# -----------------------------------------------------------------------------
#       _|_  o  |   _
#  |_|   |_  |  |  _>

def numeric(x): return int(x) if int(x)==x else x

def ent(d: dict) -> float:
  "Return entropy of some symbol counts."
  N = sum(d.values())
  return [n/N*log(n/N, 2) for n in d.values()],N

def normal(mu: float, sd: float) -> float:
  "Sample from a gaussian."
  return mu + sd * sqrt(-2*log(R())) * cos(2*pi*R())

def cli(d: dict) -> None:
  "Update a dictionary from command-line flags. Maybe reset seed or exit showing help."
  for k, v in d.items():
    for c, arg in enumerate(sys.argv):
      if arg == "-h":
        sys.exit(print(__doc__ or ""))
      if arg in ["-"+k[0], "--"+k]:
        after = sys.argv[c+1] if c < len(sys.argv) - 1 else "" 
        d[k] = coerce("False" if v=="True" else ("True" if v=="False" else after))
  if seed := d.get("rseed",None): random.seed(seed)
  if d.get("help",None): sys.exit(print(__doc__))

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

# -----------------------------------------------------------------------------
#  ._ _    _.  o  ._
#  | | |  (_|  |  | |

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

  def bayes(_):
    data1 = read(the.train)
    for i, row in enumerate(sorted(data1.rows, key=lambda r:like(data1,r,1000,2))):
      if i % 30 == 0:
        print(f"{like(data1,row,1000,2):.3f}", row)
    m = mid(data1)
    print(f"{like(data1,m,1000,2):.3f}", m)

  def branch(_):
    data1 = ydists(read(the.train))
    n = int(len(data1.rows)//2)
    print(f"{ydist(data1, data1.rows[n]):.3}")
    _, labels = cluster(data1, sortp=True, maxDepth=4, all=False)
    print(f"{ydist(data1, labels.rows[0]):.3}")

  def tree(_):
    data1 = read(the.train)
    tree1, _ = cluster(data1, sortp=True, all=True, maxDepth=4)
    showTree(tree1)

  def acquire(_):
    data1 = ydists(read(the.train))
    num1,num2 = NUM(),NUM()
    [col(num1,ydist(data1,row)) for row in data1.rows]
    for _ in range(20):
      labels, rows = acquire(data1, shuffle(data1.rows))
      print(len(rows), end=" ")
      col(num2, ydist(data1,rows[0]))
    print(f"{num1.mu:.3f}, {num1.lo+.35*num1.sd:.3f} {num2.mu:.3f}")

# -----------------------------------------------------------------------------
#   _  _|_   _.  ._  _|_
#  _>   |_  (_|  |    |_

the = o(**{m[1]: coerce(m[2]) for m in re.finditer(r"--(\w+).*=\s*(\S+)", __doc__)})
random.seed(the.rseed)

if __name__ == "__main__":
  cli(the.__dict__)
  for i, s in enumerate(sys.argv):
    if s[:2] == "--":
      getattr(main, s[2:], lambda _: print(f"'{s}' not known"))(i)

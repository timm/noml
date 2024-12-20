#!/usr/bin/env python3.13 -B
# <!-- vim: set et ts=2 sw=2 :  -->
# -*-coding: utf-8 -*-  
# autopep8 -i --max-line-length 100 -a --indent-size 2 h2c.py  
# 1-(1-.35/6)^100 = 0.9975  

"""
h2c.py: How 2 Change your mind  
(via diversity sampling, then TPE with Naive Bayes)    
(c) 2024 Tim Menzies (timm@ieee.org). BSD-2 license  
  
USAGE:  
  chmod +x h2c.py  
  ./h2c.py [OPTIONS]  
  
OPTIONS:  
  -c --cohen   size of 'near enough'          = .35
  -e --end     leaf cluster size              = .5  
  -f --far     samples for finding far points = 30  
  -g --guesses max guesses per loop           = 100  
  -h --help    show help                      = False  
  -k --k       low frequency Bayes hack       = 1  
  -l --lives   number of tolerated failures   = 4  
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
  def __add__(self,d): self.__dict__.update(**d); return self
  def __repr__(self): return self.__class__.__name__ + say(self.__dict__)

DATA, COLS, CLUSTER, TREE = o, o, o
NUM, SYM  = o, o
COL = NUM | SYM

number = float | int   #
atom = number | bool | str  # and sometimes "?"
row = list[atom]
rows = list[row]
classes = dict[str, rows]  # `str` is the class name

# ## Data -----------------------------------------------------------------------------
#  _|   _.  _|_   _.
# (_|  (_|   |_  (_|

def COL(at=0, name=" ") -> COL:
  "Columns know their position `at`, their `name`, and item numbers `n`."
  return o(n=0, at=at, name=name)

def SYM(**d) -> SYM:
  "SYMs track symbol `counts` and `mode` of a stream of symbols."
  return COL(**d) + dict(isNum=False, most=0, mode=None, counts={})

def NUM(**d) -> NUM:
  "NUMs track mean `mu`, `sd`, `lo` and `hi` of a stream of numbers."
  return COL(**d) + dict(isNum=True, mu=0, m2=0, sd=0, lo=big, hi=-big,
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
  return [(c.sd if c.isNum else ent(c.counts)) for c in self.cols.all]

def read(file: str) -> DATA:
  "Load in a csv file into a new DATA."
  src = csv(file)
  self = DATA(next(src))
  [data(self, row) for row in src]
  return self

def norm(self: NUM, x) -> float:
  "Normalize a number to the range 0..1 for min..max."
  return x if x == "?" else (x - self.lo)/(self.hi - self.lo + 1/big)

# ## Bayes -----------------------------------------------------------------------------
#  |_    _.       _    _
#  |_)  (_|  \/  (/_  _>
#            /

def like(self: DATA, row: row, nall: int, nh: int) -> float:
  "Compute likelihood that row belongs to a DATA."
  def _sym(sym1, x, prior):
    return (sym1.counts.get(x, 0) + the.m*prior) / (sym1.n + the.m)

  def _num(num1, x, _):
    v = num1.sd**2 + 1E-32
    tmp = exp(-1*(x - num1.mu)**2/(2*v)) / (2*pi*v) ** 0.5
    return min(1, tmp + 1E-32)

  prior = (len(self.rows) + the.k) / (nall + the.k*nh)
  likes = [(_num if c.isNum else _sym)(c, row[c.at], prior) for c in self.cols.x]
  return sum(log(x) for x in likes + [prior] if x > 0)

def acquire(self: DATA, rows: rows, labels=None, fun=lambda b,r: b+b-r) -> tuple[dict,row]:
  "From a model built so far, label next most interesting example. And repeat."
  labels = labels or {}
  def _Y(a): labels[id(a)] = a; return ydist(self, a)

  def _guess(todo, done):
    def key(r):
      return 0 if R() > guesses else fun(like(b, row, len(done), 2), like(r, row, len(done), 2))
    guesses = min(the.guesses, len(todo)) / len(todo)
    n = int(len(done)**the.end)
    b = DATA(self.cols.names, done[:n])
    r = DATA(self.cols.names, done[n:])
    return sorted(todo, key=key, reverse=True)

  def _loop(todo, done):
    lives, least, out = the.lives, big, None
    while len(done) < the.Stop and lives>0:
      top, *todo = guess(todo, done)
      done = sorted(done + [top], key=_Y)
      if ydist(self,done[0]) < least: 
        least = ydist(self,done[0])
        lives += the.lives
      else:
        lives -= 1
    return done

  b4 = list(labels.values())
  m = max(0, the.start - len(b4))
  return labels, _loop(rows[m:], sorted(rows[:m] + b4, key=_Y))

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
  if seed := d.get("rseed",None): random.seed(seed)
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

# ## Distance -----------------------------------------------------------------------------
#   _|  o   _  _|_   _.  ._    _   _
#  (_|  |  _>   |_  (_|  | |  (_  (/_

def xdist(self: DATA, row1: row, row2: row) -> float:
  "Minkowski distance between independent columns of two rows."
  def _sym(_, x, y): return x != y

  def _num(num1, x, y):
    x, y = norm(num1, x), norm(num1, y)
    x = x if x != "?" else (1 if y < .5 else 0)
    y = y if y != "?" else (1 if x < .5 else 0)
    return abs(x - y)
  n = d = 0
  for c in self.cols.x:
    a, b = row1[c.at], row2[c.at]
    d += 1 if a == b == "?" else (_num if c.isNum else _sym)(c, a, b)**the.p
    n += 1
  return (d/n) ** (1/the.p)

def ydist(self: DATA, row) -> float:
  "Chebyshev distance dependent columns to best possible dependent values."
  return max(abs(c.goal - norm(c, row[c.at])) for c in self.cols.y)

def ydists(self: DATA) -> DATA:
  "Short all rows by Chebyshev, best rows appear at lower values."
  self.rows.sort(key=lambda r: ydist(self, r))
  return self

class CLUSTER(o): pass

def dendogram(self: DATA, 
              rows=None, sortp=False, all=False, maxDepth=100) -> tuple[CLUSTER, DATA]:
  "Recursively divide data via 2 distance points. Return all the tree or just best branch."
  stop = len(rows or self.rows)**the.end
  labels = {}
  def _Y(a)  : labels[id(a)] = a; return ydist(self, a)
  def _X(a, b): return xdist(self, a, b)

  def _cut(rows, above=None):
    l, r = max([(above or one(rows), one(rows)) for _ in range(the.far)], key=lambda z: _X(*z))
    l, r = (r, l) if sortp and _Y(r) < _Y(l) else (l, r)
    C = _X(l, r)
    rows = sorted(rows, key=lambda row: (_X(row, l)**2 + C**2 - _X(row, r)**2)/(2*C + 1/big))
    n = int(len(rows) // 2)
    return rows[:n], l, rows[n:], r

  def _nodes(rows, above=None, lvl=0, guard=None):
    if len(rows) >= stop and lvl <= maxDepth:
      ls, l, rs, r = _cut(rows, above)
      data2 = DATA(self.cols.names, rows)
      return CLUSTER(
        data=data2,
        y=_Y(self, l),
        lvl=lvl,
        guard=guard,
        left=_nodes(ls, l, lvl+1, lambda row: _X(row, ls[-1]) < _X(row, rs[0])),
        right=_nodes(rs, r, lvl+1, lambda row: _X(row, ls[-1]) >= _X(row, rs[0])) if all else None)

  return (_nodes(rows or self.rows),  # tree
          ydists(DATA(self.cols.names, labels.values())))  # items labelled while making tree

def leaf(self: CLUSTER, row) -> DATA:
  "Return the data most relevant (nearest) to `row`." 
  if self:
    for kid in [self.left, self.right]:
      if kid and kid.guard(row): return leaf(kid, row)
    return self.data
  
def leaves(self: CLUSTER) -> Generator:
  "Iterate through the leaves."
  if self:
    if not self.left and not self.right:
      yield self
    for kid in [self.left, self.right]:
      for leaf in leaves(kid): 
        yield leaf

def showTree(self: CLUSTER) -> None:
  "Display tree."
  if self:
    mid1 = mid(self.data)
    s1 = ' '.join([f"{mid1[c.at]:6g}" for c in self.data.cols.y])
    s2 = f"{'|.. ' * self.lvl}{len(self.data.rows):>4}"
    print(f"{self.y:.2f} ({s1:20}) {s2}")
    [showTree(kid) for kid in [self.left, self.right] if kid]

# ## Tree -----------------------------------------------------------------------------
#  _|_  ._   _    _
#   |_  |   (/_  (/_ 

class TREE(o): pass

def decisionTree(self:DATA, datas:classes, stop=10, lvl=0, guard=None):
  kids=[]
  d = {y:len(rows) for y,rows in datas}
  n = sum(d.values())
  if n > stop and ent(d) != 0:
    for guard in gaurds(self,datas):
      datas1 = {y:[row for y,rows in datas for row in rows if gaurd.gaurd(row)]}
      kids += [decisionTree(self, datas1, stop=stop, lvl=lvl+1, guard)]
  return TREE(lvl=lvl, datas=datas, guard=guard, kids=kids)

def inc(d, x, n=1): d[x] = d.get(x,0) + n; return x
def dec(d, x) : return inc(d,x,-1) 

def guards(self:DATA, datas:classes):
  min= big
  for c in self.cols.x:
    all= [(r[c.at],y) for y,d in datas for r  in d.rows if r[c.at] != "?"]
    if now := (guardNums if c.isNum else guardSyms)(c,sorted(all))
      if now.e > min: 
        min, guards, =now.e, sorted(now.guards, key=lambda guard: -guard.n)
   return guards

def guardSyms(self:SYM,xys): 
  d,n = {},{}
  for x,y in xys:
    d[x] = d.get(x,{})
    inc(d[x],y)
    inc(n,x) 
  guards= [o(txt=f"{self.name} == {x}", n=n[x], guard==lambda row: row[self.at] in ["?",x]) 
           for x in d.keys()]
  return o(e=sum((n[x]/len(xys)) * ent(y) for x,y in d.items()), guards=guards)

def guardNums(self:NUM, xys):
  least = len(xys)/(6/the.cohen)
  guards, left, right, now = None, {}, {}, []
  [_inc(right, y) for _,y in xys]
  lo = ent(right)
  for i,(x,y) in enumerate(xys):
    now += [inc(left, dec(right, y))]
    if least <= i < len(xys) - least and len(now) >= least:
      if x != xys[i+1][0] and now[-1] - now[0] > the.cohen*self.sd:
        e1,n1 = ent(left, 1)
        e2,n2 = ent(right, 1)
        e = (n1 * e1 + n2 * e2)/(n1+n2)
        if e < lo:
          lo,now = e,[]
          guards= o(e=lo, guards=[
                    o(txt=f"{self.name} <= {guard}", n=n,           
                      guard=lambda row: row[self.at]=="?" or row[self.at]<= guard),
                    o(txt=f"{self.name}  > {guard}", n=len(xys)- n, 
                      guard=lambda row: row[self.at]=="?" or row[self.at]>  guard)])
  return guards


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
    tree1, _ = cluster(data1, sortp=True, all=True, maxDepth=3)
    showTree(tree1)

  def acquire(_):
    data1 = ydists(read(the.train))
    asIs = NUM()
    [col(asIs,ydist(data1,row)) for row in data1.rows]
    print(the)
    for the.lives in [2,4,6,8,10,the.Stop]:
      toBe,samples = NUM(),NUM()
      for _ in range(20):
        labels, rows = acquire(data1, shuffle(data1.rows))
        col(samples, len(labels.values()))
        col(toBe, ydist(data1,rows[0]))
      better = (asIs.mu - toBe.mu)/asIs.sd
      print(f"{the.lives:3} :labels {samples.mu:3.1f} :asIs {asIs.mu:.3f} :todo {toBe.mu:.3f} :delta {better:.3f}")

  def cuts(_):
    data1 = ydists(read(the.train))
    nodes, labels = cluster(data1, sortp=False, maxDepth=4, all=True)
    for x in cuts(data1,  [(i,node.data) for i,node in enumerate(leaves(nodes))]):
      print(x)

# ## Start -----------------------------------------------------------------------------
#   _  _|_   _.  ._  _|_
#  _>   |_  (_|  |    |_

the = o(**{m[1]: coerce(m[2]) for m in re.finditer(r"--(\w+).*=\s*(\S+)", __doc__)})
random.seed(the.rseed)

if __name__ == "__main__":
  cli(the.__dict__)
  for i, s in enumerate(sys.argv):
    if s[:2] == "--":
      getattr(main, s[2:], lambda _: print(f"'{s}' not known"))(i)

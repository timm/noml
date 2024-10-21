#!/usr/bin/env python3.13 -B
# <!-- vim: set et ts=4 sw=4 :  -->
# -*-coding: utf-8 -*-
# autopep8 -i --max-line-length 100 -a --indent-size 4 how.py
"""
how.py: how to change your mind, with very little information
(c) Tim Menzies <timm@ieee.org>, BSD-2 license """

from typing import Any as any
from typing import Union, List, Dict, Type, Callable, Generator
from fileinput import FileInput as file_or_stdin
from math import sqrt, exp, log, cos, inf, pi
import random, time, sys, ast, re
from stats import SOME,report

class o:
  def __init__(self, **d): self.__dict__.update(**d)
  def __repr__(self): return self.__class__.__name__ + say(self.__dict__)

the = o(
  k=1,
  m=2,
  p=2,
  rseed=1234567891,
  start=4,
  Stop=30,
  train="../../moot/optimize/misc/auto93.csv")

big = 1E32
R = random.random
random.seed(the.rseed)

# ## TYPES --------------------------------------------------------------------
DATA, COLS = o, o
NUM, SYM = o, o
COL = NUM | SYM
number = float | int   #
atom = number | bool | str  # and sometimes "?"
row = list[atom]
rows = list[row]
classes = dict[str, rows]  # `str` is the class name

# ## STRUCTS -------------------------------------------------------------------
def SYM(at=0, txt=" ") -> SYM:
  return o(nump=False, n=0, at=at, txt=txt, most=0, mode=None, counts={})

def NUM(at=0, txt=" "):
  return o(nump=True, n=0, at=at, txt=txt, m2=0, mu=0, sd=0, lo=big, hi=-big,
       goal=0 if txt[-1] == "-" else 1)

def COLS(names: list[str]) -> COLS:
  all, x, y, nums = [], [], [], []
  for at, s in enumerate(names):
    col = (NUM if s[0].isupper() else SYM)(at=at, txt=s)
    all += [col]
    if not s[-1] == "X":
      (y if s[-1] in "+-!" else x).append(col)
  return o(names=names, all=all, x=x, y=y)

def DATA(names, rows=None):
  return datas(  # datas is a CREATE function
    o(rows=[], cols=COLS(names)), rows)

# ## UPDATE -------------------------------------------------------------------
def num(self: NUM, x):
  if x != "?":
    self.n += 1
    self.lo = min(x, self.lo)
    self.hi = max(x, self.hi)
    d = x - self.mu
    self.mu += d / self.n
    self.m2 += d * (x - self.mu)
    self.sd = stdev(self)
  return x

def sym(self: SYM, x, n=1):
  if x != "?":
    self.n += n
    tmp = self.counts[x] = n + self.counts.get(x, 0)
    if tmp > self.most:
      self.most, self.mode = tmp, x
  return x

def add(self: COL, x): return (num if self.nump else sym)(self, x)

def adds(self: COL, src):
  [add(self, x) for x in src]
  return self

def data(self: DATA, row):
  self.rows += [row]
  [add(c, row[c.at]) for c in self.cols.all]

def datas(self: DATA, rows=None):
  [data(self, row) for row in rows or []]
  return self

# ## CREATE -------------------------------------------------------------------
def clone(self: DATA, rows=None):
  return datas(o(rows=[], cols=COLS(self.cols.names)), rows)

def read(file: str) -> DATA:
  src = csv(file)
  return datas(o(rows=[], cols=COLS(next(src))), src)

def merged(i: SYM, j: SYM, n: int) -> SYM:
  k = SYM(at=i.at, txt=i.txt)
  for counts in [i.counts, j.counts]:
    for x, n in counts.items:
      sym(k, x, n)
  if i.n < n or j.n < n: return k
  if len(k.counts.keys()) == 2 and k.mode == i.mode == j.mode: return k
  if ent(k.counts) <= (i.n*ent(i.counts) + j.n*ent(j, counts))/k.n: return k

# ## QUERY --------------------------------------------------------------------
def norm(self: NUM, x) -> float:
  return x if x == "?" else (x - self.lo)/(self.hi - self.lo + 1/big)

def stdev(self: NUM): return 0 if self.n < 2 else (self.m2/(self.n - 1))**.5

def cdf(self: NUM, x):
  def fun(x): return 1 - 0.5 * exp(-0.717*x - 0.416*x*x)
  z = (x - i.mu) / i.sd
  return fun(z) if z >= 0 else 1 - fun(-z)

# ## Bayes -------------------------------------------------------------------
def like(self: DATA, row: row, nall: int, nh: int) -> float:
  def _sym(sym1, x, prior):
    return (sym1.counts.get(x, 0) + the.m*prior) / (sym1.n + the.m)

  def _num(num1, x, _):
    v = num1.sd**2 + 1E-32
    tmp = exp(-1*(x - num1.mu)**2/(2*v)) / (2*pi*v) ** 0.5
    return min(1, tmp + 1E-32)

  prior = (len(self.rows) + the.k) / (nall + the.k*nh)
  likes = [(_num if c.nump else _sym)(c, row[c.at], prior) for c in self.cols.x]
  return sum(log(x) for x in likes + [prior] if x > 0)

def learn(self:DATA, ntrain=0.33):
  random.shuffle(self.rows)
  best,rest,done = None,None,None
  Y  = lambda r: ydist(self, r) # best is left
  BR = lambda r: like(best,r,len(done),2) - like(rest,r,len(done),2) # best is right
  ntrain = int(ntrain * len(self.rows))
  train  = self.rows[:ntrain]
  test   = self.rows[ntrain:]
  todo   = train[the.start:]
  done   = train[:the.Start]
  while True:
    done = sorted(done,key=Y)
    if len(done) > the.Stop: break
    n    = int(sqrt(len(done)))
    best = clone(self, done[:n])
    rest = clone(self, done[n:])
    a, b, *todo, c, d = todo #sorted(todo, key=BR)
    done = done + [a,b,c,d]
  return (done[0]
         ,max([r for r in test if BR(r) > 0], key=BR))

def learn1(self:DATA, ntrain=0.33):
  random.shuffle(self.rows)
  best,rest,done = None,None,None
  Y  = lambda r: ydist(self, r) # best is left
  BR = lambda r: like(best,r,len(done),2) - like(rest,r,len(done),2) # best is right
  ntrain = int(ntrain * len(self.rows))
  train  = self.rows[:ntrain]
  test   = self.rows[ntrain:]
  done   = sorted(train[:the.Stop],key=Y)
  n      = int(sqrt(len(done)))
  best   = clone(self, done[:n])
  rest   = clone(self, done[n:])
  return (done[0]
         ,max([r for r in test if BR(r) > 0], key=BR))

# ## DISTANCE -----------------------------------------------------------------
# def ydist(self: DATA, row) -> float:
#   "Chebyshev distance dependent columns to best possible dependent values."
#   return max(abs(c.goal - norm(c, row[c.at])) for c in self.cols.y)

def ydist(i:DATA, row1:row) -> number:
  d = sum(abs(norm(y, row1[y.at]) - y.goal)**the.p for y in i.cols.y)
  return (d / len(i.cols.x))**(1/the.p)

def ydists(self: DATA) -> DATA:
  self.rows.sort(key=lambda r: ydist(self, r))
  return self

# ## UTILS --------------------------------------------------------------------
def say(x: any) -> str:
  if isinstance(x, float): return str(x) if int(x) == x else f"{x:.3f}"
  if isinstance(x, list ) : return "["+', '.join([say(y) for y in x])+"]"
  if not isinstance(x, dict): return str(x)
  return "(" + ' '.join(f":{k} {say(v)}"
              for k, v in x.items() if not str(k)[0] == "_") + ")"

def cli(a: list[str], d: dict) -> None:
  slots = {f"-{k[0]}": k for k in d}
  for i, s in enumerate(a):
    if s in ["-h", "--help"]: sys.exit(print(__doc__))
    elif s[:2] == "--": getattr(main, s[2:], lambda: print("?", s[2:]))()
    elif s in slots:
      k = slots[s]
      d[k] = coerce(d[k] == True and "False" or d[k] == False and "True" or a[i+1])
      if k == "rseed": random.seed(d[k])

def shuffle(lst): random.shuffle(lst); return lst

def coerce(s: str) -> atom:
  try: return ast.literal_eval(s)
  except Exception: return s

def csv(file: str) -> Generator:
  with file_or_stdin(None if file == "−" else file) as src:
    for line in src:
      line = re.sub(r"([\n\t\r ]|\#.*)", "", line)
      if line:
        yield [coerce(s.strip()) for s in line.split(",")]

# ## START UP -----------------------------------------------------------------
class main:
  "things that can be called from the command line using --x"
  def the(): print(the)

  def like():
    data1 = read(the.train)
    print(sorted([round(like(data1, row, len(data1.rows), 2), 2)
            for i, row in enumerate(data1.rows) if i % 20 == 0]))

  def ydist():
    data1 = read(the.train)
    print(sorted([round(ydist(data1, row), 2)
            for i, row in enumerate(data1.rows) if i % 20 == 0]))

  def learn1():
    data1 = read(the.train)
    num = adds(NUM(), [ydist(data1, row) for row in data1.rows])
    Y = lambda r: R(ydist(data1,r))
    R = lambda n: round(n,3)
    trained,tested = NUM(),NUM()
    for _ in range(20):
      trained1, tested1 = learn1(data1)
      add(trained, Y(trained1))
      add(tested,  Y(tested1))
    print(the.Stop, [R(x) for x in [num.lo,num.mu,trained.mu,tested.mu]])

if __name__ == "__main__":
  cli(sys.argv, the.__dict__)

#!/usr/bin/env python3.13 -B
"""
how.py: how to change your mind, with very little information
(c) Tim Menzies <timm@ieee.org>, BSD-2 license """

from typing import Any as any
from typing import Union, List, Dict, Type, Callable, Generator
from fileinput import FileInput as file_or_stdin
from math import sqrt, exp, log, cos, inf,pi
import random, time, sys, ast, re
from stats import SOME

class o:
  def __init__(self, **d): self.__dict__.update(**d)
  def __repr__(self): return self.__class__.__name__ + say(self.__dict__)

the = o(
  bins=7,
  cohen=0.35, 
  end=.5, 
  far=30,
  guesses=100,
  k=1, 
  m=2, 
  p=2,
  rseed=1234567891,  
  Repeats=20,
  start=4, 
  Stop=10, 
  train="../../moot/optimize/misc/auto93.csv"
)

big=1E32
R=random.random
random.seed(the.rseed)

# ## TYPES --------------------------------------------------------------------
DATA, COLS = o, o
NUM, SYM  = o, o
COL = NUM | SYM
number = float | int   #
atom = number | bool | str  # and sometimes "?"
row = list[atom]
rows = list[row]
classes = dict[str, rows]  # `str` is the class name

# ## CREATE -------------------------------------------------------------------
def SYM(at=0, txt=" ") -> SYM:
  return o(nump=False, n=0, at=at, txt=txt, most=0, mode=None, counts={})

def NUM(at=0, txt=" "): 
  return o(nump=True, n=0, at=at, txt=txt, m2=0, mu=0, sd=0, lo=big, hi=-big,
          goal = 0 if txt[-1] == "-" else 1)

def COLS(names: list[str]) -> COLS:
  all,x,y,nums = [],[],[],[]
  for at,s in enumerate(names):
    col = (NUM if s[0].isupper() else SYM)(at=at, txt=s)
    all += [col]
    if not s[-1] == "X": 
       (y if s[-1] in "+-!" else x).append(col)
  return o(names=names, all=all, x=x, y=y)

def DATA(names, rows=None): 
  return datas(o(rows=[], cols=COLS(names)), rows)

def clone(self:DATA, rows=None):
  return datas(DATA(self.cols.names), rows)

def read(file: str) -> DATA:
  src = csv(file)
  return datas(DATA(next(src)), src)

def merged(i:SYM,j:SYM, n:int) -> SYM:
  k=SYM(at=i.at, txt=i.txt)
  for counts in [i.counts, j.counts]:
    for x,n in counts.items:
      sym(k,x,n)
  if i.n < n or j.n < n: return k
  if ent(k.counts) <= (i.n*ent(i.counts) + j.n*ent(j,counts))/k.n: return k

# ## UPDATE -------------------------------------------------------------------
def adds(self: COL, src):
  [add(self,x) for x in src]
  return self

def add(self: COL, x) -> None:
  return (num if self.nump else sym)(self,x)
 
def num(self:NUM,x):
  if x != "?": 
    self.n += 1
    self.lo = min(x, self.lo)
    self.hi = max(x, self.hi)
    d = x - self.mu
    self.mu += d / self.n
    self.m2 += d * (x - self.mu)
    self.sd = stdev(self)
  return x

def sym(self:SYM, x, n=1):
  if x != "?": 
    self.n += n
    tmp = self.counts[x] = n + self.counts.get(x, 0)
    if tmp > self.most:
      self.most, self.mode = tmp, x
  return x

def subtracts(self:DATA, row:row):
  for col in self.cols.all:
    x = row[col.at]
    if x !="?":
      col.n -= 1
      if col.nump:
        d = x - col.mu
        col.mu -= d / col.n
        col.m2 -= d * (x - col.mu)
        col.sd  = stdev(col)
      else:
        col.counts[x] -= 1

def datas(self:DATA, rows=None):
  [data(self,row) for row in rows or []]
  return self

def data(self:DATA, row):
  self.rows += [row]
  [add(c, row[c.at]) for c in self.cols.all]

# ## QUERY --------------------------------------------------------------------
def norm(self: NUM, x) -> float:
  return x if x == "?" else (x - self.lo)/(self.hi - self.lo + 1/big)

def stdev(self:NUM): return  0 if self.n < 2 else (self.m2/(self.n - 1))**.5

def cdf(self:NUM,x):
 fun = lambda x: 1 - 0.5 * exp(-0.717*x - 0.416*x*x) 
 z = (x - i.mu) / i.sd
 return fun(z) if z>=0 else 1 - fun(-z)

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

def acquire(self: DATA, rows:rows,  eps=0.058, labelled=None, fun=lambda _,b,r:b+b-r):
  "From a model built so far, label next most interesting example. And repeat."
  labelled = labelled or {}
  def Y(a): labelled[id(a)] = a; return ydist(self, a)

  def guess(todo, done, last):
    def score(r): 
      return fun(len(done), like(best, r, len(done), 2),like(rest, r, len(done), 2))
    nBest   = int(len(done)**the.end)
    guesses = min(the.guesses, len(todo)) / len(todo)
    best    = DATA(self.cols.names, done[:nBest])
    rest    = DATA(self.cols.names, done[nBest:])
    return sorted(todo, reverse=True,
                        key=lambda r:last and score(r) or  R()<guesses and score(r) or 0)

  b4   = list(labelled.values())
  m    = max(0, the.start - len(b4))
  todo = rows[m:]
  done = sorted(rows[:m] + b4, key=Y)
  while len(done) < the.Stop:
    top, *todo = guess(todo, done, len(done)==the.Stop - 1)
    done = sorted(done + [top], key=Y)
    if ydist(self, top) <= eps or len(todo) < 3:
      break
  return labelled, done

# ## EXPLAIN ------------------------------------------------------------------
def discretize(col,x):
  return (x=="?" and x) or (not col.nump and x) or (int(the.bins*cdf(col,x)))

class BIN(o):
  def __repr__(self):
    s,lo,hi= self.y.txt, self.lo, self.hi
    if bin.lo==inf   : return f"{s}  < {hi}"
    if bin.lo==bin.hi: return f"{s} == {lo}"
    if bin.hi==inf   : return f"{s} >= {lo}"
    return f"{lo} <= {s} < {hi}"

  def add(self, x,y):
    self.lo = min(x, self.lo)
    self.hi = max(x, self.hi)
    add(self.y, y)

  def accepts(self, row):
    x = row[self.y.at]
    return x=="?" or self.lo == x == self.hi or self.lo <= x < self.hi 

def cuts(self:data, datas:classes):
  out,lo = {}, big
  for col in self.cols.x:
    tmp,N = {},0
    for y,rows in datas.items():
      for row in rows:
        x = row[col.at]
        if x != "?":
          N += 1
          b = discretize(col,x)
          tmp[b] = d.get(b,None) or BIN(lo=x, hi=x, y=SYM(col.at, col.txt))
          tmp[b].add(x, y)
    e = sum(ent(bin.y)*bin.y.n for bin in tmp.values()) / N
    if e < lo:
      lo, out = e, complete(tmp.values(), N/the.bins))
  return out

def complete(col, bins, n):
  if col.nump: 
    for i,bin in enumerate(merges(sorted(bins, key=lambda b: b.lo), n)):
      if i < len(bins): bin.hi = bins[i+1].lo
    bins[ 0].lo = -inf
    bins[-1].hi =  inf
  return sorted(bins, key=lambda b: bin.y.n)

def merges(b4:list[BIN],n) -> list[BIN]: 
  i,now = 0,[]
  while i < len(b4):
    bin = b4[i]
    if i < len(b4) - 1:
      if tmp := merged(bin.y, b4[i+1].y, n)
         bin = BIN(lo=bin.lo, hi=b4[i+1].hi, y=tmp)
         i += 1
    now += [bin]
    i += 1
  return b4 if len(b4)==len(now) else merges(now,n)

class TREE(o): pass

def tree(self:DATA, datas:classes, stop=10, lvl=0, cut=None):
  kids,g = [], {y:len(rows) for y,rows in datas}
  n = sum(d.values())
  if n > stop and ent(d) != 0:
    for one in cuts(self, datas):
      kids += [tree(self, {y:[row for y,rows in datas for row in rows if one.accepts(row)]},
               stop=stop, lvl=lvl+1, cut=one)]
  return TREE(datas=datas, stop=stop, lvl=lvl, cut=cut, kids=kids)

def showDecisions(self: TREE) -> None:
  if self:
    print( f"{'|.. ' * self.lvl}{self.cut}")
    [showDecisions(kid) for kid in kids]

# ## DISTANCE -----------------------------------------------------------------
def xdist(self: DATA, row1: row, row2: row) -> float:
  "Minkowski distance between independent columns of two rows."
  def _sym(_,x,y): return x!=y
  def _num(num1, x, y):
    x, y = norm(num1, x), norm(num1, y)
    x = x if x != "?" else (1 if y < .5 else 0)
    y = y if y != "?" else (1 if x < .5 else 0)
    return abs(x - y)

  n = d = 0
  for c in self.cols.x:
    a, b = row1[c.at], row2[c.at]
    d += 1 if a == b == "?" else (_num if c.nump else _sym)(c, a, b)**the.p
    n += 1
  return (d/n) ** (1/the.p)

def ydist(self: DATA, row) -> float:
  return (sum(abs(c.goal - norm(c, row[c.at]))**the.p 
              for c in self.cols.y)/len(self.cols.y))**1/the.p

def ydists(self: DATA) -> DATA:
  self.rows.sort(key=lambda r: ydist(self, r))
  return self

# ## UTILS --------------------------------------------------------------------
def say(x: any) -> str:
  if isinstance(x, float): 
    return str(x) if int(x) == x else f"{x:.3f}"
  if isinstance(x, list ) : return "["+', '.join([say(y) for y in x])+"]"
  if not isinstance(x, dict): return str(x)
  return "(" + ' '.join(f":{k} {say(v)}"
                        for k, v in x.items() if not str(k)[0] == "_") + ")"

def cli(a:list[str], d:dict) -> None:
  slots = {f"-{k[0]}": k for k in d} 
  for i,s in enumerate(a):
    if s in ["-h", "--help"]: 
      sys.exit(print(__doc__))
    elif s[:2] == "--": 
      getattr(main, s[2:], lambda: print("?",s[2:]))()
    elif s in slots:
      k = slots[s]
      d[k] = coerce(d[k]==True and "False" or d[k]==False and "True" or a[i+1])
      if k=="rseed": random.seed(d[k])

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
    print(sorted([round(like(data1,row,len(data1.rows),2),2)
                   for i,row in enumerate(data1.rows) if i % 20 ==0]))
   
  def xdist():
    data1 = read(the.train)
    print(sorted([round(xdist(data1,row,data1.rows[0]),2)
                   for i,row in enumerate(data1.rows) if i % 20 ==0]))

  def kmeans():
    data1 = read(the.train)
    for data in kmeans(data1): print(mid(data))


  def slash4():
    data1 = read(the.train)
    for row in slash4(data1): print(ydist(data1,row))

  def acquire():
    data1 = read(the.train)
    asIs = NUM()
    asIsS=[]
    for y in  [ydist(data1, row) for row in data1.rows]: add(asIs,y); asIsS += [y]
    for the.Stop in [6,12,24,48]:
      rand, deltas, toBe = NUM(), NUM(), NUM()
      rands, toBes = [],[]
      t1= time.time_ns()
      for _ in range(the.Repeats):
        some = random.choices(data1.rows,k=the.Stop)
        best = ydists(clone(data1,some)).rows[0]
        add(rand, ydist(data1, best))
        rands += [ydist(data1,best)]
        labelled, rows = acquire(data1, shuffle(data1.rows))
        y = ydist(data1, rows[0])
        add(toBe, y)
        toBes += [y]
        add(deltas, (asIs.mu - y)/asIs.sd)
      t2= (time.time_ns() - t1)/the.Repeats // 1000000
      s1,s2=SOME(rands,txt="rand"),SOME(toBes,txt="toBe")
      print(s2.mid()<s1.mid(), s2 != s1, end=" ")

      print(f"{the.Stop} {len(data1.rows)} {len(data1.cols.x)} {len(data1.cols.y)} {len(labelled.values())}",end=" ")
      print(f"{asIs.mu:.2f} {toBe.mu:.2f} {rand.mu:.2f} {asIs.sd*the.cohen:.2f} {toBe.sd:.2f} {rand.sd:.2f} {t2}",end=" ")
      print(the.train.split("/")[-1])

if __name__ == "__main__": cli(sys.argv, the.__dict__)

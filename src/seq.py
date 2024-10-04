#!/usr/bin/env python3.13 -B
"""
seq.py : sequential model optimization (with inital diverse sampling)
(c) 2024 Tim Menzies (timm@ieee.org). BSD-2 license

USAGE: 
  python3 seq.py [OPTIONS]

OPTIONS:   
  -e --end     float leaf cluster size                 = .5
  -f --far     int   samples for finding far points    = 30
  -k --k       int   low frequency Bayes hack          = 1
  -m --m       int   low frequency Bayes hack          = 2
  -p --p       int   distance formula exponent         = 2   
  -s --seed    int   random number seed                = 1234567891   
  -S --Samples int   initial samples                   = 4
  -t --train   str   training csv file. row1 has names = ../../moot/optimize/misc/auto93.csv
  --help print help
"""

from typing import Any as any
from typing import Union,List, Dict, Type, Callable, Generator
from fileinput import FileInput as file_or_stdin
from math import sqrt,log,cos, pi
import random, sys, ast, re
R=random.random
one=random.choice

big = 1E32

class o:
  def __init__(i,**d): i.__dict__.update(**d)
  def __repr__(i): return  i.__class__.__name__ + say(i.__dict__)

number         = float  | int   #
atom           = number | bool | str # and sometimes "?"
row            = list[atom]
rows           = list[row]
classes        = dict[str,rows] # `str` is the class name
NUM,SYM        = o,o
COL            = NUM | SYM
DATA,COLS,TREE = o,o,o

# -----------------------------------------------------------------------------
def SYM(at=0, name=" ") -> SYM:
  return o(isNum=False, at=at, name=name, n=0,
           most=0, mode=None, has={})

def NUM(at=0, name=" ") -> NUM:
  return o(isNum=True,  at=at, name=name, n=0,
           mu=0, m2=0, sd=0, lo=big, hi=-big, goal= 0 if name[-1]=="-" else 1)

def COLS(names: list[str]) -> COLS:
  all,x,y = [],[],[]
  for at,name in enumerate(names):
    a,z  = name[0], name[-1]
    col  = (NUM if a.isupper() else SYM)(at,name)
    all += [col]
    if not z == "X":
      (y if z in "+-!" else x).append(col)
  return o(names=names, all=all, x=x, y=y)

def DATA(names:list[str], src:list|Generator=None) -> DATA:
  data1 = o(rows=[], cols=COLS(names))
  [data(data1,row) for row in src or []]
  return data1

def data(i:DATA, row) -> None:
  i.rows += [row]
  [col(col1, row[col1.at]) for col1 in i.cols.all]

def col(i:COL, x) -> None:
  if x == "?" : return
  i.n += 1
  if not i.isNum:
    tmp = i.has[x] = 1 + i.has.get(x,0)
    if tmp > i.most:
      i.most, i.mode = tmp,x
  else:
    i.lo  = min(x, i.lo)
    i.hi  = max(x, i.hi)
    d     = x - i.mu
    i.mu += d / i.n
    i.m2 += d * (x - i.mu)
    i.sd  = 0 if i.n < 2 else (i.m2/(i.n - 1))**.5

def mid(i:DATA) -> row:
  tmp= [(c.mu if c.isNum else c.mode) for c in i.cols.all]
  return min(i.rows, key=lambda row: xdist(i,row,tmp))

def div(i:DATA) -> list[float]:
  return [(c.sd if c.isNum else ent(c.has)) for c in i.cols.all]

def read(file:str) -> DATA:
  src = csv(file)
  i   = DATA(next(src))
  [data(i,row) for row in src]
  return i

def norm(i:NUM, x) -> float: 
  return x if x=="?" else (x - i.lo)/(i.hi - i.lo + 1/big)

# -----------------------------------------------------------------------------
def xdist(i:DATA, row1:row, row2:row) -> float:
  def sym(_,   x,y): return x != y
  def num(num1, x,y):
    x,y = norm(num1,x), norm(num1,y)
    x   = x if x != "?" else (1 if y < .5 else 0)
    y   = y if y != "?" else (1 if x < .5 else 0)
    return abs(x - y)
  n = d = 0
  for c in i.cols.x:
    a,b = row1[c.at], row2[c.at]
    d  += 1 if a==b=="?" else (num if c.isNum else sym)(c,a,b)**the.p
    n  += 1
  return (d/n) ** (1/the.p)

def ydist(i:DATA, row) -> float:
  return max(abs(c.goal - norm(c, row[c.at])) for c in i.cols.y)

def ydists(i:DATA) -> DATA:
  i.rows.sort(key=lambda r: ydist(i,r))
  return i

class TREE(o): pass

def cluster(data1:DATA, rows=None, sortp=False, all=False, maxDepth=100) -> tuple[TREE,DATA]:
  stop   = len(rows or data1.rows)**the.end
  labels = {}
  def Y(a)  : labels[id(a)] = a; return ydist(data1, a)
  def X(a,b): return xdist(data1, a,b)

  def cut(rows, above=None):
    l,r  = max([(above or one(rows), one(rows)) for _ in range(the.far)], key=lambda z:X(*z))
    l,r  = (r,l) if sortp and Y(r) < Y(l) else (l,r)
    C    = X(l,r)
    rows = sorted(rows, key=lambda row:(X(row,l)**2 + C**2 - X(row,r)**2)/(2*C + 1/big))
    n    = int(len(rows) // 2)
    return rows[:n], l, rows[n:], r

  def nodes(rows, above=None, lvl=0, guard=None):
    if len(rows) >= stop and lvl < maxDepth:
      ls, l, rs, r = cut(rows, above)
      data2 = DATA(data1.cols.names, rows) 
      return TREE(
        data  = data2, 
        y     = ydist(data1, l),
        lvl   = lvl, 
        guard = guard, 
        left  = nodes(ls, l, lvl+1, lambda row: X(row,ls[-1]) <  X(row,rs[0])),
        right = nodes(rs, r, lvl+1, lambda row: X(row,ls[-1]) >= X(row,rs[0])) if all else None)

  return (nodes(rows or data1.rows), # tree 
          ydists(DATA(data1.cols.names, labels.values()))) # items labelled while making tree

def showTree(t:TREE) -> None:
  if t:
    mid1 = mid(t.data)
    s1 = ', '.join([f"{mid1[c.at]:6.2f}"  for c in t.data.cols.y])
    s2 = f"{'|.. ' * t.lvl}{len(t.data.rows):>4}" 
    print(f"{t.y:.2f} | {s1:20} {s2}")
    [showTree(t.__dict__.get(kid,None)) for kid in ["left", "right"]]

# -----------------------------------------------------------------------------
def like(i:DATA, row:row, nall:int, nh:int) -> float:
  def sym(sym1, x, prior):
    return (sym1.has.get(x,0) + the.m*prior) / (sym1.n + the.m)
  
  def num(num1, x,_):
    v     = num1.sd**2 + 1E-30
    nom   = exp(-1*(x - num1.mu)**2/(2*v)) + 1E-32
    denom = (2*pi*v) ** 0.5
    return min(1, nom/(denom + 1E-32))

  prior = (len(i.rows) + the.k) / (nall + the.k*nh)
  likes = [(num if c.isNum else sym)(row[c.at], prior) for c in i.cols.x]
  return sum(log(x) for x in likes + [prior] if x>0)

def acquire(i:DATA, rows:rows, labels=None, score=Callable) -> rows:
  labels = labels or {}
  done   = labels.values()
  def Y(a): labels[id(a)] = a; return ydist(i, a)

  def guess(todo, done):
    nBest = int(sqrt(len(done)))
    nUse  = min(the.some,len(todo))/len(todo))
    best  = DATA(i.cols.names, done[:nBest])
    rest  = DATA(i.cols.names, done[nBest:])
    key   = lambda row: 0 if R() > nUse else score(like(best, row, len(done), 2), 
                                                   like(rest, row, len(done), 2))
    return sort(todo, key=key)

  m = max(0, the.start - len(done))
  done += rows[:m]
  done.sort(key=Y)
  todo  = rows[m:]
  while len(done) < the.stop:
    top, *todo = guess(todo, done) 
    done += [top]
    done.sort(key=Y)
  return done
  
## -----------------------------------------------------------------------------
def ent(d:dict) -> float:
 N = sum(d.values())
 return [n/N*log(n/N,2) for n in d.values()]

def say(x:any) -> str:
  if isinstance(x,float)   : return f"{x:.3f}"
  if isinstance(x,list )   : return "["+', '.join([say(y) for y in x])+"]"
  if not isinstance(x,dict): return str(x)
  return "(" + ' '.join(f":{k} {say(v)}"
                        for k,v in x.items() if not str(k)[0]=="_") + ")"

def coerce(s:str) -> atom:
  try: return ast.literal_eval(s)
  except Exception: return s

def csv(file:str) -> Generator:
  with file_or_stdin(None if file=="−" else file) as src:
    for line in src:
      line = re.sub(r"([\n\t\r ]|\#.*)", "", line)
      if line:
        yield [coerce(s.strip()) for s in line.split(",")]

def normal(mu:float,sd:float) -> float: 
    return mu+sd*sqrt(-2*log(R())) * cos(2*pi*R())

def shuffle(lst:list) -> list:
  random.shuffle(lst)
  return lst

def cli(d:dict) -> None:
  for k,v in d.items():
    for c,arg in enumerate(sys.argv):
      if arg=="-h": sys.exit(print(__doc__ or ""))
      if arg in ["-"+k[0], "--"+k]:
        d[k] = coerce(sys.argv[c+1])
        if k=="seed": random.seed(d[k])

# -----------------------------------------------------------------------------
class go:
  def help(_): print(__doc__)

  def num(_):
    r = 256
    num1 = NUM()
    [col(num1, normal(10,2)) for _ in range(r)]
    assert 9.95 < num1.mu < 10 and 2 < num1.sd < 2.05,"go.num"

  def data(_):
    data1 = read(the.train)
    [print(col) for col in data1.cols.x]

  def xdist(_):
    data1 =  read(the.train)
    random.shuffle(data1.rows)
    d = lambda r:xdist(data1,data1.rows[0],r)
    for i,row in enumerate(sorted(data1.rows, key=d)):
      if i % 30 == 0: print(f"{d(row):.3f}",row)

  def ydist(_):
    data1 = read(the.train)
    random.shuffle(data1.rows)
    for i,row in enumerate(ydists(data1).rows):
      if i % 30 == 0: print(f"{ydist(data1,row):.3f}",row)

  def branch(_):
    data1 = ydists(read(the.train))
    n =  int(len(data1.rows)//2)
    print(f"{ydist(data1, data1.rows[n]):.3}")
    _,labels=cluster(data1,sortp=True,maxDepth=4, all=False)
    print(f"{ydist(data1, labels.rows[0]):.3}")

  def tree(_):
    data1 = read(the.train)
    tree1,_=cluster(data1,sortp=True,all=True,maxDepth=4)
    showTree(tree1)

# -----------------------------------------------------------------------------
the = o(**{m[1]:coerce(m[2]) for m in 
           re.finditer(r"\n\s*-\w+\s*--(\w+).*=\s*(\S+)", __doc__)})
cli(the.__dict__)
random.seed(the.seed)

for i,s in enumerate(sys.argv):
  if s[:2] == "--":
    getattr(go, s[2:], lambda :1)(i)

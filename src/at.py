#!/usr/bin/env python3.13 -B
"""
- Functions with UP CASE names; e.g. `DATA`.
- Instances have constructor names, plus a number; e.g. `data1`.
- Functions with down case names are updaters; e.g. `data(data1,row)`
"""
from fileinput import FileInput as file_or_stdin
from math import sqrt,log,cos, pi
import random, sys, ast, re
R=random.random
one=random.choice

big = 1E32

class o:
  def __init__(i,**d): i.__dict__.update(**d)
  def __repr__(i): return  i.__class__.__name__ + say(i.__dict__)

the = o(end     = .5,
        far     = 30,
        p       = 2,
        Samples = 4,
        seed    = 1234567891,
        train   = "../../moot/optimize/misc/auto93.csv")

# -----------------------------------------------------------------------------
def SYM(at=0, name=" "):
  return o(isNum=False, at=at, name=name, n=0,
           most=0, mode=None, has={})

def NUM(at=0, name=" "):
  return o(isNum=True,  at=at, name=name, n=0,
           mu=0, m2=0, sd=0, lo=big, hi=-big, goal= 0 if name[-1]=="-" else 1)

def COLS(names):
  all,x,y = [],[],[]
  for at,name in enumerate(names):
    a,z  = name[0], name[-1]
    col  = (NUM if a.isupper() else SYM)(at,name)
    all += [col]
    if not z == "X":
      (y if z in "+-!" else x).append(col)
  return o(names=names, all=all, x=x, y=y)

def DATA(names, src=None):
  data1 = o(rows=[], cols=COLS(names))
  [data(data1,row) for row in src or []]
  return data1

def data(data1, row):
  data1.rows += [row]
  [col(col1, row[col1.at]) for col1 in data1.cols.all]

def col(col1, x):
  if x == "?" : return
  col1.n += 1
  if not col1.isNum:
    tmp = col1.has[x] = 1 + col1.has.get(x,0)
    if tmp > col1.most:
      col1.most, col1.mode = tmp,x
  else:
    col1.lo  = min(x, col1.lo)
    col1.hi  = max(x, col1.hi)
    d        = x - col1.mu
    col1.mu += d / col1.n
    col1.m2 += d * (x - col1.mu)
    col1.sd  = 0 if col1.n < 2 else (col1.m2/(col1.n - 1))**.5

def mid(data1):
  tmp= [(col1.mu if col1.isNum else col1.mode) for col1 in data1.cols.all]
  return min(data1.rows, key=lambda row: xdist(data1,row,tmp))

def div(data1):
  return [(col1.sd if col1.isNum else ent(col1.has)) for col1 in data1.cols.all]

def read(file):
  src = csv(file)
  data1 = DATA(next(src))
  [data(data1,row) for row in src]
  return data1

def norm(num1, x):
  return x if x=="?" else (x - num1.lo)/(num1.hi - num1.lo + 1/big)

# -----------------------------------------------------------------------------
def xdist(data1,row1,row2):
  def sym(_,   x,y): return x != y
  def num(num1,x,y):
    x,y = norm(num1,x), norm(num1,y)
    x   = x if x != "?" else (1 if y < .5 else 0)
    y   = y if y != "?" else (1 if x < .5 else 0)
    return abs(x - y)
  n = d = 0
  for col1 in data1.cols.x:
    a,b = row1[col1.at], row2[col1.at]
    d  += 1 if a==b=="?" else (num if col1.isNum else sym)(col1,a,b)**the.p
    n  += 1
  return (d/n) ** (1/the.p)

def ydist(data1,row, used=None):
  if used is not None: used[id(row)] = row
  return max(abs(col.goal - norm(col, row[col.at])) for col in data1.cols.y)

def ydists(data1, used=None):
  data1.rows.sort(key=lambda row: ydist(data1,row,used))
  return data1

def WALK(data1, sortp=True):
  return o(data=data1, used={}, sortp=sortp,
           stop=log(len(data1.rows)/ (len(data1.rows)**the.end),2))

def half(walk1, rows, top=None):
  def Y(a)         : return ydist(walk1.data, a, walk1.used)
  def X(a,b)       : return xdist(walk1.data, a,b)
  def cos(r,a,b,C) : return (X(r,a)**2 + C**2 - X(r,b)**2)/(2*C + 1/big)
  top  = top or one(rows)
  a,b  = max([(top, one(rows)) for _ in range(the.far)], key=lambda z:X(*z))
  a,b  = (b,a) if walk1.sortp and Y(b) < Y(a) else (a,b)
  C    = X(a,b)
  rows = sorted(rows, key=lambda r:cos(r,a,b,C))
  n    = int(len(rows) // 2)
  return rows[:n], rows[n:],a,b

def tree(walk1, rows=None, lvl=0, top=None):
  rows = rows or walk1.data.rows
  if lvl>=walk1.stop or len(rows)<4: return DATA(walk1.data.cols.names, rows) 
  lefts, rights, left, right = half(walk1, rows, top)
  return o(data  = DATA(walk1.data.cols.names,rows), lvl=lvl, cut=rights[0],
           left  = None if lvl >= walk1.stop else tree(walk1, lefts,  lvl+1, left),
           right = None if lvl >= walk1.stop else tree(walk1, rights, lvl+1, right))

def slash(walk1, rows=None, lvl=0, top=None):
  rows = rows or walk1.data.rows
  if lvl>=walk1.stop or len(rows)<4: return DATA(walk1.data.cols.names, rows),top 
  lefts, rights,left,right = half(walk1, rows, top)
  return slash(walk1, lefts, lvl+1, left)

def showTree(data1, tree1):
  if tree1:
    print(f"{ydist(data1, mid(tree1.data)):.3f}    ", end="")
    print(f"{'|.. ' * tree1.lvl}{len(tree1.data.rows)}" )
    for kid in ["left", "right"]:
      showTree(data1, tree1.__dict__.get(kid,None))

# -----------------------------------------------------------------------------
def ent(d):
 N = sum(d.values())
 return [n/N*log(n/N,2) for n in d.values()]

def say(x) -> str:
  if isinstance(x,float)   : return f"{x:.3f}"
  if isinstance(x,list )   : return "["+', '.join([say(y) for y in x])+"]"
  if not isinstance(x,dict): return str(x)
  return "(" + ' '.join(f":{k} {say(v)}"
                        for k,v in x.items() if not str(k)[0]=="_") + ")"

def coerce(s):
  try: return ast.literal_eval(s)
  except Exception: return s

def csv(file):
  with file_or_stdin(None if file=="−" else file) as src:
    for line in src:
      line = re.sub(r"([\n\t\r ]|\#.*)", "", line)
      if line:
        yield [coerce(s.strip()) for s in line.split(",")]

def normal(mu,sd): return mu+sd*sqrt(-2*log(R())) * cos(2*pi*R())

def shuffle(lst):
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

  def half(_):
    data1 = read(the.train)
    walk1 = WALK(data1)
    lefts,rights = half(walk1, data1.rows)
    print(len(lefts), len(rights), walk1.used.keys())

  def tree(_):
    data1 = read(the.train)
    walk1 = WALK(data1)
    print(walk1.stop)
    showTree(data1, tree( walk1))

  def slash(_):
    for _ in range(20):
      data1 = read(the.train)
      walk1 = WALK(data1)
      data2,top= slash(walk1, data1.rows)
      print(f"{len(data2.rows)} {ydist(data1, top, walk1.used):.3f}, {len(walk1.used.values()):>3}")
    #print(len(data2.rows), len(walk1.used.values()),ydist(data2, data2.rows[0], walk1.used))

# -----------------------------------------------------------------------------
cli(the.__dict__)
random.seed(the.seed)
for i,s in enumerate(sys.argv):
  if s[:2] == "--":
    getattr(go, s[2:], lambda :1)(i)

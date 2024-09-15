"""
less.py

In this code UPPERCASE functions are constrictors and lowercase
versions of that constructor are functions that add one item and
lowercase plus a "s" add multiple items. e.g. DATA, SYM and constructors
and data,sym are functions to add one iteam to a DATA or a SYM.
And datas adds may rows.
"""
from time import time_ns as nano
import random,math,sys,ast,re,os
from fileinput import FileInput as file_or_stdin
R, cos, log, sqrt = random.random, math.cos, math.log, math.sqrt

class o:
  def __init__(i,**d): i.__dict__.update(**d)
  def __repr__(i): return  i.__class__.__name__ + pretty(i.__dict__)

the = o( 
  buckets = 10, 
  p       = 2, 
  seed    = 1234567891, 
  train   = "../../moot/optimize/misc/auto93.csv"
)

def DATA(): 
  return o(rows=[], cols=o(names=[],nums=[],syms=[],all=[],x=[],y=[]))

def SYM(c=0, x=" "): return o(This=SYM, c=c, txt=x, n=0, has={})
def NUM(c=0, x=" "): return o(This=NUM, c=c, txt=x, n=0, 
                              mu=0, m2=0, sd=0, lo=1E32, hi=-1E32, 
                              goal = 0 if x[-1]=="-" else 1)

def CLUSTER(mid,data): return o(This=CLUSTER, data=data, mid=mid, nearest=1E32, close=None)

def sym(i,v): 
  i.n += 1
  i.has[v] = 1 + i.has.get(v,0)

def num(i,v):
  i.n += 1
  i.lo = min(v, i.lo)
  i.hi = max(v, i.hi)
  d = v - i.mu
  i.mu += d / i.n
  i.m2 += d * (v - i.mu)
  i.sd = 0 if i.n < 2 else (i.m2/(i.n - 1))**.5 

def data(i,row):
  def goalp(v):  return v[-1] in "+-!"
  def nump(v):   return v[0].isupper()
  def ignorep(v): return v[-1] == "X"
  def head(c,v):
    col = (NUM if nump(v) else SYM)(c,v)
    i.cols.all.append(col)
    if not ignorep(v):
      (i.cols.y    if goalp(v) else i.cols.x   ).append(col)
  if i.cols.all == []:
    i.cols.names = row
    [head(c,v) for c,v in enumerate(row)]
  else:
    i.rows += [row]
    for cols in [i.cols.x, i.cols.y]:
      for col in cols:
        v = row[col.c]
        if v != "?":
          (sym if col.This is SYM else num)(col, v)
  return i
    
def datas(i,src): [data(i,row) for row in src]; return i
def mids(data)  : return [mid(col) for col in data.cols.all]
def mid(i)      : return i.mu if i.This is NUM else max(i.has,key=i.has.get)
def norm(i,x)   : return x if x=="?" else (x - i.lo) / (i.hi - i.lo + 1E-32)

def clone(i,rows=[]):
  return datas(data(DATA(), i.cols.names),rows)

def xDist(data, row1, row2):
  def dist(x,a,b):
    if a=="?" and b=="?": return 1
    if x.This is SYM: return a != b
    a, b = norm(x,a), norm(x,b)
    a = a if a != "?" else (1 if b<.5 else 0)
    b = b if b != "?" else (1 if a<.5 else 0)
    return abs(a - b)
  d = sum(dist(x, row1[x.c], row2[x.c])**the.p for x in data.cols.x)
  return d**(1/the.p) / len(data.cols.x)**(1/the.p)

def yDist(data, row):
 return max(abs(y.goal - norm(y,row[y.c])) for y in data.cols.y)

def kmeans(data1, k=16, loops=10, samples=512):
  samples = min(len(data1.rows),samples)
  rows = random.choices(data1.rows, k=samples)
  def loop(loops, centroids):
    d = {}
    for row in rows:
      k = id(min(centroids, key=lambda r: xDist(data1,r,row)))
      d[k] = d.get(k,None) or clone(data1)
      data(d[k],row)
    return loop(loops-1, [mids(data2) for data2 in d.values()]) if loops else d.values()
  return loop(loops, rows[:k])

#-----------------------------------------------------------------------
def pretty(x):
  if isinstance(x,float)   : return f"{x:.3f}"
  if isinstance(x,list )   : return "["+', '.join([pretty(y) for y in x])+"]"
  if not isinstance(x,dict): return str(x)
  return "(" + ' '.join(f":{k} {pretty(v)}" 
                        for k,v in x.items() if not str(k)[0].isupper()) + ")"

def coerce(s):
  try: return ast.literal_eval(s)
  except Exception: return s

def csv(file):
  with file_or_stdin(None if file=="−" else file) as src: 
    for line in src: 
      line = re.sub(r"([\n\t\r ]|\#.*)", "", line)
      if line: 
        yield [coerce(s.strip()) for s in line.split(",")]

def cli(d):
  for k,v in d.items():
    for c,arg in enumerate(sys.argv):
      if arg=="-h": sys.exit(print(__doc__ or "")) 
      if arg in ["-"+k[0], "--"+k]: 
        d[k] = coerce(sys.argv[c+1])
        if k=="seed": random.seed(d[k])

#-----------------------------------------------------------------------
class eg:
  def the(_): print(the)

  def csv(_): 
   for i,row in enumerate(csv(the.train)):
     if i % 30 == 0: print(i,row)

  def datas(_): 
    d = datas(DATA(),csv(the.train))
    print(mids(d))
    for col in d.cols.y:
      print(col)

  def clones(_): 
    d1 = datas(DATA(),csv(the.train))
    d2 = datas(clone(d1),d1.rows)
    for col in d1.cols.x: print(col)
    print("")
    for col in d2.cols.x: print(col)

  def kmeans(_): 
    d = datas(DATA(),csv(the.train))
    print(pretty(sorted([yDist(d, mids(x)) for x in kmeans(d)])))

  def kmeans2(_): 
    d         = datas(DATA(),csv(the.train))
    n=NUM()
    [num(n,yDist(d,x)) for x in d.rows]
    print(f"mu= {n.mu:.3f}, 'zero'= {n.lo+0.35*n.sd:.3f}")
    fun       = lambda d1:yDist(d, mids(d1))
    k1=12; k2=6; k3=6
    for _ in range(20):
      clusters1 = kmeans(d, k=k1)
      rows1     = sorted(clusters1, key=fun)[0].rows
      clusters2 = kmeans(clone(d,rows1),k=k2)
      rows2     = sorted(clusters2, key=fun)[0].rows
      random.shuffle(rows2)
      row       = sorted(rows2[:k3], key=lambda r:yDist(d,r))[0]
      print(f"{yDist(d,row):.3f}",k1+k2+k3,row,sep="\t")

#-----------------------------------------------------------------------
random.seed(the.seed)
cli(the.__dict__)
for i,s in enumerate(sys.argv):
  getattr(eg,s[1:], lambda _:_)(i+1)

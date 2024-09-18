"""
mink,py: multi-objective optimization, using very few y labels.  
(c) 2024, Tim Menzies <timm@ieee.org>, MIT license

     k1=k2=k3=10   # total labels = k1+k2+k3
     rows = all rows
     for k in [k1,k2]:
        find k clusters within the rows (using kmeans)
        sort(cluster centroids, ascending on yDist)
        rows = rows of best cluster
     rows = sort(any k3 items of rows, ascending on yDist)
     return rows[0]

In this code "i" refers to "self" and methods are grouped by function,
not by class name (so, e.g. all the distance methods are together).

"""
# -----------------------------------------------------------------------
# ## Some setup.
from typing import List, Dict, Type, Callable, Generator, Iterator
import inspect,random,math,sys,ast,re
from time import time_ns as nano
from fileinput import FileInput as file_or_stdin

# My types
number  = float  | int   #
atom    = number | bool | str # and sometimes "?"
row     = list[atom]
rows    = list[row]
classes = dict[str,rows] # `str` is the class name

# A class for associative arrays.
class o:
  def __init__(i,**d): i.__dict__.update(**d)
  def __repr__(i)    : return  i.__class__.__name__ + say(i.__dict__)
  def adds(i,lst=[]) : [i.add(x) for x in lst]; return i

# My global settings
the = o(
  buckets = 10,
  p       = 2,
  seed    = 1234567891,
  train   = "../../moot/optimize/misc/auto93.csv"
)

# -----------------------------------------------------------------------
# ## Misc utils

# Update dictionary via cli flag that match d's slots.
def cli(d:dict) -> None:
  for k,v in d.items():
    for c,arg in enumerate(sys.argv):
      if arg=="-h": sys.exit(print(__doc__ or "")) 
      if arg in ["-"+k[0], "--"+k]: 
        d[k] = coerce(sys.argv[c+1])
        if k=="seed": random.seed(d[k])

# String to atom.
def coerce(s:str) -> atom:
  try: return ast.literal_eval(s)
  except Exception: return s

# Iterate over csv file.
def csv(file:str) -> Iterator[row]:
  with file_or_stdin(None if file=="−" else file) as src: 
    for line in src:
      line = re.sub(r"([\n\t\r ]|\#.*)", "", line)
      if line:
        yield [coerce(s.strip()) for s in line.split(",")]

# Diversity of a set of symbol counts
def ent(d:dict):
  N = sum(n for n in d.values())
  return -sum(n/N * math.log(n/N,2) for n in d.values())

# Allow methods to be listed outside of the class XX: construct.
def of(cat,doc):
  def doit(fun):
    fun.__doc__ = doc
    setattr(inspect.getfullargspec(fun).annotations['i'],fun.__name__, fun)
  return doit

# Generates a string showing a recursive pretty print.
def say(x) -> str:
  if isinstance(x,float)   : return f"{x:.3f}"
  if isinstance(x,list )   : return "["+', '.join([say(y) for y in x])+"]"
  if not isinstance(x,dict): return str(x)
  return "(" + ' '.join(f":{k} {say(v)}" for k,v in x.items() if not str(k)[0]=="_") + ")"

# -----------------------------------------------------------------------
# ## Classes and methods.

# ### Create

class COL(o): ...

# Summarize a stream of symbols.
class SYM(COL):
  def __init__(i,c=0,x=" "): i.c=c; i.txt=x; i.n=0; i.has={}

# Summarize a stream of numbers.
class NUM(COL):
  def __init__(i,c=0, x=" "):
    i.c=c; i.txt=x; i.n=0; i.mu=0; i.m2=0; i.sd=0;
    i.lo=1E32; i.hi=-1E32; i.goal = 0 if x[-1]=="-" else 1

# Store rows, summarized into columns.
class DATA(o):
  def __init__(i): i.rows=[]; i.cols=o(names=[],all=[],x=[],y=[])

@of("CREATE","make a new data, copying the structure of an old one")
def clone(i:DATA, rows:list=[]) -> DATA:
  return DATA().add(i.cols.names).adds(rows)

# ### Update

@of("UPDATE","increment symbol counts")
def add(i:SYM,v:atom, n=1):
  i.n += n
  i.has[v] = n + i.has.get(v,0)

@of("UPDATE","increment numeric summary")
def add(i:NUM, v:atom):
  i.n  += 1
  i.lo  = min(v, i.lo)
  i.hi  = max(v, i.hi)
  d     = v - i.mu
  i.mu += d / i.n
  i.m2 += d * (v - i.mu)
  i.sd  = 0 if i.n < 2 else (i.m2/(i.n - 1))**.5

@of("UPDATE","increment a DATA with one new row")
def add(i:DATA, row:row):
  def nump(v)   : return v[0].isupper()
  def goalp(v)  : return v[-1] in "+-!"
  def ignorep(v): return v[-1] == "X"
  def create(c,v):
    col = (NUM if nump(v) else SYM)(c,v)
    i.cols.all += [col]
    if not ignorep(v):
      (i.cols.y if goalp(v) else i.cols.x).append(col)

  if i.cols.names: # true if we have already seen the header row
    i.rows += [row]
    [col.add(row[col.c]) for col in i.cols.all if row[col.c] != "?"]
  else:
    i.cols.names = row
    [create(c,v) for c,v in enumerate(row)]
  return i

# ### Query

@of("QUERY","mode = middle of symbolic distributions")
def mid(i:SYM): return max(i.has, key=i.has.get)

@of("QUERY","mean = middle of numeric distributions")
def mid(i:NUM): return i.mu

@of("QUERY","the middle of a numeric distribution is its mean")
def norm(i:NUM, x:atom): #  -> 0..1 
  return x if x=="?" else (x - i.lo) / (i.hi - i.lo + 1E-32)

@of("QUERY","map numbers 0..1 for min..max")
def mid(i:DATA): return [col.mid() for col in i.cols.all]

@of("QUERY","cumulative distribution")
def cdf(i:NUM,x):
  fun = lambda x: 1 - 0.5 * math.exp(-0.717*x - 0.416*x*x) 
  z   = (x - i.mu) / i.sd
  return  fun(x) if z>=0 else 1 - fun(-z) 

# ### Distance

@of("DISTANCE","between two symbols")
def dist(i:SYM, a:atom, b:atom): return 1 if a==b=="?" else a != b

@of("DISTANCE","between two numbers")
def dist(i:NUM, a:number, b:number) -> number:
  if a==b=="?": return 1
  a, b = i.norm(a), i.norm(b)
  a = a if a != "?" else (1 if b<.5 else 0)
  b = b if b != "?" else (1 if a<.5 else 0)
  return abs(a - b)

@of("DISTANCE","between two rows (x-value Minkowski)")
def xDist(i:DATA, row1:row, row2:row) -> number:
    d = sum(col.dist(row1[col.c], row2[col.c])**the.p for col in i.cols.x)
    return d**(1/the.p) / len(i.cols.x)**(1/the.p)

@of("DISTANCE","max distance of goals to best goals (Chebyshev)")
def yDist(i:DATA, row:number) -> number:
  return max(abs(y.goal - y.norm(row[y.c])) for y in i.cols.y)

@of("DISTANCE","guess centroids, move rows to nearest guess, update guess, repeat")
def kmeans(i:DATA, k=10, n=10, samples=512):
  def loop(n, centroids):
    datas = {}
    for row in rows:
      k = id(min(centroids, key=lambda centroid: i.xDist(centroid,row)))
      datas[k] = datas.get(k,None) or i.clone()
      datas[k].add(row)
    return datas.values() if n==0 else loop(n-1, [d.mid() for d in datas.values()])

  random.shuffle(i.rows)
  rows = i.rows[:samples]
  return loop(n, rows[:k])

# -----------------------------------------------------------------------
# ## Discretization

# Summarize symbols seen in column y, within the span lo..hi of numeric column x.
class BIN(SYM):
  def __init__(i,*l,**d):
    super().__init__(*l,**d)
    i.span=o(lo=1E32, hi=-1E32)

@of("UPDATE","add to a  span")
def addxy(i:BIN,x,y):
  i.add(y)
  i.span.lo = min(x, i.span.lo)
  i.span.hi = max(x, i.span.hi)

@of("Query","selects")
def addxy(i:BIN, row):
  v=  row[i.c] 
  return v=="?" or i.span.lo <= v < i.span.hi

@of("CREATE","Combine two BINs if too small or complex. Else return nil.")
def combined(i:BIN, j:BIN, tiny=10):
  k = BIN(i.c,i.txt)
  k.span = o(lo = min(i.span.lo,j.span.lo), 
             hi = max(i.span.hi, j.span.hi))
  [k.add(x,n) for has in [i.has, j.has] for x,n in has.items()]
  xpect = (i.n*ent(i.has) + j.n*ent(j.has))/k.n
  if i.n < tiny or j.n < tiny or ent(k.has) <= xpect:
    return k

@of("DISCRETIZE","generate bins")
def bins(i:COL, groups: dict[str,list]): # -> list[SYM]:
  n,bins = 0,{}
  for y,rows in groups.items():
    for row in rows:
      x = row[i.c]
      if x != "?" :
        n     += 1
        b      = i.bin(x)
        bins[b] = bins.get(b,None) or BIN(i.c, i.txt)
        bins[b].addxy(x,y)
  bins = i.merges(sorted(bins.values(), key=lambda xy:xy.span.lo), n/the.buckets)
  w = sum(bin.n * ent(bin.has) for bin in bins)/n
  return w,bins

@of("DISCRETIZE","map a number to a few values")
def bin(i:NUM, x:atom): return int(i.cdf(x)*the.buckets)

@of("DISCRETIZE","symbols discretize to themselves")
def bin(i:SYM, x):  return x

@of("DISCRETIZE","symbolic bins  discretize to themselves")
def merges(i:SYM, bins, _): return bins

@of("DISCRETIZE","fuse together adjacent bins that can be combined.")
def merges(i:NUM,bins, tiny):
  out = [bins[0]]
  for j,bin in enumerate(bins):
    if j>=0:
      if combined := bin.combined(out[-1], tiny):
        out[-1] = combined
      else:
        out += [bin]
  out[ 0].span.lo = -math.inf
  out[-1].span.hi =  math.inf
  for j,bin in enumerate(out):
    if j>0:
      bin.span.lo = out[j-1].span.hi
  return out

# -----------------------------------------------------------------------

  

# -----------------------------------------------------------------------
# ## Main

# All these methods can be called from command-line; e.g. -csv runs `main.csv()`.
class main:
  def the(): print(the)

  def csv():
   for i,row in enumerate(csv(the.train)):
     if i % 30 == 0: print(i,row)

  def datas():
    d = DATA().adds(csv(the.train))
    print(d.mid())
    for col in d.cols.y:
      print(col)

  def clones():
    d1 = DATA().adds(csv(the.train))
    d2 = d1.clone(d1.rows)
    for col in d1.cols.x: print(col)
    print("")
    for col in d2.cols.x: print(col)

  def kmeans():
    d = DATA().adds(csv(the.train))
    print(say(sorted([d.yDist(d2.mid()) for d2 in d.kmeans()])))

  def kmeans2():
    repeats=20
    d   = DATA().adds(csv(the.train))
    n0  = NUM().adds([d.yDist(row) for row in d.rows])
    fun = lambda d1:d.yDist(d1.mid())
    k1=k2=k3=10
    print("# ",the.train)
    print("#best","#","rept","asIs","zero", "rand", "(sd)","row",sep="\t| ")
    for _ in range(repeats):
      n=NUM().adds(d.yDist(r) for r in d.clone(random.choices(d.rows,k=k1+k2+k3)).rows)
      clusters1 = d.kmeans(k=k1)
      rows1     = sorted(clusters1, key=fun)[0].rows
      clusters2 = d.clone(rows1).kmeans(k=k2)
      rows2     = sorted(clusters2, key=fun)[0].rows
      random.shuffle(rows2)
      row       = sorted(rows2[:k3], key=lambda r:d.yDist(r))[0]
      print(f"{d.yDist(row):.2f}",k1+k2+k3,repeats,
            f"{n0.mu:.2f}\t| {n0.lo+0.35*n0.sd:.2f}",
            f"{n.mu:.2f}\t| {n.sd:.2f}",row,the.train,sep="\t| ")

  def weight():
    d = DATA().adds(csv(the.train)); # print(d.div())
    groups = {chr(j+65): data.rows for j,data in  enumerate(d.kmeans())}
    for w,bins in sorted(col.bins(groups) for col in d.cols.x):
      print("")
      print("expected entropy if dividing on this feature:",say(w))
      for bin in bins:
        print("\t",bin.txt,bin.span)

# -----------------------------------------------------------------------
# ## Starting-ip
random.seed(the.seed)

if __name__ == "__main__":
  cli(the.__dict__)
  for i,s in enumerate(sys.argv):
    getattr(main, s[1:], lambda:1)()

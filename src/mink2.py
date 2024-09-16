#                                      __         
#                   __                /\ \        
#      ___ ___     /\_\        ___    \ \ \/'\    
#    /' __` __`\   \/\ \     /' _ `\   \ \ , <    
#    /\ \/\ \/\ \   \ \ \    /\ \/\ \   \ \ \\`\  
#    \ \_\ \_\ \_\   \ \_\   \ \_\ \_\   \ \_\ \_\
#     \/_/\/_/\/_/    \/_/    \/_/\/_/    \/_/\/_/

"""
mink,py: multi-objective optmization, using very few samples of y labels.
(c) 2024, Tim Menzies <timm@ieee.org>, MIT license

- Run K-means (on the x columns), to find clusters1.
- Sort clusters1 by the yDist of their mid. Select best cluster
- Run K-means on the  rows of the best cluster rows
  yDist on their mid. Apply k-means to the  best cluster to find clusters2
  Select the best cluster.
- Sort some random items from best cluster. Return best one.

In this code:
- UPPERCASE functions are constrictors
- lowercase versions of that constructor name are functions that add 1 item
- lowercase plus a "s" add multiple items

e.g. 
- DATA, SYM, NUM are constructors
- `data`, `sym`, `num` are functions that add 1 item to DATA,SYM or NUM
- `datas` is a function that adds many rows to DATA

"""
from typing import List, Dict, Type, Callable, Generator
import random,sys,ast,re
from time import time_ns as nano
from fileinput import FileInput as file_or_stdin

class o:
  "A class for associative arrays"
  def __init__(i,**d): i.__dict__.update(**d)
  def __repr__(i)    : return  i.__class__.__name__ + pretty(i.__dict__)
  def adds(i,lst=[]) : [i.add(x) for x in lst]; return i

#-----------------------------------------------------------------------
number  = float  | int   #
atom    = number | bool | str # and sometimes "?"
row     = list[atom]
rows    = list[row]
classes = dict[str,rows] # `str` is the class name

the = o(
  buckets = 10,
  p       = 2,
  seed    = 1234567891,
  train   = "../../moot/optimize/misc/auto93.csv"
)

#-----------------------------------------------------------------------
#  |  o  |_   ._   _.  ._     
#  |  |  |_)  |   (_|  |   \/ 
#                          /  

def pretty(x) -> str:
  "pretty print"
  if isinstance(x,float)   : return f"{x:.3f}"
  if isinstance(x,list )   : return "["+', '.join([pretty(y) for y in x])+"]"
  if not isinstance(x,dict): return str(x)
  return "(" + ' '.join(f":{k} {pretty(v)}" 
                        for k,v in x.items() if not str(k)[0].isupper()) + ")"

def coerce(s:str) -> atom:
  "string to atom"
  try: return ast.literal_eval(s)
  except Exception: return s

def csv(file:str): #-> Generator[row]:
  "Iterate over csv file"
  with file_or_stdin(None if file=="−" else file) as src: 
    for line in src: 
      line = re.sub(r"([\n\t\r ]|\#.*)", "", line)
      if line: 
        yield [coerce(s.strip()) for s in line.split(",")]

def cli(d:dict) -> None:
  "update dictionary by looking for cli flafs that match d's slits"
  for k,v in d.items():
    for c,arg in enumerate(sys.argv):
      if arg=="-h": sys.exit(print(__doc__ or "")) 
      if arg in ["-"+k[0], "--"+k]: 
        d[k] = coerce(sys.argv[c+1])
        if k=="seed": random.seed(d[k])
#-----------------------------------------------------------------------
#   _      ._ _  
#  _>  \/  | | | 
#      /         

class SYM(o):
  "summarize a stream of numbers"
  def __init__(i,c=0,x=" "): i.c=c; i.txt=x; i.n=0; i.has={}
  
  def add(i,v:atom):
    i.n += 1
    i.has[v] = 1 + i.has.get(v,0)

  def dist(i, a:atom, b:atom): return 1 if a=="?" and b=="?" else a != b

  def mid(i): return max(i.has, key=i.has.get)
                 
#  ._        ._ _  
#  | |  |_|  | | | 

class NUM(o):
  "summarize a stream of symbols"
  def __init__(i,c=0, x=" "):
    i.c=c; i.txt=x; i.n=0; i.mu=0; i.m2=0; i.sd=0;
    i.lo=1E32; i.hi=-1E32; i.goal = 0 if x[-1]=="-" else 1

  def add(i, v:atom):
    i.n += 1
    i.lo = min(v, i.lo)
    i.hi = max(v, i.hi)
    d = v - i.mu
    i.mu += d / i.n
    i.m2 += d * (v - i.mu)
    i.sd = 0 if i.n < 2 else (i.m2/(i.n - 1))**.5 

  def dist(i, a:number, b:number) -> number:
    a, b = i.norm(a), i.norm(b)
    a = a if a != "?" else (1 if b<.5 else 0)
    b = b if b != "?" else (1 if a<.5 else 0)
    return abs(a - b)

  def mid(i): return i.mu

  def norm(i,x:atom): #  -> 0..1 
    return x if x=="?" else (x - i.lo) / (i.hi - i.lo + 1E-32)
                    
#   _|   _.  _|_   _. 
#  (_|  (_|   |_  (_| 

class DATA(o):
  "DAtA stores rows and cols"
  def __init__(i): i.rows=[]; i.cols=o(names=[],all=[],x=[],y=[])

  def add(i, row:row):
    "update a DATA with new row"
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
      [col.add(row[col.c]) for l in [i.cols.x,i.cols.y] for col in l if row[col.c] != "?"]
    else:
      i.cols.names = row
      [create(c,v) for c,v in enumerate(row)]
    return i

  def clone(i,rows=[]):
    "create a new DATA with same structure of the receiver"
    return DATA().add(i.cols.names).adds(rows)

  def kmeans(i, k=16, loops=10, samples=512):
    "guess centroids, update, respond"
    def loop(loops, centroids):
      d = {}
      for row in rows:
        k = id(min(centroids, key=lambda r: i.xDist(r,row)))
        d[k] = d.get(k,None) or i.clone()
        d[k].add(row)
      return loop(loops-1, [j.mid() for j in d.values()]) if loops else d.values()
  
    samples = min(len(i.rows),samples)
    rows = random.choices(i.rows, k=samples)
    return loop(loops, rows[:k])

  def mid(i): return [col.mid() for col in i.cols.all]

  def xDist(i, row1:row, row2:row) -> number:
    "x-value Minkowski"
    d = sum(col.dist(row1[col.c], row2[col.c])**the.p for col in i.cols.x)
    return d**(1/the.p) / len(i.cols.x)**(1/the.p)
  
  def yDist(i, row:number) -> number:
    "y-value Chebyshev"
    return max(abs(y.goal - y.norm(row[y.c])) for y in i.cols.y)
#-----------------------------------------------------------------------
#  ._ _    _.  o  ._  
#  | | |  (_|  |  | | 

class main:
  "all these methods can be called from command-line; e.g. -csv runs `csv`."
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
    print(pretty(sorted([d.yDist(d2.mid()) for d2 in d.kmeans()])))

  def kmeans2():
    d   = DATA().adds(csv(the.train))
    n0  = NUM().adds([d.yDist(row) for row in d.rows])
    fun = lambda d1:d.yDist(d1.mid())
    k1=10; k2=4; k3=6
    print("#best","#","asIs","zero", "rand", "(sd)","row",sep="\t| ")
    for _ in range(20):
      n=NUM()
      [n.add(d.yDist(r)) for r in d.clone(random.choices(d.rows,k=k1+k2+k3)).rows]
      clusters1 = d.kmeans(k=k1)
      rows1     = sorted(clusters1, key=fun)[0].rows
      clusters2 = d.clone(rows1).kmeans(k=k2)
      rows2     = sorted(clusters2, key=fun)[0].rows
      random.shuffle(rows2)
      row       = sorted(rows2[:k3], key=lambda r:d.yDist(r))[0]
      print(f"{d.yDist(row):.2f}",k1+k2+k3,
            f"{n0.mu:.2f}\t| {n0.lo+0.35*n0.sd:.2f}",
            f"{n.mu:.2f}\t| {n.sd:.2f}",row,the.train,sep="\t| ")

#-----------------------------------------------------------------------
random.seed(the.seed)
cli(the.__dict__)
for i,s in enumerate(sys.argv):
  getattr(main, s[1:], lambda:1)()

#                                      __         
#                   __                /\ \        
#      ___ ___     /\_\        ___    \ \ \/'\    
#    /' __` __`\   \/\ \     /' _ `\   \ \ , <    
#    /\ \/\ \/\ \   \ \ \    /\ \/\ \   \ \ \\`\  
#    \ \_\ \_\ \_\   \ \_\   \ \_\ \_\   \ \_\ \_\
#     \/_/\/_/\/_/    \/_/    \/_/\/_/    \/_/\/_/

"""
In this code:
- UPPERCASE functions are constrictors
- lowercase versions of that constructor name are functions that add 1 item
- lowercase plus a "s" add multiple items

e.g. 
- DATA, SYM, NUM are constructors
- `data`, `sym`, `num` are functions that add 1 item to DATA,SYM or NUM
- `datas` is a function that adds many rows to DATA

"""
import random,sys,ast,re
from time import time_ns as nano
from fileinput import FileInput as file_or_stdin

class o:
  def __init__(i,**d): i.__dict__.update(**d)
  def __repr__(i): return  i.__class__.__name__ + pretty(i.__dict__)

#-----------------------------------------------------------------------
number  = float  | int   #
atom    = number | bool | str # and sometimes "?"
row     = list[atom]
rows    = list[row]
classes = dict[str,rows] # `str` is the class name
COL     = o
SYM     = COL
NUM     = COL
DATA    = o

the = o(
  buckets = 10,
  p       = 2,
  seed    = 1234567891,
  train   = "../../moot/optimize/misc/auto93.csv"
)

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
#   _  ._   _    _.  _|_   _  
#  (_  |   (/_  (_|   |_  (/_ 

def DATA(): 
  return o(rows=[], cols=o(names=[],all=[],x=[],y=[]))

def SYM(c=0, x=" "): 
  return o(This=SYM, c=c, txt=x, n=0, has={})

def NUM(c=0, x=" "):
  return o(This=NUM, c=c, txt=x, n=0,
           mu=0, m2=0, sd=0, lo=1E32, hi=-1E32, goal = 0 if x[-1]=="-" else 1)

def clone(i:DATA, rows=[]):
  return datas(data(DATA(), i.cols.names),rows)

#       ._    _|   _.  _|_   _  
#  |_|  |_)  (_|  (_|   |_  (/_ 
#       |                       

def sym(i:SYM, v:atom): 
  i.n += 1
  i.has[v] = 1 + i.has.get(v,0)

def num(i:NUM, v:number):
  i.n += 1
  i.lo = min(v, i.lo)
  i.hi = max(v, i.hi)
  d = v - i.mu
  i.mu += d / i.n
  i.m2 += d * (v - i.mu)
  i.sd = 0 if i.n < 2 else (i.m2/(i.n - 1))**.5 

def datas(i,src): [data(i,row) for row in src]; return i

def data(i:DATA, row):
  def nump(v)   : return v[0].isupper()
  def goalp(v)  : return v[-1] in "+-!"
  def ignorep(v): return v[-1] == "X"
  def update(col): (sym if col.This is SYM else num)(col, row[col.c]) 
  def create(c,v):
    col = (NUM if nump(v) else SYM)(c,v)
    i.cols.all += [col]
    if not ignorep(v):
      (i.cols.y if goalp(v) else i.cols.x).append(col)

  if i.cols.names: # true if we have already seen the header row
    i.rows += [row]
    [update(col) for cols in [i.cols.x,i.cols.y] for col in cols if row[col.c] != "?"]
  else:
    i.cols.names = row
    [create(c,v) for c,v in enumerate(row)]
  return i

#   _.        _   ._     
#  (_|  |_|  (/_  |   \/ 
#    |                /  

def mids(data): return [mid(col) for col in data.cols.all]
def mid(i)    : return i.mu if i.This is NUM else max(i.has,key=i.has.get)
def norm(i,x) : return x if x=="?" else (x - i.lo) / (i.hi - i.lo + 1E-32)

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

#   _  |        _  _|_   _   ._ 
#  (_  |  |_|  _>   |_  (/_  |  

def kmeans(data1, k=16, loops=10, samples=512):
  def loop(loops, centroids):
    d = {}
    for row in rows:
      k = id(min(centroids, key=lambda r: xDist(data1,r,row)))
      d[k] = d.get(k,None) or clone(data1)
      data(d[k],row)
    return loop(loops-1, [mids(data2) for data2 in d.values()]) if loops else d.values()

  samples = min(len(data1.rows),samples)
  rows = random.choices(data1.rows, k=samples)
  return loop(loops, rows[:k])
#-----------------------------------------------------------------------
class eg:
  def the(): print(the)

  def csv():
   for i,row in enumerate(csv(the.train)):
     if i % 30 == 0: print(i,row)

  def datas():
    d = datas(DATA(),csv(the.train))
    print(mids(d))
    for col in d.cols.y:
      print(col)

  def clones():
    d1 = datas(DATA(),csv(the.train))
    d2 = datas(clone(d1),d1.rows)
    for col in d1.cols.x: print(col)
    print("")
    for col in d2.cols.x: print(col)

  def kmeans():
    d = datas(DATA(),csv(the.train))
    print(pretty(sorted([yDist(d, mids(x)) for x in kmeans(d)])))

  def kmeans2():
    d         = datas(DATA(),csv(the.train))
    n0=NUM()
    [num(n0,yDist(d,x)) for x in d.rows]
    fun       = lambda d1:yDist(d, mids(d1))
    k1=10; k2=4; k3=6
    print("#best","#","asIs","zero", "rand", "(sd)","row",sep="\t| ")
    for _ in range(20):
      n=NUM()
      [num(n,yDist(d,r)) for r in clone(d,random.choices(d.rows,k=k1+k2+k3)).rows]
      clusters1 = kmeans(d, k=k1)
      rows1     = sorted(clusters1, key=fun)[0].rows
      clusters2 = kmeans(clone(d,rows1),k=k2)
      rows2     = sorted(clusters2, key=fun)[0].rows
      random.shuffle(rows2)
      row       = sorted(rows2[:k3], key=lambda r:yDist(d,r))[0]
      print(f"{yDist(d,row):.2f}",k1+k2+k3,
            f"{n0.mu:.2f}\t| {n0.lo+0.35*n0.sd:.2f}",
            f"{n.mu:.2f}\t| {n.sd:.2f}",row,the.train,sep="\t| ")

#-----------------------------------------------------------------------
random.seed(the.seed)
cli(the.__dict__)
for i,s in enumerate(sys.argv):
  getattr(eg,s[1:], lambda _:_)()

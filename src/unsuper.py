import random,math,sys,ast,re
from fileinput import FileInput as file_or_stdin
R = random.random
cos, log, sqrt = math.cos, math.log, math.sqrt
from time import time_ns as nano
#---------------------------------------------------------------------
#                  _         
#   _   _   ._   _|_  o   _  
#  (_  (_)  | |   |   |  (_| 
#                         _| 

class o:
  def __init__(i,**d): i.__dict__.update(**d)
  def __repr__(i): return  i.__class__.__name__ + pretty(i.__dict__)

the = o( # first letters must be unique; updatable via cli using cli(the.__dict__)
  buckets  = 10, 
  p     = 2, 
  seed  = 1234567891, 
  train = "../../moot/optimize/misc/auto93.csv"
)

#---------------------------------------------------------------------
#             
#   _   _   | 
#  (_  (_)  | 
            
class COL(o):
  def bins(i,groups: dict[str,list]): # -> list[SYM]:
    n,out = 0,{}
    for y,rows in groups.items():
      for row in rows:
        x = row[i.at]
        if x != "?" :
          n     += 1
          b      = i.bin(x)
          out[b] = out.get(b,None) or SYM(at=i.at, txt=i.txt)
          out[b].addxy(x,y)
    out =  i.merges(sorted(out.values(), key=lambda xy:xy.span.lo), n/the.buckets)
    w = sum(bin.n * bin.ent() for bin in out)/n
    return w,out
 
#---------------------------------------------------------------------
#                  
#  |\ |  | |  |\/| 
#  | \|  |_|  |  | 
                 
class NUM(COL):
  def __init__(i,init=[],at=0,txt=" "): 
    i.at, i.txt, i.goal         = at, txt, (0 if txt[-1] == "-" else 1)
    i.n, i.mu, i.m2, i.lo, i.hi = 0, 0, 0, 1E32, -1E32
    [i.add(x) for x in init]

  def add(i,x):
    if x != "?":
      i.n  += 1
      d     = x - i.mu
      i.mu += d/i.n
      i.m2 += d*(x - i.mu)
      i.sd  = 0 if i.n < 2 else (i.m2/(i.n - 1))**0.5
      i.lo  = min(x, i.lo)
      i.hi  = max(x, i.hi)

  def bin(i,x): return int(i.cdf(x)*the.buckets)

  def cdf(i,x):
    fun = lambda x: 1 - 0.5 * math.exp(-0.717*x - 0.416*x*x) 
    z   = (x - i.mu) / i.sd
    return  fun(x) if z>=0 else 1 - fun(-z) 

  def xDist(i,x,y):
    if x==y=="?": return 1
    x, y = i.norm(x), i.norm(y)
    x = x if x != "?" else (1 if y<.5 else 0)
    y = y if y != "?" else (1 if x<.5 else 0)
    return abs(x - y)
   
  def div(i): return i.sd

  def merges(i,bins, tiny):
    for j,bin in enumerate(bins):
      if j==0:
        out = [bins[0]]
      else:
        if tmp := bin.merged(out[-1], tiny): out[-1] = tmp
        else: out += [bin]
    out[ 0].span.lo = -math.inf
    out[-1].span.hi =  math.inf
    for j,bin in enumerate(out):
      if j>0:
         bin.span.lo = out[j-1].span.hi
    return out

  def mid(i): return i.mu

  def norm(i,x): return x if x=="?" else (x - i.lo) / (i.hi - i.lo + 1E-32)

#---------------------------------------------------------------------
#   __            
#  (_   \_/  |\/| 
#  __)   |   |  | 
#                 

class SYM(COL):
  def __init__(i,init=[],at=0,txt=" "): 
    i.n, i.at, i.txt, i.has = 0, at, txt, {}
    i.most, i.mode = 0, None
    i.span = o(lo=1e32, hi=-1e32)
    [i.add(x) for x in init]

  def add(i,x,n=1):
    if x != "?":
      i.n  += n
      i.has[x] = i.has.get(x,0) + n
      if i.has[x] > i.most: i.mode, i.most = x, i.has[x]

  def addxy(i,x,y):
    i.add(y)
    if x < i.span.lo: i.span.lo = x
    if x > i.span.hi: i.span.hi = x

  def bin(i,x):  return x

  def div(i): return i.ent()

  def ent(i): return -sum(n/i.n * math.log(n/i.n,2) for n in i.has.values())

  def merged(i,j, tiny=10):
    k = SYM(at=i.at,txt=i.txt)
    k.span = o(lo = min(i.span.lo,j.span.lo), hi = max(i.span.hi, j.span.hi))
    [k.add(x,n) for has in [i.has, j.has] for x,n in has.items()]
    if i.n < tiny or j.n < tiny or k.ent() <= (i.n*i.ent() + j.n*j.ent())/k.n:
      return k

  def merges(i,bins, _): return bins

  def mid(i): return i.mode

  def xDist(i,x,y): return 1 if x=="?" and y=="?" else x!=y

#---------------------------------------------------------------------
#   _         ___       
#  | \   /\    |    /\  
#  |_/  /--\   |   /--\ 

class DATA(o):
  def __init__(i):
    i.rows, i.names, i.cols, i.x, i.y = [], None, None, [],[]

  def adds(i,rows=[]): [i.add(row) for row in rows]; return i

  def add(i,row): 
    if i.cols:
      i.rows += [row]
      [col.add(row[col.at]) for col in i.cols]
    else:
      i.names = row
      i.cols  = [(NUM if s[0].isupper() else SYM)(at=i,txt=s) 
                 for i,s in enumerate(row)]
      for col in i.cols:
        (i.y if (col.txt[-1] in "+-!") else i.x).append(col)
    
  def clone(i,rows=[]): return DATA().adds([i.names]+rows)

  def csv(i,file): [i.add(row) for row in csv(file)]; return i
  def div(i): return [f"{col.div():.3f}" for col in i.cols]

  def twoFar(i,rows,sortp=False):
    a,b = max([(random.choice(rows), random.choice(rows)) for _ in range(20)],
              key=lambda z: i.xDist(z[0],z[1]))
    if sortp and i.yDist(a) < i.yDist(b): a,b = b,a
    return a,b, i.xDist(a,b)

  def half(i,rows, sortp=False):
    lefts,rights = [],[]
    left,right,c = i.twoFar(rows,sortp)
    def cos(a,b): return (a**2 + c**2 - b**2) / (2*c+ 1E-32) 
    def fun(r)  : return cos(i.xDist(r,left), i.xDist(r,right))
    for j,row in enumerate(sorted(rows, key=fun)):
      (lefts if j <= len(rows)/2 else rights).append(row) 
    return lefts, rights, left, right, i.xDist(left,rights[0]) 

  def halves(i,min=.5, samples=512,depth=4, sortp=False):
    leafs, rows = [], random.choices(i.rows, k=samples)
    stop = len(rows)**min
    def tree(depth,rows):
      if depth <= 0 or  len(rows) < 2*stop:
        leafs.append(i.clone(rows))
      else:
        lefts, rights, *_ = i.half(rows, sortp=sortp)
        tree(depth-1, lefts)
        tree(depth-1, rights)
    tree(depth,rows) 
    return leafs

  def kmeans(i, k=16, loops=10, samples=512):
    rows = random.choices(i.rows, k=samples)
    def loop(loops, mids):
      d = {}
      for row in rows:
        k    = id(min(mids, key=lambda r: i.xDist(r,row)))
        d[k] = d.get(k,None) or i.clone()
        d[k].add(row)
      return loop(loops-1, [data.mid() for data in d.values()]) if loops else d.values()
    return loop(loops, rows[:k])
    
  def mid(i): return [col.mid() for col in i.cols]

  def xDist(i, x, y):
    tmp = sum(c.xDist(x[c.at], y[c.at])**the.p for c in i.x) 
    return tmp / len(i.x)**(1/the.p)

  def yDist(i,row):
    return max(abs(col.norm(row[col.at]) - col.goal) for col in i.y)

#---------------------------------------------------------------
#            
#  |  o  |_  
#  |  |  |_) 

def gauss(mu=0, sd=1):
  return mu + sd * sqrt(-2*log(R()))* cos(2*math.pi*R())

def coerce(s):
  try: return ast.literal_eval(s)
  except Exception: return s

def csv(file):
  with file_or_stdin(None if file=="−" else file) as src: 
    for line in src: 
      line = re.sub(r"([\n\t\r ]|\#.*)", "", line)
      if line: yield [coerce(s.strip()) for s in line.split(",")]

def cli(d):
  for k,v in d.items():
    v = str(v)
    for c,arg in enumerate(sys.argv):
      after = sys.argv[c+1] if c < len(sys.argv) - 1 else ""
      if arg in ["-"+k[0], "--"+k]:
        d[k] = coerce("False" if v=="True" else ("True" if v=="False" else after))
  return d

def pretty(x):
  if isinstance(x,float): return f"{x:g}"
  if not isinstance(x,dict): return f"{x}"
  return "(" + ' '.join(f":{k} {v}" for k,v in x.items() if str(k)[0] != "_") + ")"
                       
#---------------------------------------------------------------
#            
#   _  _|_   _.  ._  _|_ 
#  _>   |_  (_|  |    |_ 
                       
def eg_main():
  n = NUM( [gauss(10,2) for _ in range(1000)]) ;assert 9.9 < n.mu < 10.1  and 1.9 < n.sd < 2.1
  n = NUM([5, 5, 9, 9, 9, 10, 5, 10, 10])      ;assert 2.29 < n.sd < 2.30 and n.mu==8
  s = SYM("aaaabbc")                           ;assert s.mode == "a"      and 1.37 < s.ent() < 1.38
  n = 0
  #assert 3192 == sum(len(row) for i,row in enumerate(csv(the.train)))
  d = DATA().csv(the.train); # print(d.div())
  print("kmeans",sorted([f"{d.yDist(data.mid()):.2f}" for data in d.kmeans()]))
  print("halves",sorted([f"{d.yDist(data.mid()):.2f}" for data in d.halves(sortp=True)]))
  t1=nano(); [d.kmeans() for _ in range(10)]
  t2=nano(); [d.halves() for _ in range(10)]
  t3=nano()
  print("kmeans/halves", (t2-t1)/(t3-t2))
  groups = {chr(j+65): data.rows for j,data in  enumerate(d.halves())}
  for col in d.x:
    col.bins(groups)

def eg_halves():
  d = DATA().csv(the.train); # print(d.div())
  groups = {chr(j+65): data.rows for j,data in  enumerate(d.halves())}
  for w,bins in sorted(col.bins(groups) for col in d.x):
    print("")
    print("expected entropy if dividing on this feature:",pretty(w))
    for bin in bins:
      print("\t",bin.txt,bin.span)

cli(the.__dict__)
random.seed(the.seed)
eg_halves()

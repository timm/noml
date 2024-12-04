import random,math,sys,ast,re
from fileinput import FileInput as file_or_stdin
R = random.random
cos, log, sqrt = math.cos, math.log, math.sqrt
from time import time_ns as nano

class o:
  def __init__(i,**d): i.__dict__.update(**d)
  def __repr__(i): return  i.__class__.__name__ + pretty(i.__dict__)

the = o( # first letters must be unique; updatable via cli using cli(the.__dict__)
  buckets  = 10, 
  p     = 2, 
  k     = 4,
  seed  = 1234567891, 
  train = "../../moot/optimize/misc/auto93.csv"
)

class COL(o): pass

#------------------------------------------------------------------------------
class NUM(COL):
  def __init__(i,at=0,txt=" "): 
    i.at, i.txt, i.goal = at, txt, (0 if txt[-1] == "-" else 1)
    i.n, i.mu, i.m2, i.lo, i.hi = 0, 0, 0, 1E32, -1E32 

  def add(i,x):
    if x != "?":
      i.n  += 1
      d     = x - i.mu
      i.mu += d/i.n
      i.m2 += d*(x - i.mu)
      i.sd  = 0 if i.n < 2 else (i.m2/(i.n - 1))**0.5
      i.lo  = min(x, i.lo)
      i.hi  = max(x, i.hi)

  def cdf(i,x):
    fun = lambda x: 1 - 0.5 * math.exp(-0.717*x - 0.416*x*x) 
    z   = (x - i.mu) / i.sd
    return  fun(x) if z>=0 else 1 - fun(-z) 
  
  def bin(i,x): return int(i.cdf(x)*the.buckets)
  def div(i): return i.sd
  def mid(i): return i.mu
  def norm(i,x): return x if x=="?" else (x - i.lo) / (i.hi - i.lo + 1E-32)

  def xDist(i,x,y):
    if x==y=="?": return 1
    x, y = i.norm(x), i.norm(y)
    x = x if x != "?" else (1 if y<.5 else 0)
    y = y if y != "?" else (1 if x<.5 else 0)
    return abs(x - y)
   
#------------------------------------------------------------------------------
class SYM(COL):
  def __init__(i,at=0,txt=" "): 
    i.n, i.at, i.txt, i.has, i.most, i.mode = 0, at, txt, {}, 0, None 

  def add(i,x,n=1):
    if x != "?":
      i.n  += n
      i.has[x] = i.has.get(x,0) + n
      if i.has[x] > i.most: i.mode, i.most = x, i.has[x]

  def bin(i,x): return x
  def div(i):   return i.ent()
  def ent(i):   return -sum(n/i.n * math.log(n/i.n,2) for n in i.has.values())
  def mid(i):   return i.mode
  def xDist(i,x,y): return 1 if x=="?" and y=="?" else x!=y

#------------------------------------------------------------------------------
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

  def kmeans(i, k=16, loops=10, samples=512):
    rows = random.choices(i.rows, k=samples)
    def loop(loops, mids):
      d = {}
      for row in rows:
        k    = id(min(mids, key=lambda r: i.xDist(r,row)))
        d[k] = d.get(k,None) or i.clone()
        d[k].add(row)
      return loop(loops-1, [data.mid() for data in d.values()]
                 ) if loops else d.values()
    return loop(loops, rows[:k])
   
   
  def mid(i,rows=None): 
    tmp = [col.mid() for col in i.cols]
    return min(rows or i.rows, key=lambda r: i.xDist(r,tmp))

  def xDist(i, x, y):
    tmp = sum(c.xDist(x[c.at], y[c.at])**the.p for c in i.x) 
    return tmp / len(i.x)**(1/the.p)

  def yDist(i,row):
    return max(abs(col.norm(row[col.at]) - col.goal) for col in i.y)

#------------------------------------------------------------------------------
def adds(t, it=None):
  it = it or (NUM() if type(t[0]) in [int,float] else SYM())
  for x in t: it.add(x)
  return it

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
  return "(" + ' '.join(f":{k} {pretty(v)}" for k,v in x.items() if str(k)[0] != "_") + ")"
                       
#------------------------------------------------------------------------------
class eg:
  def num(_):
    n = adds([gauss(10,2) for _ in range(1000)])
    assert 9.9 < n.mu < 10.1  and 1.9 < n.sd < 2.1
    n = adds([5, 5, 9, 9, 9, 10, 5, 10, 10])     
    assert 2.29 < n.sd < 2.30 and n.mu==8

  def sym(_):
    s = adds("aaaabbc"); assert s.mode == "a" and 1.37 < s.ent() < 1.38

  def csv(_):
    assert 3192 == sum(len(row) for i,row in enumerate(csv(the.train)))

  def cluster(_):
    d = DATA().csv(the.train); # print(d.div())
    n = adds([d.yDist(row) for row in d.rows])
    print(o(lo=n.lo,mid=n.mu, hi=n.hi, div=n.sd))
    print("kmeans",sorted([f"{d.yDist(data.mid()):.2f}" 
                           for data in d.kmeans(loops=5, k=the.k)]))

  def clusters(_):
    d = DATA().csv(the.train); # print(d.div())
    r = 20
    t1=nano(); [d.kmeans(loops=5,k=4) for _ in range(r)]
    t2=nano()
    print("kmeans", (t2-t1)/10**9/r)

  def rkmeans(_):
    d0 = DATA().csv(the.train); # print(d.div())
    D  = lambda row: d0.yDist(row)
    print(adds([D(row) for row in d0.rows]).lo)
    dnow = d0
    for _ in range(4):
        print("\n",len(dnow.rows))
        datas = dnow.kmeans(k=4,loops=10,samples=512)
        [ print(len(data.rows)) for data in datas]
        dnow = sorted(datas, key=lambda data:D(data.mid()))[0]
    print(dnow.mid(), len(dnow.rows), D(dnow.mid()))
   
  def bins(_):
    d = DATA().csv(the.train); # print(d.div())
    groups = {chr(j+65): data.rows for j,data in  enumerate(d.halves())}
    for col in d.x:
      col.bins(groups)

  def weight(_):
    d = DATA().csv(the.train); # print(d.div())
    groups = {chr(j+65): data.rows for j,data in  enumerate(d.halves())}
    for w,bins in sorted(col.bins(groups) for col in d.x):
      print("")
      print("expected entropy if dividing on this feature:",pretty(w))
      for bin in bins:
        print("\t",bin.txt,bin.span)
 
cli(the.__dict__)
random.seed(the.seed)
for i,s in enumerate(sys.argv): getattr(eg,s[2:], lambda *_:_)(i+1)

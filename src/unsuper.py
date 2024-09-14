import random,math,ast,re
from fileinput import FileInput as file_or_stdin
R = random.random
cos, log, sqrt = math.cos, math.log, math.sqrt
from time import time_ns as nano

class o:
  def __init__(i,**d): i.__dict__.update(**d)
  def __repr__(i): return  i.__class__.__name__ + str(i.__dict__)

the = o(bins=10, p=2, seed=1234567891, 
        train="../../moot/optimize/misc/auto93.csv")

class NUM(o):
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

  def bin(i,x,bins): return int(i.cdf(x)*bins)

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

  def merges(i.bins, small):
    bins = sorted(bins.items(), key=lambda z:z[1])
    out = [bins[1]]
    for j,bin in enumerate(bins):
      if j>1:
        if tmp := bin.merged(out[-1], small): out[-1] = tmp
        else: out += [bin]
    return out

  def mid(i): return i.mu

  def norm(i,x): return x if x=="?" else (x - i.lo) / (i.hi - i.lo + 1E-32)


class SYM(o):
  def __init__(i,init=[],at=0,txt=" "): 
    i.n, i.at, i.txt, i.has = 0, at, txt, {}
    i.most, i.mode = 0, None
    [i.add(x) for x in init]

  def add(i,x,n=1):
    if x != "?":
      i.n  += n
      i.has[x] = i.has.get(x,0) + n
      if i.has[x] > i.most: i.mode, i.most = x, i.has[x]

  def bin(i,x):  return x

  def xDist(i,x,y): return 1 if x=="?" and y=="?" else x!=y
 
  def div(i): return i.ent()

  def ent(i): return -sum(n/i.n * math.log(n/i.n,2) for n in i.has.values())

  def merged(i,j, tiny=10):
    k = SYM(i.at,i.txt)
    [k.add(x,n) for has in [i.j.has, i.k.has] for x,n in has.items()]
    if i.n < tiny or j.n < tiny or k.ent() <= (i.n*i.ent() + j.n*j.ent())/k.n:
      return k

  def merges(i,bins, _): return sorted(bins.items(),lambda z:z[1])

  def mid(i): return i.mode

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

  def xDist(i, x, y):
    tmp = sum(c.xDist(x[c.at], y[c.at])**the.p for c in i.x) 
    return tmp / len(i.x)**(1/the.p)

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
    for j,row in enumerate(sorted(rows, key=lambda r: cos(i.xDist(r,left), i.xDist(r,right)))):
      (lefts if j <= len(rows)/2 else rights).append(row) 
    return lefts, rights, left, right, i.xDist(left,rights[0]) 

  def halves(i,min=.5, samples=512, depth=4):
    leafs, rows = [], random.choices(i.rows, k=samples)
    stop = len(rows)**min
    def tree(depth,rows):
      if depth < 1 or  len(rows) < 2*stop:
        leafs.append(i.clone(rows))
      else:
        lefts, rights, *_ = i.half(rows, sortp=True)
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
      return d.values() if loops else loop(loops-1, [data.mid() for data in d.values()])
    return loop(loops, rows[:k])
    
  def mid(i): return [col.mid() for col in i.cols]

  def yDist(i,row):
    return max(abs(col.norm(row[col.at]) - col.goal) for col in i.y)

#---------------------------------------------------------------
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

def main():
  n = NUM( [gauss(10,2) for _ in range(1000)]) ;assert 9.9 < n.mu < 10.1  and 1.9 < n.sd < 2.1
  n = NUM([5, 5, 9, 9, 9, 10, 5, 10, 10])      ;assert 2.29 < n.sd < 2.30 and n.mu==8
  s = SYM("aaaabbc")                           ;assert s.mode == "a"      and 1.37 < s.ent() < 1.38
  n = 0
  assert 3192 == sum(len(row) for i,row in enumerate(csv(the.train)))
  d = DATA().csv(the.train); print(d.div())
  print("kmeans",sorted([f"{d.yDist(data.mid()):.2f}" for data in d.kmeans()]))
  print("halves",sorted([f"{d.yDist(data.mid()):.2f}" for data in d.halves()]))
  t1=nano()
  for _ in range(10**2): d.kmeans()
  t2=nano()
  for _ in range(10**2): d.halves()
  t3=nano()
  print("k", t2-t1)
  print("h", t3-t2)

#---------------------------------------------------------------
random.seed(the.seed)
main()

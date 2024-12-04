import math,ast
from bisect import bisect_left as chop

class o:
  def __init__(i,**d): i.__dict__.update(**d)
  def __repr__(i): return  i.__class__.__name__ + pretty(i.__dict__)

the = o( # first letters must be unique; updatable via cli using cli(the.__dict__)
  bins  = 10, 
  p     = 2, 
  k     = 4,
  seed  = 1234567891, 
  train = "../../moot/optimize/misc/auto93.csv"
)

def nump(x): return  type(x) is list

class COL(o):
  def __init__(i,init=None, at=0,txt=" "): 
    i.at, i.txt, i.goal = at, txt, (0 if txt[-1] == "-" else 1)
    i.has = init or ([] if txt[0].isupper() else {})
    i.reSort = nump(i.has) and len(i.has) > 0

  def add(i,x):
    if x != "?":
      if nump(i.has): 
        i.reSort = True
        return i.has.append(x)
      i.has[x] = 1 + i.has.get(x,0)

  def ok(i): 
    if i.reSort: i.has.sort()
    i.reSort = False
    return i.has

  def lo(i):     return i.ok().has[0] 
  def hi(i):     return i.ok().has[-1] 
  def div(i):    return stdev(i.ok().has)  if nump(i.has) else entropy(i.has)  
  def mid(i):    return median(i.ok().has) if nump(i.has) else max(i.has, key=i.has.get)
  def norm(i,x): return x if x=="?" else (x - i.lo()) / (i.hi() - i.lo() + 1E-32)
  def bin(i,x):  return int(0.5 + (chop(i.ok().has,x)/len(i.has)*the.bins)) if nump(i.has) else x

  def xDist(i,x,y):
    if x==y=="?": return 1
    if nump(i.has):
      x, y = i.norm(x), i.norm(y)
      x = x if x != "?" else (1 if y<.5 else 0)
      y = y if y != "?" else (1 if x<.5 else 0)
      return abs(x - y)
    return x != y

#-------------------------------------------------------------------------------
class DATA(o):
  def __init__(i):
    i.rows, i.cols = [], o(names=[], x=[], y=[], all=])

  def adds(i,rows=[]): [i.add(row) for row in rows]; return i

  def add(i,row): 
    if i.cols:
      i.rows += [row]
      [col.add(row[col.at]) for col in i.cols.all]
    else:
      i.cols.names= row
      for i,s in enumerate(row):
        col = COL([],i,s) if s[0].isupper() else COL({},i,s)
        i.cols.all += [col]
        (i.cols.y if (col.txt[-1] in "+-!") else i.cols.x).append(col)
    return i
    
  def clone(i,rows=[]): return DATA().add(i.cols.names).adds(rows)

  def csv(i,file): [i.add(row) for row in csv(file)]; return i

  def  xdist(i,r1,r2):
   return ( sum(math.abs(c.norm(r1[c.at]) - c.norm(r2[c.at]))**the.p for c in i.cols.x)
          / len(i.cols.x))**(1/the.p)

  def  ydist(i,rrow):
   return (sum(math.abs(c.norm(row[c.at]) - c.goal)**the.p for c in i.cols.y)
          / len(i.cols.y))**(1/the.p)

  def div(i): return [f"{col.div():.3f}" for col in i.cols]

#-------------------------------------------------------------------------------
def adds(t, it=None):
  it = it or (COL([]) if type(t[0]) in [int,float] else COL({}))
  for x in t: it.add(x)
  return it

def per(a,n):  return a[int(int(len)*n)]
def median(a): return per(a,0.5)
def stdev(a):  return (per(a,0.9) - per(a,0.1))/2.58

def entropy(d):
  N=sum(d.values())
  return -sum(n/N * math.log(n/N,2) for n in d.values() if n > 0)

def pretty(x):
  if isinstance(x,float): return f"{x:g}"
  if not isinstance(x,dict): return f"{x}"
  return "(" + ' '.join(f":{k} {pretty(v)}" for k,v in x.items() if str(k)[0] != "_") + ")"

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

#-------------------------------------------------------------------------------
cli(the.__dict__)
random.seed(the.seed)
for i,s in enumerate(sys.argv): getattr(eg,s[2:], lambda *_:_)(i+1)

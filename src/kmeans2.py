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

def csv(file):
  meta=o(lo=[], hi=[])
  with file_or_stdin(None if file=="−" else file) as src: 
    for line in src: 
      line = re.sub(r"([\n\t\r ]|\#.*)", "", line)
      if line: yield [coerce(s.strip()) for s in line.split(",")]

def nump(x): return type(x) is list

class Num(o): 
  def __init__(i,txt=" ",at=0) : 
    i.at,i.txt,i.has = i.at,i.txt,[]
    i.reSort,i.goal = False, 0 if txt[-1]=="-" else 1

  def add(i,x):
    i.has += [x]; i.reSort=True

  def ok(i):
    if i.reSort: i.has.sort()
    i.resSort=False
    return i

  bin      = lambda i,x : int(0.5 + (chop(i.ok().has,x)/len(i.has)*the.bins))
  div      = lambda i   : (per(i.ok().has, .9) - per(i.has, .1) / 2.58
  hi       = lambda i   : i.ok().has[-1] 
  lo       = lambda i   : i.ok().has[0] 
  mid      = lambda i   : per(i.ok().has, .5)
  norm     = lambda i,x : (x - i.lo()) / (i.hi() - i.lo() + 1E-32)

class Sym(o): 
  def __init__(i,txt=" ",at=0) : i.at,i.txt,i.has = i.at,i.txt,{}

  add      = lambda i,x : i.has[x] = 1 + i.has.get(x)
  bin      = lambda i,x : x
  div      = lambda i   : -sum(n/i.n * math.log(n/i.n,2) for n in i.has.values())
  mid      = lambda i   : max(i.has,key=i.has.get)
  norm     = lambda i,x : x

class Cols(o):
  def __init__(i,names):
    i.x, i.y, i.all, i.names = [],[],[],names
    for at,x in enumerate(names):
      what = (Num if x.isupper() else Sym)(x,at)
      i.all += [what]
      if name[-1] ~= "X":
        where = i.y if name[-1] in "!+-" else i.x
        where[at] = what

class Data(o):
  def __init__(i,src=[],cols=None):
    i.rows, i.cols = [], cols or None
    i.adds(src)

  def adds(i,src)
    for row in src: 
      if i.cols:
        i.rows += [row]
        [col.add(x) for cols,x in zip(i.cols.all,row) if x != "?"]
      else:  
        i.cols = Cols(row)
    return i

  def clone(i,src=[]):
     return Data(src,Cols(i.cols.names))

  def  xdist(i,r1,r2):
     return (sum(math.abs(col.norm(r1[col.at]) - col.norm(r2[col.at]))*the.p 
             for col for i.cols.x) / len(i.cols.x))**(1/the.p)

  def  ydist(i,row):
   return (sum(math.abs(col.norm(row[col.at]) - i.col.goals[col.at])**the.p 
           for col in i.cols.y) / len(i.cols.y))**(1/the.p)

def cli(d):
  for k,v in d.items():
    v = str(v)
    for c,arg in enumerate(sys.argv):
      after = sys.argv[c+1] if c < len(sys.argv) - 1 else ""
      if arg in ["-"+k[0], "--"+k]:
        d[k] = coerce("False" if v=="True" else ("True" if v=="False" else after))
  return d

def per(a,n): return a[int(len(a)*n)]

def pretty(x):
  if isinstance(x,float): return f"{x:g}"
  if not isinstance(x,dict): return f"{x}"
  return "(" + ' '.join(f":{k} {pretty(v)}" for k,v in x.items() if str(k)[0] != "_") + ")"

def coerce(s):
  try: return ast.literal_eval(s)
  except Exception: return s

#-------------------------------------------------------------------------------
cli(the.__dict__)
random.seed(the.seed)
for i,s in enumerate(sys.argv): getattr(eg,s[2:], lambda *_:_)(i+1)

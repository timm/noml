class o:
  def __init__(i,**d): i.__dict__.update(**d)
  def __repr__(i): return  i.__class__.__name__ + pretty(i.__dict__)

the = o( 
  buckets = 10, 
  p       = 2, 
  seed    = 1234567891, 
  train   = "../../moot/optimize/misc/auto93.csv"
)

def COLS()           : return o(Is=COLS, all=[], x=[], y=[])
def DATA()           : return o(Is=DATA, rows=[], cols=COLS())
def SYM(at=0,txt=" "): return o(Is=SYM,  n=0, at=at, txt=txt, has=[])
def NUM(at=0,txt=" "): return o(Is=NUM,  n=0, at=at, txt=txt, has=[],
                                goal=0 if txt[0]=="-" else 1,
                                old=False)

def add(i,x):
  if x=="?": return
  match i.Is::
    case SYM: i.n += 1; i.has[x] = 1 + i.has.get(x,0)
    case NUM: i.n += 1; i.has   += [x]; i.old=True
    case DATA: 
      i.rows += [x]
      [c.add(x) for cols in [i.cols.x,i.cols.y] for c in cols]
    case COLS: 
      i.all += [x]
      if x.txt[-1] != "X": 
        (i.y if x.txt[-1] in "+-!" else i.x).append(x)
  return x

data = DATA()
for i,row in enumerate(csv(file)):
  if i==0:
    for at,txt in enumerate(names): 
      add(data.cols, (NUM if txt[0].isupper() else SYM)(at,txt))
    continue

def pretty(x):
  if isinstance(x,float): return f"{x:g}"
  if not isinstance(x,dict): return f"{x}"
  return "(" + ' '.join(f":{k} {pretty(v)}" 
                        for k,v in x.items() if str(k)[0].isupper()) + ")"

from typing import Any as any
from typing import Union, List, Dict, Type, Callable, Generator
from fileinput import FileInput as file_or_stdin
from math import sqrt, exp, log, cos, pi
import random, sys, ast, re

big=1E32

class o:
  def __init__(self, **d): self.__dict__.update(**d)
  def __repr__(self): return self.__class__.__name__ + say(self.__dict__)

DATA, COLS = o, o
NUM, SYM  = o, o
COL = NUM | SYM

number = float | int   #
atom = number | bool | str  # and sometimes "?"
row = list[atom]
rows = list[row]
classes = dict[str, rows]  # `str` is the class name

the = o(k=1, m=2, train="../../moot/optimize/misc/auto93.csv")

def coerce(s: str) -> atom:
  try: return ast.literal_eval(s)
  except Exception: return s

def csv(file: str) -> Generator:
  with file_or_stdin(None if file == "−" else file) as src:
    for line in src:
      line = re.sub(r"([\n\t\r ]|\#.*)", "", line)
      if line:
        yield [coerce(s.strip()) for s in line.split(",")]

def SYM(at=0, txt=" ") -> SYM:
  return o(nump=False, n=0, at=at, txt=txt, most=0, mode=None, counts={})

def NUM(at=0, txt=" "): 
  return o(nump=True, n=0, at=at, txt=txt, m2=0, mu=0, sd=0, lo=big, hi=-big,
          goal = 0 if txt[-1] in "-" else 1)

def DATA(names): return o(rows=[], cols=COLS(names))

def COLS(names):
  all,x,y,nums = [],[],[],[]
  for at,s in enumerate(names):
    col = (NUM if s[0].isupper() else SYM)(at=at, txt=s)
    all += [col]
    if not s[-1] == "X": 
       (y if s[-1] in "+-!" else x).append(col)
  return o(names=names, all=all, x=x, y=y)

def col(self: COL, x) -> None:
  if x != "?" : 
    self.n += 1
    if self.nump:
      self.lo = min(x, self.lo)
      self.hi = max(x, self.hi)
      d = x - self.mu
      self.mu += d / self.n
      self.m2 += d * (x - self.mu)
      self.sd = 0 if self.n < 2 else (self.m2/(self.n - 1))**.5
    else:
      tmp = self.counts[x] = 1 + self.counts.get(x, 0)
      if tmp > self.most:
        self.most, self.mode = tmp, x
  return x

def data(self:DATA, row):
  self.rows.append( [col(c, row[c.at]) for c in self.cols.all] )

def read(file: str) -> DATA:
  src = csv(file)
  self = DATA(next(src))
  [data(self, row) for row in src]
  return self

def like(self: DATA, row: row, nall: int, nh: int) -> float:
  def _sym(sym1, x, prior):
    return (sym1.counts.get(x, 0) + the.m*prior) / (sym1.n + the.m)

  def _num(num1, x, _):
    v = num1.sd**2 + 1E-32
    tmp = exp(-1*(x - num1.mu)**2/(2*v)) / (2*pi*v) ** 0.5
    return min(1, tmp + 1E-32)

  prior = (len(self.rows) + the.k) / (nall + the.k*nh)
  likes = [(_num if c.nump else _sym)(c, row[c.at], prior) for c in self.cols.x]
  return sum(log(x) for x in likes + [prior] if x > 0)

def acquire(self: DATA, rows: rows, labels=None, fun=lambda b,r: b+b-r) -> tuple[dict,row]:
  labels = labels or {}
  def _Y(a): labels[id(a)] = a; return ydist(self, a)

  def _guess(todo, done):
    def key(r):
      return 0 if R() > guesses else fun (like(best, r, len(done), 2), 
                                            like(rest, r, len(done), 2))
    nBest   = int(len(done)**the.end)
    guesses = min(the.guesses, len(todo)) / len(todo)
    best    = DATA(self.cols.names, done[:nBest])
    rest    = DATA(self.cols.names, done[nBest:])
    return sorted(todo, key=key, reverse=True)

  def _loop(todo, done):
    lives, least, out = the.lives, big, None
    while len(done) < the.Stop and lives>0:
      top, *todo = _guess(todo, done)
      done = sorted(done + [top], key=Y)
      if ydist(self,done[0]) < least: 
        least = ydist(self,done[0])
        lives += the.lives
      else:
        lives -= 1
    return done

  b4 = list(labels.values())
  m = max(0, the.start - len(b4))
  return labels, _loop(rows[m:], sorted(rows[:m] + b4, key=_Y))

def norm(self: NUM, x) -> float:
  return x if x == "?" else (x - self.lo)/(self.hi - self.lo + 1/big)

def ydist(self: DATA, row) -> float:
  return max(abs(c.goal - norm(c, row[c.at])) for c in self.cols.y)

def ydists(self: DATA) -> DATA:
  self.rows.sort(key=lambda r: ydist(self, r))
  return self

def say(x: any) -> str:
  if isinstance(x, float): 
    return str(x) if int(x) == x else f"{x:.3f}"
  if isinstance(x, list ) : return "["+', '.join([say(y) for y in x])+"]"
  if not isinstance(x, dict): return str(x)
  return "(" + ' '.join(f":{k} {say(v)}"
                        for k, v in x.items() if not str(k)[0] == "_") + ")"

[print(col) for col in read(the.train).cols.y]

class main:
  def acquire(_):
    data1 = ydists(read(the.train))
    labels, rows = acquire(data1, shuffle(data1.rows))
    better = (asIs.mu - toBe.mu)/asIs.sd
    print(f"{the.lives:3} :labels {samples.mu:3.1f} :asIs {asIs.mu:.3f} :todo {toBe.mu:.3f} :delta {better:.3f}")



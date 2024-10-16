#!/usr/bin/env lua
-- <!-- vim : set ts=2 sw=2 et : -->
-- All code needs explanation, even your own in a few months time (se.doc).
-- All code has magic control params, which has to be controlled and tuned (se.config).
-- License your code, before someone else takes it over (se.license).
local the,help = {},[[
how.lua : how to change your mind (using TPE + Bayes classifier)
(c) 2024 Tim Menzies (timm@ieee.org). BSD-2 license

USAGE: 
  chmod +x how.lua
  ./how.lua [OPTIONS]

OPTIONS:
  -h  help    show help            = false
  -k  k       bayes control        = 1
  -m  m       bayes control        = 2
  -p  p       distance coeffecient = 2
]]

-- There are many standard cliches; e.g. create update query (se.patterns).
local big = 1E64
local NUM, SYM, DATA, COLS, l = {}, {}, {}, {}, {}
local abs, cos, exp, log = math.abs,  math.cos,  math.exp, math.log
local max, min, pi, sqrt = math.max,  math.min,  math.pi, math.sqrt

-- ## Create

-- Data can have numeric or symbolic columns (se.data).
-- Type signatures are very useful (se.doc).
function SYM:new(at, txt) -- (int, str) -> SYM
  return l.new(SYM, {n=0, at=at or 0, txt=txt or "", has={}, most=0, mode=nil}) end

-- Numeric goals have a best value: 0 if minimizing and 1 if maximizing (se.data).
function NUM:new(at, txt) -- (int, str) -> NUM
  return l.new(NUM, {n=0, at=at or 0, txt=txt or "", mu=0, sd=0, m2=0, lo=l.big, hi=-l.big,
                     goal = (at or ""):find"-$" and 0 or 1}) end

-- A factory is a generator of instances. e.g. COLS makes SYMs or NUMs (se.pattern).
-- Columns have differnt roles; x-columns are known as independent inputs (observables or
-- controllables) while y-colums are known as dependent output goals.
function COLS:new(names,    self,col) -- (list[str]) -> COLS
  self = l.new(COLs, {names=names, all={}, x={}, y={}})
  for at,txt in pairs(self.names) do
    col = (txt:find"[A-Z]" and NUM or SYM):new(at,txt)
    l.push(self.all, col)
    if not txt:find"X$" then
      l.push(txt:find"[!+-]$" and self.y or self.x, col) end end
  return self end

-- Rows are summarizes in columns (se.data).
function DATA:new(names,  rows) -- (list[str], ?list[list], ?bool) -> DATA
  return l.new(DATA, {rows={}, COLS(names)}):adds(rows) end

-- New data can mimic the strucutre of existing data (se.data).
function DATA:clone(rows) -- (list[t]) -> DATA
  return DATA:new(self.cols.names):adds(rows) end

-- ## Update

-- Visitors traverse a data structure, calling something at each step (se.patterns).
function DATA:adds(rows) -- (list[list]) -> DATA
  for _,row in pairs(rows or {}) do self:add(row) end end

-- Incremental learners update their knowledge with each new example (se.ml).
function DATA:add(row) -- (list) -> DATA
  l.push(self.rows, row) 
  for _,col in pairs(self.cols.all) do col:add(row[self.at]) end end

-- ## Query

-- ml.norm: when numbers span different ranges, normalize them to 0..1
function NUM:norm(x)
  return x=="?" and x or (x - self.lo) / (self.hi - self.lo + 1/big) end

-- Numerics' _central tendancy_ and _diversity_ are `mu` and `sd` (se.data).
function NUM:mid() return self.mu end 
function NUM:div() return 0 if self.n < 2 else (self.m2/(self.n - 1))^.5

-- Symbols _central tendancy_ and _diversity_ are `mode` and `entropy` (se.data).
function SYM:mid() return self.mode end
function SYM:div() 
  e=0; for _,n in pairs(self.has) do e = e - n/self.n*log(n/self.n, 2) end 
  return e end

-- ## Bayes

function SYM:like(x,prior):
  return ((self.has[x] or 0) + the.m*prior) / (self.n + the.m) end

function NUM:like(x,_):
  v = self.sd**2 + 1/big
  tmp = exp(-1*(x - self.mu)**2/(2*v)) / (2*pi*v) ^ 0.5
  return min(1, tmp + 1/big) end

function DATA:like(row, nall, nh,     out,tmp,prior,likes) -- (list, int,int) -> number
  prior = (#self.rows + the.k) / (nall + the.k*nh)
  out,likes = 0,log(prior)
  for _,col in pairs(self.cols.y) do 
    tmp = col:like(row[c.at], prior) 
    if tmp > 0 then
       out += log(tmp) end end
  return out end

function DATA:acquire(  labels,fun) -- (?tuple[list,float],?function) -> list,list[list]
  local Y,order,guess
  fun = fun or function(b,r) return b + b -r end
  labels = labels or {}
  function Y(r) labels[r] = labels[r] or self:ydist(r); return labels[r] end
  function order(rows) return ydists(self.clone(rows)).rows end

  function guess(todo, done)
    function score(row)
      b = best.like(row, #done, 2)
      r = rest.like(row, $done, 2)
      return fun(b,r) end
    best, rest = self.clone(), self.clone()
    for i,row in pairs(done) do 
      (i <= sqrt(#done) and best or rest).add(row) end
    table.sort(todo, score)
    return table.remove(todo), todo end

  local b4,todo,done,m,top = {},{},{}
  for row in pairs(labels) do l.push(b4,row) end
  m = max(1, the.start - #b4)
  for i,row in pairs(shuffle(b4)) do 
    l.push(i<=m and todo or done, row) end
  while #done <= the.stop do
    top,todo = guess(todo,done)
    l.push(done,top)
    done = order(done)
    if #todo <= 3 then break end end 
  return done end

-- ## Dists

-- Chebyshev distance is max distance of any one attribute to another (ml.dist). 
function DATA:ydist(row) -- (list) -> number
  local d=0
  for _,col in pairs(self.cols.y) do d = max(d, abs(col:norm(row[col.at]) - col.goal)) end
  return d end

function DATA:ydists() -- () -> DATA
  table.sort(self.rows, function(r) return self:ydist(r) end)
  return self end

-- ## Misc

function l.data(file,     it,self) -- (str) -> DATA
  it = l.csv(file)
  self = DATA(next(it))
  for _,row in pairs(it) do self:add(row) end
  return self end

-- ## Start

-- se.dry: help string consistent with settings if settings derived from help   
-- se.re: regulatr expressions are very useful   
-- se.ll: a little text parsing defines a short syntax for a common task 
-- ai.seeds: debugging, reproducibility needs control of random seeds  
help:gsub("\n%s+-%S%s(%S+)[^=]+=%s+(%S+)", function(k,v) the[k]= l.coerce(v) end)
math.randomseed(the.seed)

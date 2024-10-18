#!/usr/bin/env lua
-- <!-- vim : set ts=2 sw=2 et : -->
-- Line of UNIX shell scripts can list the interpreter for that file (se.sh).
-- All code needs explanation, even your own in a few months time (se.doc).
-- All code has magic control params, which has to be controlled and tuned (se.config).
-- License your code, least someone else takes it from yauo (se.license).
local the,help = {},[[
how.lua : how to change your mind (using TPE + Bayes classifier)
(c) 2024 Tim Menzies (timm@ieee.org). BSD-2 license

USAGE: 
  chmod +x how.lua
  ./how.lua [OPTIONS]

OPTIONS:
  -e end     size of                  = .5
  -g guesses how many todos to sample = 256
  -h help    show help                = false
  -k k       bayes control            = 1
  -m m       bayes control            = 2
  -p p       distance coeffecient     = 2
  -r rseed   random seed              = 1234567891
  -s start   init number of samples   = 4
  -S Stop    stopping for acquire     = 30
	-t train   data                     = ../../moot/optimize/misc/auto93.csv]]

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
  return l.new(NUM, {n=0, at=at or 0, txt=txt or "", mu=0, m2=0, lo=big, hi=-big,
                     goal = (txt or ""):find"-$" and 0 or 1}) end

-- A factory is a generator of instances. e.g. COLS makes SYMs or NUMs (se.pattern).
-- Columns have differnt roles; x-columns are known as independent inputs (observables or
-- controllables) while y-colums are known as dependent output goals.
function COLS:new(names,    col) -- (list[str]) -> COLS
  self = l.new(COLS, {names=names, all={}, x={}, y={}})
  for at,txt in pairs(self.names) do
    col = (txt:find"[A-Z]" and NUM or SYM):new(at,txt)
    l.push(self.all, col)
    if not txt:find"X$" then
      l.push(txt:find"[!+-]$" and self.y or self.x, col) end end
  return self end

-- Rows are summarizes in columns (se.data). DATA is my data amalytics  swiss army knife. It is
-- used everywhere. Decision tree nodes divide one DATA into multiple sub-DATAs. K-means splits
-- one DATAs into smaller DATAs (one per cluster). My Baues classifier stores data from different classes
-- in different DATAs. When I want stats from some ros, I load those rows into a DATA and report
-- the columns, etc.
function DATA:new(names,  rows) -- (list[str], ?list[list], ?bool) -> DATA
  return l.new(DATA, {rows={}, cols=COLS:new(names)}):adds(rows) end

-- New data can mimic the strucutre of existing data (se.data).
function DATA:clone(rows) -- (list[t]) -> DATA
  return DATA:new(self.cols.names):adds(rows) end

-- ## Update

-- Visitors traverse a data structure, calling something at each step (se.patterns).
function DATA:adds(rows) -- (list[list]) -> DATA
  for _,row in pairs(rows or {}) do self:add(row) end
  return self end

-- Incremental learners update their knowledge with each new example (se.ml).
function DATA:add(row) -- (list) -> DATA
  l.push(self.rows, row) 
  for _,col in pairs(self.cols.all) do col:add(row[col.at]) end end

-- (maths) [Welford's algorithm](https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Welford's_online_algorithm)
function NUM:add(x,    d) --(num) -> nil
  if x ~= "?" then
    self.n  = self.n + 1
    d       = x - self.mu
    self.mu = self.mu + d / self.n
    self.m2 = self.m2 + d * (x - self.mu)
    self.hi = max(self.hi, x)
    self.lo = min(self.lo, x) end end

function SYM:add(x,  n) -- (atom,?int) -> nil
  if x ~= "?" then
    n           = n or 1
    self.n      = n + self.n 
    self.has[x] = n + (self.has[x] or 0) 
    if self.has[x] > self.most then 
		  self.most, self.mode = self.has[x], x end end end

-- ## Query

-- When numbers span different ranges, normalize them to 0..1 (ml.norm).
function NUM:norm(x)
  return x=="?" and x or (x - self.lo) / (self.hi - self.lo + 1/big) end

-- Numerics' _central tendency_ and _diversity_ are `mu` and `sd` (se.data).
function NUM:mid() return self.mu end
function NUM:div() return self.n < 2 and 0 or (self.m2/(self.n - 1))^.5 end

-- Symbols _central tendency_ and _diversity_ are `mode` and `entropy` (se.data).
function SYM:mid() return self.mode end
function SYM:div(     e) 
  e=0; for _,n in pairs(self.has) do e = e - n/self.n*log(n/self.n, 2) end 
  return e end

-- Split one DATA into two.
function DATA:split(rows,n,       first,rest)
  first, rest = self:clone(), self:clone()
  for i,row in pairs(rows) do 
    (i <= n and first or rest):add(row) end
  return first,rest end

-- ## Bayes

function SYM:like(x,prior)
  return ((self.has[x] or 0) + the.m*prior) / (self.n + the.m) end

function NUM:like(x,_ ,      v,tmp)
  v = self:div()^2 + 1/big
  tmp = exp(-1*(x - self.mu)^2/(2*v)) / (2*pi*v) ^ 0.5
  return max(0,min(1, tmp + 1/big)) end

function DATA:like(row, nall, nh,     out,tmp,prior,likes) -- (list, int,int) -> number
  prior = (#self.rows + the.k) / (nall + the.k*nh)
  out,likes = 0,log(prior)
  for _,col in pairs(self.cols.y) do 
    tmp = col:like(row[c.at], prior) 
    if tmp > 0 then
       out = out + log(tmp) end end
  return out end

  -- def valley(m1,std1,m2,std2):
  -- """https://stackoverflow.com/questions/22579434/
  -- python-finding-the-intersection-point-of-two-gaussian-curves"""
  -- if std1 < 0.0001: return (m1+m2)/2
  -- if std2 < 0.0001: return (m1+m2)/2
  -- if abs(std1-std2) < 0.01:
  --   return (m1+m2)/2
  -- else:
  --   a  = 1/(2*std1**2) - 1/(2*std2**2)
  --   b  = m2/(std2**2) - m1/(std1**2)
  --   c  = m1**2 /(2*std1**2) - m2**2 / (2*std2**2) - math.log(std2/std1)
  --   x1 = (-b + math.sqrt(b**2 - 4 * a * c)) / (2 * a)
  --   x2 = (-b - math.sqrt(b**2 - 4 * a * c)) / (2 * a)
  --   return x1 if m1 <= x1 <= m2 else x2
  --
function DATA:acquire(labels,fun, -- (?tuple[list,float],?function) -> list[list]
                      Y,todo,done,best,rest)
  fun    = fun or function(b,r) return b + b -r end
  labels = labels or {}
  Y      = function(r) labels[r] = labels[r] or self:ydist(r); return labels[r] end
  todo   = l.shsuffle(self.rows)
  done   = {}
  for row in pairs(labels)     do l.push(done, row) end 
  for i = 1, the.start - #done do l.push(done, table.remove(todo)) end
  while true do
    done = l.sort(done,Y)                   -- sort labelled items
    if #todo <= 3 or #done >= the.Stop then return done end -- maybe stop
    best,rest = self:split(done, sqrt(done))        -- divide labels into two groups
    todo = l.sort(todo, function(r) -- sort todo by some function of like(best), like(rest)
                         if   math.random() > min(#todo, the.guesses)/#todo 
                         then return -big
                         else return fun(best.like(r,#done,2),
                                         rest.like(r,#done,2)) end end)
    l.push(done, table.remove(todo)) end end  -- label the best todo

-- ## Dists

-- Chebyshev distance is max distance of any one attribute to another (ml.dist). 
function DATA:ydist(row,    d) -- (list) -> number
  d = 0; for _,y in pairs(self.cols.y) do d = max(d, abs(y:norm(row[y.at]) - y.goal)) end
  return d end

function DATA:ydists() -- () -> DATA
  self.rows = l.sort(self.rows, function(r) return self:ydist(r) end)
  return self end

-- ## Misc

l.fmt = string.format

function l.data(file,     it,self) -- (str) -> DATA
  for row in l.csv(file) do
    if   self 
    then self:add(row) 
    else self = DATA:new(row) end end
  return self end

function l.shuffle(t,    j) --> list
  for i = #t, 2, -1 do j = math.random(i); t[i], t[j] = t[j], t[i] end
  return t end

function l.coerce(s,     fun) --> atom
  fun = function(s) return s=="true" and true or s ~= "false" and s end
  return math.tointeger(s) or tonumber(s) or fun(l.trim(s)) end

-- (se.abstraction) aka information hiding. liskov iterators
function l.csv(file,     src) --> nil
  if file and file ~="-" then src=io.input(file) end
  return function(     s,t)
    s = io.read()
    if not s then 
      if src then io.close(src) end 
    else
      t={}; for s1 in s:gmatch"([^,]+)" do l.push(t,l.coerce(s1)) end; return t end end end

function l.trim( s ) --> str
  return s:match"^%s*(.-)%s*$" end

function l.o(x,     f,g) --> str
  if type(x) == "number" then return l.fmt("%g",x) end
  if type(x) ~= "table"  then return tostring(x)   end
  f=function(x)   return l.o(x) end
  g=function(k,v) return l.o(k):find"^_" and nil or l.fmt(":%s %s",k,l.o(x[k])) end 
  return "{" .. table.concat(#x>0 and l.map(x,f) or l.sort(l.maps(x,g))," ").."}" end

function l.oo(x) --> nil
    print(l.o(x)) end

function l.map(t,fun,     u) --> list
  u={}; for _,v in pairs(t) do u[1+#u] = fun(v)  end; return u end

function l.maps(t,fun,    u) --> list
  u={}; for k,v in pairs(t) do u[1+#u]=fun(k,v)  end; return u end

function l.lt(x) return function(t,u) return t[x] < u[x] end end

-- (se.pattern) decorate-sort-undecorate; also known as the  Schwartzian transform 
function l.sort(t,fun,     u,v)
  u={}; for _,x in pairs(t) do l.push(u, {fun(x),x}) end
  v={}; for _,x in pairs(l.sort(u,l.lt(1))) do l.push(v, x[2]) end
  return v end

function l.normal(mu,sd,    r)
  r = math.random
  return (mu or 0) + (sd or 1) * sqrt(-2*log(r())) * cos(2*pi*r()) end

function l.cli(t)
  for k,v in pairs(t) do
    v = tostring(v)
    for n,x in ipairs(arg) do
      if x=="-"..(k:sub(1,1)) or x=="--"..k then
        v= v=="false" and "true" or v=="true" and "false" or arg[n+1] end end 
    t[k] = l.coerce(v) end 
  if t.help then os.exit(print(help)) end
  math.randomseed(the.rseed or 1)
  return t end

function l.lts(a,b,c)
  return a<b and b<c end

function l.push(t,x) t[#t+1]=x; return x end

-- OO is defined by class, instances, methods, messaging, inheritance, abstractions, 
-- encapuslation (formatio hiding, which can be optional or enfored or somewhere in between), polymorphism (se.prog.oo).
-- Encapulation and packaging ahve a connection. Abstaction needs querying support (see lipskov iterators and error handlers).
-- For a nice, and brief, survey of the literature, see https://www.tonymarston.co.uk/php-mysql/abstraction.txt.
-- Note that this comment is LONGER than the code required for my LUA implementation of class, instance, methods,
-- messaging, encapulation, abstraction and polymorphism.
function l.new(klass, obj) --> obj 
  klass.__index    = klass
  klass.__tostring = klass.__tostring or l.o
  return setmetatable(obj,klass) end

-- ## Start
local eg={}
function eg.the() l.oo(the) end -- try ths with different command line settings

function eg.num(     n)
  n=NUM:new()
	for i=1,10^3 do n:add(l.normal(10,2)) end
	assert(n.n==1000 and l.lts(9.9, n:mid(),10) and l.lts(1.95,n:div(),2)) end

function eg.sym(     s)
  s=SYM:new()
	for _,x in pairs{"a","a","a","a","b","b","c"} do s:add(x) end
	assert(s.n==7 and s:mid() == "a" and l.lts(1.37, s:div(), 1.38)) end

function eg.COLS(       t)
  t = COLS:new({"name","Age","ShoesX","Growth-"}).all
	assert(t[#t].goal == 0)
	assert(getmetatable(t[1]) == SYM) end

function eg.csv() 
  for row in l.csv(the.train) do l.oo(row) end end

function eg.DATA(       d,n) 
  d=l.data(the.train) 
  assert(#d.rows==398) 
  n=0; for _,row in pairs(d.rows) do n = n + #row end; assert(n==3184)
  assert(#d.cols.y==3) 
  assert(#d.cols.x==4) 
  assert(0 == d.cols.y[1].goal)
  assert(l.lts(5.45,d.cols.x[1]:mid(),5.5))
end

function eg.rxy(       d)
  -- ./how2.lua --rxy ../../moot/optimize/[chmp]*/*.csv | sort -t, -nk 2
  for _,f in pairs(arg) do
	  print(f)
	  if f:find"csv$" then 
		  d = l.data(f) 
			print(l.fmt("%8s, %8s, %8s,  %8s", #d.rows,#d.cols.x,#d.cols.y, (f:gsub(".*/", "  ")))) end end end

function eg.likes(    d)
  d = l.data(the.train)
	for i,row in pairs(d:ydists().rows) do
	  if (i-1) % 30 == 0 then print(i,l.o(row)) end end end 
-- se.dry: help string consistent with settings if settings derived from help   
-- se.re: regulatr expressions are very useful   
-- se.ll: a little text parsing defines a convenient shorthand for a common task 
-- ai.seeds: debugging, reproducibility needs control of random seeds  
help:gsub("\n%s+-%S%s(%S+)[^=]+=%s+(%S+)", function(k,v) the[k]= l.coerce(v) end)
math.randomseed(the.rseed)

if arg[0]:find"how2.lua" then
  l.cli(the)
  for i,s in pairs(arg) do
     if  eg[s:sub(3)] then eg[s:sub(3)]() end end end

return {NUM=NUM, SYM=SYM, DATA=DATA, COLS=COLS, the=the, help=help, lib=l}

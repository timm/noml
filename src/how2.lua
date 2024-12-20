#!/usr/bin/env lua
-- vim : set ts=2 sw=2 et :
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
  -c conf       statistical confidence   = 0.01
  -C Cliffs     threshjold for cliffs    = 0.195
  -B Bootstraps num.of bootstraps        = 256
  -e end        size of                  = .5
  -f far        num.far samples          = 30
  -g guesses    how many todos to sample = 100
  -h help       show help                = false
  -k k          bayes control            = 1
  -l leaf       leaf size                = .5
  -m m          bayes control            = 2
  -p p          distance coeffecient     = 2
  -r rseed      random seed              = 1234567891
  -s start      init number of samples   = 4
  -S Stop       stopping for acquire     = 25
  -t train      data                     = ../../moot/optimize/misc/auto93.csv]]
    
-- There are many standard cliches; e.g. create update query (se.patterns).
local big = 1E32
local NUM, SYM, DATA, COLS, TREE, l = {}, {}, {}, {}, {}, {}
local abs, cos, exp, log = math.abs,  math.cos,  math.exp, math.log
local max, min, pi, sqrt = math.max,  math.min,  math.pi, math.sqrt

-- ## Create

-- Data can have numeric or symbolic columns (se.data).
-- Type signatures are very useful (se.doc).
function SYM:new(txt,at) -- (int, str) -> SYM
  return l.new(SYM, {n=0, at=at or 0, txt=txt or "", has={}, most=0, mode=nil}) end

-- Numeric goals have a best value: 0 if minimizing and 1 if maximizing (se.data).
function NUM:new(txt,at) -- (int, str) -> NUM
  return l.new(NUM, {n=0, at=at or 0, txt=txt or "", mu=0, m2=0, lo=big, hi=-big,
                     goal = (txt or ""):find"-$" and 0 or 1}) end

-- A factory is a generator of instances. e.g. COLS makes SYMs or NUMs (se.pattern).
-- Columns have differnt roles; x-columns are known as independent inputs (observables or
-- controllables) while y-colums are known as dependent output goals.
function COLS:new(names,    col) -- (list[str]) -> COLS
  self = l.new(COLS, {names=names, all={}, x={}, y={}})
  for at,txt in pairs(self.names) do
    col = (txt:find"[A-Z]" and NUM or SYM):new(txt,at)
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

function NUM:delta(other,      y,z,e)
  e, y, z = 1E-32, self, other
  return abs(y.mu - z.mu) / ( (e + y:div()^2/y.n + z:div()^2/z.n)^.5) end

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
  for _,col in pairs(self.cols.x) do 
    tmp = col:like(row[col.at], prior) 
    if tmp > 0 then
       out = out + log(tmp) end end
  return out end

-- function DATA:acquire(  labels,fun) -- (?tuple[list,float],?function) -> list,list[list]
--   local b4,todo,done,m = {},{},{},nil
--   labels = labels or {}
--   for row in pairs(labels) do l.push(b4,row) end
--   m = max(1, the.start - #b4)
--   for i,row in pairs(l.shufflex(b4)) do 
--     l.push(i<=m and todo or done, row) end
--   fun = fun or function(b,r) return b + b -r end,
--   self:acquire1(
--      todo, done,
--      function(r)    return  fun(best.like(r #done, 2), rest.like(r, #done, 2)) enda,
--      function(r)    labels[r] = labels[r] or self:ydist(r); return labels[r] end,
--      function(rows) return self.ydists(self.clone(rows)).rows end) end
--
-- function DATA:acquire1(todo, done, fun, Y,order,     guess,top)
--   function guess(todo.    score,best,rest)
--     best, rest = self:clone(), self:clone()
--     for i,row in pairs(done) do 
--       (i <= sqrt(#done) and best or rest).add(row) end
--     table.sort(todo, function(r) return fun(r) end) end
--
--   while #done <= the.Stop do
--     guess(todo)
--     l.push(done, table.remove(todo))
--     done = order(done)
--     if #todo <= 3 then break end end 
--   return done end
--   -- def valley(m1,std1,m2,std2):
--   -- """https://stackoverflow.com/questions/22579434/
--   -- python-finding-the-intersection-point-of-two-gaussian-curves"""
--   -- if std1 < 0.0001: return (m1+m2)/2
--   -- if std2 < 0.0001: return (m1+m2)/2
--   -- if abs(std1-std2) < 0.01:
--   --   return (m1+m2)/2
--   -- else:
--   --   a  = 1/(2*std1**2) - 1/(2*std2**2)
--   --   b  = m2/(std2**2) - m1/(std1**2)
--   --   c  = m1**2 /(2*std1**2) - m2**2 / (2*std2**2) - math.log(std2/std1)
--   --   x1 = (-b + math.sqrt(b**2 - 4 * a * c)) / (2 * a)
--   --   x2 = (-b - math.sqrt(b**2 - 4 * a * c)) / (2 * a)
--   --   return x1 if m1 <= x1 <= m2 else x2
--
local function _focus(t,b,r,    l,m)
  b,r = exp(b), exp(r)
  l = 0.25
  m = 1 + (exp(l*t) - 1) / (exp(l*(b-1)) - 1)
  return ((b+1)^m + (r+1))/ (abs(b-r) + 1E-32) end

function DATA:acquire(  labels,fun, -- (?tuple[list,float],?function) -> list[list]
                      Y,todo,done,best,rest)
  --fun    = fun or function(b,r) b,r = exp(b), exp(r); return (b + r)/(abs(b-r)+ 0.0000000001)  end
  fun    = fun or function(_,b,r) return b  - r end
  --fun    = fun or function(_,b,r) return math.random() < 0.5 end
  _,labels = self:tree(true)
  Y      = function(r) labels[r] = labels[r] or self:ydist(r); return labels[r] end
  H      = function(r) 
                       --#print(min(#todo, the.guesses)/#todo )
                       if   math.random() > min(#todo, the.guesses)/#todo 
                       then return -10^8
                       else return fun(#done,
                                       best:like(r,#done,2),
                                       rest:like(r,#done,2)) end end
  todo   = {}
  done   = {}
  for _, row in pairs(l.shuffle(self.rows)) do l.push(todo, row) end
  for row in pairs(labels)     do l.push(done, row) end 
  for i = 1, the.start - #done do l.push(done, table.remove(todo)) end
  while true do
    done = l.keysort(done, Y)
    if #todo <= 4 or #done >= the.Stop then return done end -- maybe stop
    best,rest = self:split(done, sqrt(#done))        -- divide labels into two groups
    todo = l.keysort(todo, H)
    for i=1,2 do
      l.push(done, table.remove(todo,1)) 
      l.push(done, table.remove(todo))  end
    end end -- label the best todo

-- ## Dists

function SYM:dist(a,b)
  return (a=="?" and b=="?" and 0) or (a==b and 0 or 1) end

function NUM:dist(a,b)
  if a=="?" and b=="?" then return 1 end
  a,b = self:norm(a), self:norm(b)
  a = a ~= "?" and a or (b<0.5 and 1 or 0)
  b = b ~= "?" and b or (a<0.5 and 1 or 0)
  return abs(a-b) end

-- Minkowski  distance
function DATA:xdist(row1,row2,    d,n) -- (list) -> number
  n,d = 0,0
  for _,x in pairs(self.cols.x) do 
    d = d + x:dist(row1[x.at], row2[x.at])^the.p
    n = n + 1 end
  return (d/n)^(1/the.p) end

-- -- Chebyshev distance is max distance of any one attribute to another (ml.dist). 
-- function DATA:ydist(row,    d) -- (list) -> number
--   d = 0
--   for _,y in pairs(self.cols.y) do d = max(d, abs(y:norm(row[y.at]) - y.goal)) end
--   return d end
--
function DATA:ydist(row1,    d,n) -- (list) -> number
  n,d = 0,0
  for _,y in pairs(self.cols.y) do 
    d = d + (y:norm(row1[y.at]) - y.goal)^the.p
    n = n + 1 end
  return (d/n)^(1/the.p) end

function DATA:ydists() -- () -> DATA
  self.rows = l.keysort(self.rows, function(r) return self:ydist(r) end)
  return self end

function DATA:twoFar(rows,above, Y,sortp)
  local most,a0,b0,a,b,d
  most = 0
  for i=1,the.far do 
    a0,b0 = above or l.any(rows), l.any(rows)
    d = self:xdist(a0,b0)
    if d > most then most,a,b = d,a0,b0 end end
  if sortp and Y(b) < Y(a) then a,b = a,b end
  return most,a,b end

function DATA:half(rows,above,Y,  sortp) --> float,rows,rows,row,row
  local ls,rs,c,l1,r1,cos,fun
  c,l1,r1 = self:twoFar(rows,above,Y,sortp)
  cos   = function(a,b) return (a^2 + c^2 - b^2) / (2*c+ 1E-32) end 
  fun   = function(row) return cos(self:xdist(row,l1), self:xdist(row,r1)) end
  ls,rs = {},{}
  for i,row in pairs(l.keysort(rows,fun)) do
    l.push(i <= #rows//2 and ls or rs, row) end
  return self:xdist(l1,rs[1]), ls, rs, l1, r1 end

function TREE:new(data, lvl, guard, lefts, rights)
  return l.new(TREE, {data=data, lvl=lvl, guard=guard, lefts=lefts, rights=rights}) end

function TREE:show()
  print(l.fmt("%s%s", ('|.. '):rep(self.lvl), #self.data.rows))
  if self.lefts  then self.lefts:show() end
  if self.rights then self.rights:show() end end

function DATA:tree(sortp, depth,stop)
  local labels,Y,fun
  labels= {}
  Y     = function(r) labels[r] = labels[r] or self:ydist(r); return labels[r] end
  stop  = stop or ((#self.rows)^the.leaf)
  depth = depth or big
  go    = function(rows, lvl, guard,above)
            local ls,rs,l1,r1,goLeft,goRight,lefts,rights,cut
            if #rows > 2*stop and lvl < depth then
              cut,ls,rs,l1,r1 = self:half(rows,above,Y,sortp)
              goLeft  = function(row) return self:xdist(row,l) < cut end
              goRight = function(row) return not goLeft(row) end
              lefts   = go(ls, lvl+1, goLeft,l1)
              if sortp ~= true then rights = go(rs, lvl+1, goRight,r1) end end
            return TREE:new(self:clone(rows),lvl,guard,lefts,rights)  end
  return go(self.rows, 0), labels end

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

function l.sort(t,fun) table.sort(t,fun); return t end

-- (se.pattern) decorate-sort-undecorate; also known as the  Schwartzian transform 
function l.keysort(t,fun,     u,v)
  u={}; for _,x in pairs(t) do l.push(u, {fun(x),x}) end
  v={}; for _,x in pairs(l.sort(u, l.lt(1))) do l.push(v, x[2]) end
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

function l.any(t) --> any
  return t[math.random(#t)] end

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

-- ## Stats

local SOME={}
function SOME:new(txt)
  return l.new(SOME,{num=NUM:new(txt),mu=0, all={}}) end

function SOME:div(x) return self.num:div() end

function SOME:add(x)
  if x~="?" then
     l.push(self.all,x)
     self.num:add(x) 
     self.mu = self.num.mu end end

function SOME:same(other)
  return self:cliffs(other) and self:bootstrap(other) end

function SOME:cliffs(other)
  local lt,gt,n = 0,0,0
  for _,x in pairs(self.all) do
     for _,y in pairs(other.all) do
       n = n + 1
       if y > x then gt = gt + 1 end
       if y < x then lt = lt + 1 end end end
  return abs(gt - lt)/n <= the.Cliffs end

function SOME:bootstrap(other)
  local y0,z0 = self.all, other.all
  local  x,y,z,xmu,ymu,zmu,yhat,zhat,tobs,n
  x, y, z, yhat, zhat = NUM:new(), NUM:new(), NUM:new(), {}, {}
  for _,y1 in pairs(y0) do x:add(y1); y:add(y1)           end
  for _,z1 in pairs(z0) do x:add(z1); z:add(z1)           end
  xmu, ymu, zmu = x.mu, y.mu, z.mu
  for _,y1 in pairs(y0) do yhat[1+#yhat] = y1 - ymu + xmu end
  for _,z1 in pairs(z0) do zhat[1+#zhat] = z1 - zmu + xmu end
  tobs = y:delta(z)
  n = 0
  for _= 1,the.Bootstraps do
    local tmp1,tmp2
    tmp1=NUM:new(); for _ in pairs(yhat) do tmp1:add(l.any(yhat)) end
    tmp2=NUM:new(); for _ in pairs(zhat) do tmp2:add(l.any(zhat)) end
    n = n + (tmp1:delta(tmp2) > tobs and 1 or 0) end
  return n / the.Bootstraps >= the.conf end

function SOME.lessMoreSame(samples, less, more,same,keys,delta)
  keys=keys or {}
  less,more,same,delta = less or {}, more or {}, same or {},delta or {}
  for i,one in pairs(samples) do
    for j,two in pairs(samples) do
      if j>i then
        local k,what
        k = l.fmt("%s,%s",one.num.txt, two.num.txt)
				keys[k]=k
        delta[k] = delta[k] or NUM:new()
        delta[k]:add(one.mu - two.mu)
        what = one:same(two) and same or (one.mu < two.mu and less or more)
        what[k]= 1 + (what[k] or 0) end end end 
  print("")
  for k,_ in pairs(keys) do
	   print(l.fmt("%3s, %3s, %3s, %.3f,%s", less[k] or 0 ,  same[k] or 0,  more[k] or 0, 
           delta[k].mu,l.o(k))) end 
	return less,more,same,keys end 


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
    if f:find"csv$" then 
      d = l.data(f) ; 
      print(l.fmt("%8s, %8s, %8s,  %8s", #d.rows,#d.cols.x,#d.cols.y, (f:gsub(".*/", "  ")))) end end end

function eg.ydist(    d,num,y)
  d = l.data(the.train)
  num=NUM:new()
  for i,row in pairs(d:ydists().rows) do
    y=d:ydist(row)
    num:add(y)
    if i==1 or i % 30 == 0 then print(i,l.o(row),y) end end 
  print(num:mid()) end 

function eg.likes(    d,n)
  d = l.data(the.train)
  for i,row in pairs(l.keysort(d.rows, 
                            function(r) return d:like(r,#d.rows,2) end)) do
    if i==1 or i % 30 == 0 then 
      print(i,l.o(row),d:like(row,#d.rows,2)) end end  end

function eg.tree(      d)
  d = l.data(the.train)
  tree,labels=d:tree(true)
  for r,_ in pairs(labels) do l.oo(r) end
  tree:show() 
  done = d:acquire(labels)
  print(#done, d:ydist(done[1])) end

function eg.stats(     d,n,s1,s2)
   B=function(x) return x and "y" or "." end
   for _,n in pairs{20,40,80, 160,320} do
     d=1
     print("")
     while d < 1.5 do
       s1=SOME:new(); for i=1,n do s1:add(math.random()^2 + math.random()^.5 ) end
       s2=SOME:new(); for _,x in pairs(s1.all) do s2:add(x *d) end
       print(l.fmt("%4s %6.3f %s %s %s",n,d, 
            B(s1:cliffs(s2)), B(s1:bootstrap(s2)), B(s1:same(s2))))
       d=d*1.05 end end end
  
local function _guess(data1,n,    rows,t)
   rows = l.shuffle(data1.rows)
   t={}; for i=1,min(n,#data1.rows) do  t[1+#t] = data1:ydist(rows[i]) end
   return l.sort(t)[1] end

function eg.acqs()
  local less,more,same,keys,deltas={},{},{},{},{}
  for _,f in pairs(arg) do
    if f:find"csv$" then 
      print(f)
      the.train = f 
      local S,d,acqs,rnds,asIs,adds,eps
      S = function(n) return l.fmt("%.3f,  ",n) end
      d = l.data(the.train)
      acqs = {[12]=SOME:new("acq,15"), [25]=SOME:new("acq,25"), [100]=SOME:new("acq,100"), [200]=SOME:new("acq,200")}
      rnds = {[12]=SOME:new("rnd,15"), [25]=SOME:new("rnd,25"), [100]=SOME:new("rnd,100"), [200]=SOME:new("rnd,200")}
      asIs = SOME:new("asIs")
      for _,row in pairs(d.rows) do asIs:add(d:ydist(row)) end
      eps = asIs:div()*.35
      add = function(n,x)  n:add( ((0.5 + x/eps)//1)*eps)  end
      for n,acq in pairs(acqs) do 
			  io.write(n,": ")
        the.Stop = n
        for i=1,20 do io.write("."); add(acq, d:ydist(d:acquire()[1])) end
        for i=1,20 do io.write("."); add(rnds[n], _guess(d, the.Stop)) end  
        print("") end 
      print(the.train:gsub("^.*/","") ..", "..  #d.rows ..", ".. #d.cols.x ..", ".. #d.cols.y ..", "..
            S(asIs.mu) ..  
             S(acqs[12].mu) .. S(acqs[25].mu) .. S(acqs[100].mu) .. S(acqs[200].mu) ..
             S(rnds[12].mu) .. S(rnds[25].mu) .. S(rnds[100].mu) .. S(acqs[200].mu)) 
      local all={}; for _,t in pairs{acqs,rnds} do for _,s in pairs(t) do l.push(all,s) end end 
      SOME.lessMoreSame(all,less,more,same,keys,deltas) end end end
	   -- se.dry: help string consistent with settings if settings derived from help   


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

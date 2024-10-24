#!/usr/bin/env lua
-- vim : set tabstop=2 shiftwidth=2 expandtab :
local big = 1E32
local fmt, pop = string.format, table.remove
local pi, abs, cos, exp = math.pi, math.abs, math.cos, math.exp
local log, max, min, sqrt = math.log, math.max, math.min, math.sqrt

local R = math.random
local SYM,NUM,DATA = {},{},{}

local the = {k=1, m=2, p=2, rseed=1234567891,
             train="../../moot/optimize/misc/auto93.csv"}

----------------- ----------------- ----------------- ----------------- ------------------
-- lists
local function push(t,x) t[1+#t] = x; return x end

local function split(t,n)
  local u,v = {},{}
  for j,x in pairs(t) do push(j <= n and u or v,x) end
  return u,v end

-- random 
local function any(t)    
  return t[R(#t)] end

local function many(t,  n) 
  u={}; for i=1,(n or #t) do u[i] = any(t) end; return u end

-- sorting
local function lt(x) 
  return function(a,b) return a[x] < b[x] end end

local function sort(t,fn) 
  table.sort(t,fn); return t end

local function shuffle(t,    j)
  for i = #t, 2, -1 do j = R(i); t[i], t[j] = t[j], t[i] end
  return t end

-- mapping
local function kap(t,fn,    u) --> list
  u={}; for k,v in pairs(t) do u[1+#u]=fn(k,v)  end; return u end

local function map(t,fn,     u) --> list
  u={}; for _,v in pairs(t) do u[1+#u] = fn(v)  end; return u end

local function sum(t,fn,     n)
  n=0; for _,x in pairts(t) do n=n+(fn and fn(x) or x) end; return n end

local function adds(it,t) 
  for _,x in pairs(t or {}) do it:add(x) end; return it end

local function keysort(t,fn,     decorate,undecorate)
  decorate   = function(x) return {fn(x),x} end
  undecorate = function(x) return x[2] end
  return map(sort(map(t,decorate),lt(1)), undecorate) end

-- string to thing
local function coerce(s,     fn,trim) 
  trim= function(s) return s:match"^%s*(.-)%s*$" end
  fn  = function(s) return s=="true" and true or s ~= "false" and s end
  return math.tointeger(s) or tonumber(s) or fn(trim(s)) end

local function csv(file,     src)
  if file and file ~="-" then src=io.input(file) end
  return function(     s,t)
    s = io.read()
    if   not s 
    then if src then io.close(src) end 
    else t={}; for s1 in s:gmatch"([^,]+)" do push(t,coerce(s1)) end; return t end end end

-- thing to string
local function o(x,     f,g,go) --> str
  f  = function() return #x>0 and map(x,o) or sort(kap(x,g)) end
  g  = function(k,v) if go(k) then return fmt(":%s %s",k,o(x[k])) end end
  go = function(k,v) return not o(k):find"^_" end
  return type(x)=="number" and fmt("%g",x) or  
         type(x)~="table"  and tostring(x) or 
         "{" .. table.concat(f()," ") .. "}" end 

local function oo(x) 
  print(o(x)) end

-- polymorphism
local function new(klass, obj)
  klass.__index    = klass
  klass.__tostring = klass.__tostring or o
  return setmetatable(obj, klass) end

----------------- ----------------- ----------------- ----------------- -----------------
function SYM:new(is,num) 
  return new(SYM, {at=num, txt=s, n=0, has={}, most=0, mode=nil}) end

function SYM:add(x)
  if x~="?" then
    self.n = self.n + 1
    self.has[x] = 1 + (self.has[x] or 0) 
    if self.has[x] > self.most then self.most, self.mode = self.has[x], x end end end

function SYM:like(x,prior)
  return ((self.has[x] or 0) + the.m*prior) / (self.n + the.m) end

----------------- ----------------- ----------------- ----------------- -----------------  
function NUM:new(s,num) 
  return new(NUM, {at=num, txt=s, n=0, mu=0, m2=0, sd=0, lo=big, hi=-big,
                   goal = (s or ""):find"-$" and 0 or 1}) end

function NUM:add(x)
  if x~="?" then
    self.n = self.n + 1
    local d = x - self.mu
    self.mu = self.mu + d / self.n
    self.m2 = self.m2 + d * (x - self.mu)
    self.sd = self.n < 2 and 0 or (self.m2/(self.n - 1))^.5
    if x > self.hi then self.hi = x end
    if x < self.lo then self.lo = x end end end

function NUM:like(x,_ ,      v,tmp)
  v = self.sd^2 + 1/big
  tmp = exp(-1*(x - self.mu)^2/(2*v)) / (2*pi*v) ^ 0.5
  return max(0,min(1, tmp + 1/big)) end
  
function NUM:norm(x)
  return x=="?" and x or (x - self.lo)/(self.hi - self.lo) end
       
function NUM:delta(other,      y,z,e)
  e, y, z = 1E-32, self, other
  return abs(y.mu - z.mu) / ( (e + y.sd^2/y.n + z.sd^2/z.n)^.5) end
             
----------------- ----------------- ----------------- ----------------- -----------------  
function DATA:new(names)
  local all,x,y = {},{},nil
  for at,x in pairs(names) do 
    push(all, x:find"^[A-Z]" and NUM(x,at) or SYM(x,at))
    if not x:find"X$" then
      push(y and x:find"[!+-]$" or x, all[#all]) end end
  return {rows={}, cols={names=names, all=all, x=x, y=y}} end

function DATA:add(row) 
  push(self.rows, row)
  for _,col in pairs(self.cols.all) do col:add(row[col.at]) end end

function DATA:clone(rows) 
  return adds(DATA(self.cols.names),rows) end
    
function DATA:loglike(row, nall, nh)
  local prior,out,tmp
  prior = (#self.rows + the.k) / (nall + the.k*nh)
  out,tmp = 0,log(prior)
  for _,col in pairs(self.cols.y) do 
    tmp = col:like(col, row[col.at], prior)
    if tmp > 0 then
       out = out + log(tmp) end end
  return out end

function DATA:ydist(row)
  local d = 0
  for _,col in pairs(self.cols.y) do
    d = d + (abs(col:norm(row[col.at]) - col.goal))^the.p end
  return (d/#self.cols.y)^(1/the.p) end

function DATA:learn(ntrain)
  local Y,B,R,BR,rows,n1,train,test,todo,done,best,rest,b2,a,b
  Y          = function(r) return self:ydist(r) end
  B          = function(r) return best:loglike(r, #done, 2) end
  R          = function(r) return rest:loglike(r, #done, 2) end
  BR         = function(r) return B(r) - R(r) end
  train,test = split(shuffle(self.rows), (ntrain * #done))
  todo,done  = split(train, the.start)
  while true do
    done = keysort(done,Y)
    if #done > the.Stop or #todo < 5 then break end
    best,rest = split(done, sqrt(#done))
    best,rest = self:clone(best), self:clone(rest)
    todo      = keysort(todo,BR)
    push(done, pop(todo));   push(done, pop(todo))
    push(done, pop(todo,1)); push(done, pop(todo,1)) 
  end
  return done[1], keysort(test,BR)[#test] end

-- stats
function cliffs(xs,ys)
  local lt,gt,n = 0,0,0
  for _,x in pairs(xs) do
     for _,y in pairs(ys) do
       n = n + 1
       if y > x then gt = gt + 1 end
       if y < x then lt = lt + 1 end end end
  return abs(gt - lt)/n <= the.Cliffs end -- 0.195 

function bootstrap(y0,z0,confidence,bootstraps)
  --non-parametric significance test From Introduction to Bootstrap,
  -- Efron and Tibshirani, 1993, chapter 20. https://doi.org/10.1201/9780429246593
  local x,y,z,delta0,yhat,zhat,n,samples, sample1, sample2
  x,y,z  = adds(adds(NUM:new(),y0),z0), adds(NUM:new(),y0), adds(NUM:new(),z0)
  delta0 = y:delta(z)
  yhat   = map(y0, function(y1) return y1 - y.mu + x.mu end)
  zhat   = map(z0, function(z1) return z1 - z.mu + x.mu end)
  n = 0
  samples= bootstraps or the.stats.bootstraps or 512 
  for i=1, samples do
    sample1, sample2 = adds(NUM:new(),many(yhat)), adds(NUM:new(),many(zhat))
    n = n + (sample1.delta(sample2) > delta0 and 1 or 0) end
  return n / samples >= (confidence or the.stats.confidence or 0.05) end

-----------------------------------------------------------------------------------------
local eg={}

function eg.any(  a)
  a = {10,20,30,40,50,60}
  for i=1,5 do
	  map({any(a), many(a,3), shuffle(a), keysort(a, function(x) return -x end)},oo) end end

function eg.split(    a)
  a={10,20,30,40,50,60}
	b,c = split(a,3)
	print(o(b), o(c)) end

function eg.sort(    t)
  t={1,2,3,4,5,6,7}
  t=sort(t, function(x,y) return  x > y end)
  oo{10,4,5}
  oo(t) end

function eg.num(    n,N) 
  N = function(mu,sd) return (mu or 0)+(sd or 1)*sqrt(-2*log(R()))*cos(2*pi*R()) end
  n = NUM:new()
	for _ = 1,1000 do n:add( N(10,2) ) end
	assert(10-n.mu < 0.1 and 2-n.sd < 0.03) end

function eg.sym(    s) 
  s = adds(SYM:new(), {"a","a","a","a","b","b","c"})
	print(s.mode, o(s.has)) end

function eg.csv(   d)
  for row in csv(the.train) do oo(row) end end

math.randomseed(the.rseed)
for _,s in pairs(arg) do
  if eg[s:sub(3)] then eg[s:sub(3)]() end end 

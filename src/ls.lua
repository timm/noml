local big = 1E32
local fmt, pop = string.format, table.remove
local pi, abs, exp, log = math.pi, math.abs, math.exp, math.log
local max, min, sqrt    = math.max, math.min, math.sqrt

local SYM,NUM,DATA = {},{},{}

local the = {k=1, m=2, p=2}

----------------- ----------------- ----------------- ----------------- ------------------
local function adds(it,t) 
  for _,x in pairs(t or {}) do it:add(x) end; return it end

local function sort(t,fn)
  table.sort(t,fn)
  return t end

local function map(t,fn,     u) --> list
  u={}; for _,v in pairs(t) do u[1+#u] = fn(v)  end; return u end

local function kap(t,fn,    u) --> list
   u={}; for k,v in pairs(t) do u[1+#u]=fn(k,v)  end; return u end

local function sum(t,fn,     n)
  n=0; for _,x in pairts(t) do n=n+(fn and nf(x) or x) end; return n end

local function o(x,     fn) --> str
  fn = function(k,v) return o(k):find"^_" and nil or fmt(":%s %s",k,o(x[k])) end
  return (type(x) == "number" and fmt("%g",x)) or ( 
          type(x) ~= "table"  and tostring(x)) or (   
          #x>0 and "{" .. table.concat(#x>0 and map(x,o) or sort(kap(x,fn))," ") .. "}") end 

local function oo(x) print(o(x)) end

local function push(t,x) 
  t[1+#t] = x; return x end

local function trim(s) 
  return s:match"^%s*(.-)%s*$" end

local function coerce(s,     fn) 
  fn = function(s) return s=="true" and true or s ~= "false" and s end
  return math.tointeger(s) or tonumber(s) or fn(trim(s)) end

local function csv(file,     src)
  if file and file ~="-" then src=io.input(file) end
  return function(     s,t)
    s = io.read()
    if   not s 
    then if src then io.close(src) end 
    else t={}; for s1 in s:gmatch"([^,]+)" do push(t,coerce(s1)) end; return t end end end

local function split(t,n)
  local u,v = {},{}
  for j,x in pairs(t) do push(j <= n and u or v,x) end
  return u,v end

local function shuffle(t,    j)
  for i = #t, 2, -1 do j = math.random(i); t[i], t[j] = t[j], t[i] end
  return t end

local function lt(x) return function(a,b) return a[x] < b[x] end end

local function keysort(t,fn,     u,v)
  u={}; for _,x in pairs(t) do u[1+#u] = {fn(x),x} end
  v={}; for _,x in pairs(sort(u, lt(1))) do v[1+#v] = x[2] end
  return v end

local function new(klass, obj) --> obj
  klass.__index    = klass
  klass.__tostring = klass.__tostring or o
  return setmetatable(obj,klass) end

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

local eg={}
function eg.num(    n) 
   n=adds(NUM:new("fred",2),{1,2,3,4,5,6,7,8})
   oo(n) end

function eg.sort(    t)
   t={1,2,3,4,5,6,7}
   t=sort(t, function(x,y) return  x > y end)
   oo{10,4,5}
   oo(t) end

for _,s in pairs(arg) do
  if eg[s:sub(3)] then eg[s:sub(3)]() end end 

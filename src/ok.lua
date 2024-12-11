local help=[[
ok.lua : optimization via kmean++ style clustering
(c) 2024 Tim Menzies <timm@ieee.org>  MIT license]]

local the = {seed= 1234567891,
             p=2, samples=32,
             data= "../../moot/optimize/misc/auto93.csv"}

local Sym,Num,Cols,Data = {},{},{},{}
-------------------------------------------------------------------------------
local adds,any,cat,coerce,csv,fmt,gt,keysort,lt
local map,maps,min,new,push,prefer,shuffle,sort,sum

function push(t,x) t[1+#t]=x; return x end

function any(t) return t[math.random(#t)] end

function lt(x) return function(a,b) return a[x] < b[x] end end
function gt(x) return function(a,b) return a[x] > b[x] end end

function sort(t,F) table.sort(t,F); return t end

function keysort(t,F,     DECORATE,UNDECORATE)
  DECORATE   = function(x) return {F(x),x} end
  UNDECORATE = function(x) return x[2] end
  return map(sort(map(t,DECORATE),lt(1)), UNDECORATE) end

function shuffle(t,    j) --> list
  for i = #t, 2, -1 do j = math.random(i); t[i], t[j] = t[j], t[i] end
  return t end

function sum(t,F,    n) n=0;  for _,v in pairs(t) do n = n + F(  v) end; return n end
function map(t,F,    u) u={}; for _,v in pairs(t) do u[1+#u]=F(  v) end; return u end
function maps(t,F,   u) u={}; for k,v in pairs(t) do u[1+#u]=F(k,v) end; return u end

function min(t,F,    lo,x,tmp) 
  lo=math.huge
  for k,v in pairs(t) do
    tmp=F(v)
    if tmp < lo then lo,x = tmp,v end end
  return x end

function coerce(s) return math.tointeger(s) or tonumber(s) or s:match"^%s*(.-)%s*$" end

function csv(file,     F,src)
  F= function(s,t) for s1 in s:gmatch"([^,]+)" do push(t,coerce(s1)) end; return t end
  src= io.input(file)
  return function(s)
    s = io.read()
    if s then return F(s,{}) else io.close(src) end end end 

function prefer(t,    all,r,u,x,n,anything)
  all,u=0,{}; for x,n in pairs(t) do u[1+#u]= {x,n}; all=all+n end
  r = math.random()
  for _,xn in pairs(sort(u,gt(2))) do
    x,n = xn[1],xn[2]
    anything = anything or x
    r = r - n/all
    if r <= 0 then return x end end 
  return anything end

fmt = string.format

function cat(t,  F) 
  if type(t) == "number" then return fmt(t//1==t and "%s" or "%.3g",t) end
  if type(t) ~= "table"  then return tostring(t) end 
  F = function(k,v) return fmt(":%s %s",k,cat(v)) end
  return "{" .. table.concat( #t>0 and map(t,cat) or sort(maps(t,F))," ") .. "}" end

function new(meta, t) 
  meta.__index = meta
  meta.__tostring = cat
  return setmetatable(t,meta) end

function adds(t,  it)
  it = it or (type(t[1])=="number" and Num or Sym):new()
  print(it)
  for _,x in pairs(t) do it:add(x) end
  return it end

-----------------------------------------------------------------------------------------

function Sym:new(s,i) 
  return new(Sym,{at=i, txt=s, n=0}) end

function Num:new(s,i) 
  return new(Num, {at=i, txt=s, n=0, lo=math.huge, hi= -math.huge,
                   mu=0, m2=0, sd=0,
                   goal= (s or ""):find"-$" and 0 or 1}) end

function Data:new(names) return new(Data, {rows={}, cols=nil}) end

function Cols:new(names,    col) 
  self = new(Cols,{names=names, all={}, x={}, y={}})
  for i,s in pairs(names) do 
    col = push(self.all, (s:find"^[A-Z]" and Num or Sym):new(s,i))
    if not s:find"X$" then
       push(s:find"[!+-]$" and self.y or self.x, col) end end
  return self end

-----------------------------------------------------------------------------------------
function Sym:add(x) if x ~="?" then self.n = self.n + 1 end; return x end

function Num:add(x,    d)
  if x ~= "?" then
    self.n  = self.n + 1
    d    = x - self.mu
    self.mu = self.mu + d / self.n
    self.m2 = self.m2 + d * (x - self.mu)
    self.sd = self.n < 2 and 0 or (self.m2/(self.n - 1))^.5
    self.hi = math.max(self.hi, x)
    self.lo = math.min(self.lo, x) end end

function Data:add(row)
  if   self.cols 
  then push(self.rows, row)
       for _,col in pairs(self.cols.all) do col:add(row[col.at]) end 
  else self.cols = Cols:new(row) 
       end end

function Data:adds(src)
  if   type(src)=="string" 
  then for   row in csv(src)   do self:add(row) end
  else for _,row in pairs(src) do self:add(row) end end
  return self end

-----------------------------------------------------------------------------------------
function Num:norm(x)
  return x=="?" and x or (x - self.lo) / (self.hi - self.lo + 1E-32) end

function Sym:dist(x,y) return x=="?" and y=="?" and 1 or (x==y and 0 or 1) end

function Num:dist(x,y)
  if x=="?" and y=="?" then return 1 end
  x,y = self:norm(x), self:norm(y)
  x = x ~= "?" and x or (y<0.5 and 1 or 0)
  y = y ~= "?" and y or (x<0.5 and 1 or 0)
  return math.abs(x - y) end

function Data:xdist(row1,row2,  X)
  X= function(col) return math.abs(col:dist(row1[col.at], row2[col.at]) ^ the.p) end
  return  (sum(self.cols.x, X) / #self.cols.x) ^ (1/the.p) end

function Data:ydist(row,   Y)
  Y= function(col) return math.abs(col:norm(row[col.at]) - col.goal) ^ the.p end
  return  (sum(self.cols.y, Y) / #self.cols.y) ^ (1/the.p) end


function Data:some(k,  rows,      t,out,r1,r2)
  rows = rows or self.rows
  out = {any(rows)}
  for _ = 2,k do
    t={}
    for _ = 1,math.min(the.samples, #rows) do
      r1 = any(rows)
      r2 = min(out, function(ru) return self:xdist(r1,ru) end)  -- who ru closest 2?
      t[r1]= self:xdist(r1,r2)^2 end -- how close are you
    push(out, prefer(t)) end -- stochastically pick one item 
  return out end

-----------------------------------------------------------------------------------------
local eg={}

function eg.seed(x) 
  the.seed=coerce(x); math.randomseed(the.seed) end

function eg.csv(f) 
  for row in csv(f or the.data) do print(cat(row)) end end

function eg.xdata(file,    data,row1,rows) 
  data = Data:new():adds(file or the.data)
  row1=data.rows[1]
  rows = keysort(data.rows, function(row2) return data:xdist(row1,row2) end)
  for k,row in pairs(rows) do
    if k==1 or k % 60 == 0 then print(k, cat(row), data:xdist(row,row1)) end end end

function eg.ydata(file,    data,Y) 
  data = Data:new():adds(file or the.data)
  Y = function(row) return data:ydist(row) end
  for k,row in pairs(keysort(data.rows,Y)) do
    if k==1 or k % 60 == 0 then print(k, cat(row), Y(row)) end end end

function eg.some(file,    data,Y,b4,now)
  data = Data:new():adds(file or the.data)
  Y = function(row) return data:ydist(row) end
  b4 = adds(sort(map(data.rows, Y)))
  print("asIs",cat{n=b4.n, mu=b4.mu, sd=b4.sd})
  now=Num:new()
  for i=1,20 do
    shuffle(data.rows)
    now:add(Y(keysort(data:some(20),Y)[1])) end
  print("now",cat{n=now.n, mu=now.mu,sd=now.sd}) end

-----------------------------------------------------------------------------------------
math.randomseed(the.seed)
for k,v in pairs(arg) do
  if eg[v:sub(3)] then eg[v:sub(3)](arg[k+1]) end end 

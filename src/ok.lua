local help=[[
ok.lua : optimization via kmean++ style clustering
(c) 2024 Tim Menzies <timm@ieee.org>  MIT license]]

local the = {seed= 1234567891,
             p=2, samples=32,
             data= "../../moot/optimize/misc/auto93.csv"}

local Sym,Num,Cols,Data = {},{},{},{}
-------------------------------------------------------------------------------
-- ## Lib
local adds,any,cat,coerce,csv,fmt,gt,keysort,lt
local map,maps,min,new,push,prefer,shuffle,sort,sum

-- ### List

-- `push(list,atom) --> atom`<br>Push `x` onto `t`, returning `x`.
function push(t,x) 
  t[1+#t]=x; return x end

-- ### Sort

-- `lt|gt(str) --> function`<br>Return functions that can sort a list via a slot `x`.
function lt(x) return function(a,b) return a[x] < b[x] end end
function gt(x) return function(a,b) return a[x] > b[x] end end

-- `sort(list,funtion) --> list`<br>Return `t`, sorted in place via `F`.
function sort(t,F) table.sort(t,F); return t end

-- `keysort(list,funtion) --> list`<br>Return a new list, items sorted by `function`.
function keysort(t,F,     DECORATE,UNDECORATE)
  DECORATE   = function(x) return {F(x),x} end
  UNDECORATE = function(x) return x[2] end
  return map(sort(map(t,DECORATE),lt(1)), UNDECORATE) end

-- `shuffle(list) --> list`<br>Shuffle in place items in `t`.
function shuffle(t,    j) 
  for i = #t,2,-1 do j=math.random(i); t[i],t[j] = t[j],t[i] end; return t end

-- ### Map

-- `sum(list,function) --> num`<br>Sum items in `t`, filtered via `F`.
function sum(t,F,    n) n=0;  for _,v in pairs(t) do n = n + F(  v) end; return n end

-- `map|maps(list,function) --> list`<br>Filter `t` throught `F`.
function map(t,F,    u) u={}; for _,v in pairs(t) do u[1+#u]=F(  v) end; return u end
function maps(t,F,   u) u={}; for k,v in pairs(t) do u[1+#u]=F(k,v) end; return u end

-- `min(list[x],function) --> x`<br>Used `F` to find least item in `t`.
function min(t,F,    lo,x,tmp) 
  lo=math.huge
  for k,v in pairs(t) do
    tmp = F(v)
    if tmp < lo then lo,x = tmp,v end end
  return x end

-- `adds(lst, ?it=Num())`<br>call `it:add` for all `x` in `lst`.
-- If `lst` starts with a number, then name `it` a Num.
function adds(t,  it)
  it = it or (type(t[1])=="number" and Num or Sym):new()
  for _,x in pairs(t) do it:add(x) end
  return it end

-- ### String to Things

-- `coerce(str) --> function`<br>Coerce a string to an int,float, or trimmed string.
function coerce(s) 
  return math.tointeger(s) or tonumber(s) or s:match"^%s*(.-)%s*$" end

-- `csv(str) --> function`<br>Return a iterator that returns rows from a csv file.
function csv(file,     F,src)
  F= function(s,t) for s1 in s:gmatch"([^,]+)" do push(t,coerce(s1)) end; return t end
  src= io.input(file)
  return function(s)
    s = io.read()
    if s then return F(s,{}) else io.close(src) end end end 

-- ### Thing to String

-- Short cut to `string.format`.
fmt = string.format

-- `cat(anything) --> str`<br>Convert any nested structure to a string.
function cat(t,  F) 
  if type(t) == "number" then return fmt(t//1==t and "%s" or "%.3g",t) end
  if type(t) ~= "table"  then return tostring(t) end 
  F = function(k,v) return fmt(":%s %s",k,cat(v)) end
  return "{" .. table.concat( #t>0 and map(t,cat) or sort(maps(t,F))," ") .. "}" end

-- ### Select

-- `any(t) --> x`<br>Return any item in `t`.
function any(t) 
  return t[math.random(#t)] end

-- `prefer(dict[x,num]) --> x`<br>Weighted select of `x`, biased by `num`s.
function prefer(t,    all,r,u,x,n,anything)
  all,u=0,{}; for x,n in pairs(t) do u[1+#u]= {x,n}; all=all+n end
  r = math.random()
  for _,xn in pairs(sort(u,gt(2))) do
    x,n = xn[1],xn[2]
    anything = anything or x
    r = r - n/all
    if r <= 0 then return x end end 
  return anything end

-- ## Stats

-- `cliffs(list[num], list[num], ?delta=0.195) --> bool`   
-- Are `xs,ys` small effect same?
function cliffs(xs,ys,  delta,      lt,gt,n)
  lt,gt,n,delta = 0,0,0,delta or 0.197
  for _,x in pairs(xs) do
      for _,y in pairs(ys) do
        n = n + 1
        if y > x then gt = gt + 1 end
        if y < x then lt = lt + 1 end end end
  return math.abs(gt - lt)/n <= delta end -- 0.195 
      
-- `boot(list[num], list[num], ?int=512, ?int=0.05) --> bool`   
-- Are `y0,z0` insignificant;y different?
-- Taken from non-parametric significance test From Introduction to Bootstrap,
-- Efron and Tibshirani, 1993, chapter 20. https://doi.org/10.1201/9780429246593
-- Checks how rare are  the observed differences between samples of this data.
-- If not rare, then these sets are the same.
function boot(y0,z0,  straps,conf,     x,y,z,yhat,zhat,n,N)
  z,y,x = adds(z0), adds(y0), adds(y0, adds(z0))
  yhat  = l.map(y0, function(y1) return y1 - y.mu + x.mu end)
  zhat  = l.map(z0, function(z1) return z1 - z.mu + x.mu end)
  n     = 0 
  for _ = 1,(straps or 512)  do
    if adds(l.many(yhat)):delta(adds(l.many(zhat))) > y:delta(z)  then n = n + 1 end end
  return n / (straps or 512) >= (conf or 0.05)  end

-- `same[
function same(x,y,  delta,straps,conf)
  return cliffs(x,y,delta) and boot(x,y,straps,conf) end

-- ### Polymorphism

-- `new(t,t) --> t`<br>Tells an instance `t` to look for methods in `meta`.
function new(meta, t) 
  meta.__index = meta
  meta.__tostring = cat
  return setmetatable(t,meta) end

-----------------------------------------------------------------------------------------
-- ## Structs

-- `Sym:new(str,int) --> Sym`<br>Incrementally summarize stream of atoms.
function Sym:new(s,i) 
  return new(Sym,{at=i, txt=s, n=0, has={}, mode=nil, most=0}) end

-- `Num:new(str,int) --> Num`<br>Incrementally summarize stream of atoms.
function Num:new(s,i) 
  return new(Num, {at=i, txt=s, n=0, lo=math.huge, hi= -math.huge,
                   mu=0, m2=0, sd=0,
                   goal= (s or ""):find"-$" and 0 or 1}) end

-- `Data:new(list[str]) --> Data`<br>Store `rows`, summarized into `col`umns.
function Data:new(names) 
  return new(Data, {rows={}, cols=nil}) end

-- `Cols:new(list[str]) --> Cols`<br>Factory. Builds Nums and Syms from list of names.  
-- Upper case names are Nums. Anything ending the "X" gets ignored. Dependent columns
-- end with "!,+,-" for klass, maximize, minimize goals.
function Cols:new(names,    col) 
  self = new(Cols,{names=names, all={}, x={}, y={}, klass=nil})
  for i,s in pairs(names) do 
    col = push(self.all, (s:find"^[A-Z]" and Num or Sym):new(s,i))  
    if not s:find"X$" then                                         
       push(s:find"[!+-]$" and self.y or self.x, col)             
       if s:find"!" then self.klass = col end end end
  return self end

-----------------------------------------------------------------------------------------
-- ## Updating Structs

-- `Sym:add(atom) --> nil`<br>Update a Sym with `x`.
function Sym:add(x) 
  if x ~="?" then 
     self.n = self.n + 1 end
     self.has[x] = 1 + (self.has[x] or 0)
     if self.has[x] > self.most then 
        self.most,self.mode = self.has[x],x end end

-- `Num:add(num) --> nil`<br>Update a Num with `x`.
function Num:add(x,    d)
  if x ~= "?" then
    self.n  = self.n + 1
    d    = x - self.mu
    self.mu = self.mu + d / self.n
    self.m2 = self.m2 + d * (x - self.mu)
    self.sd = self.n < 2 and 0 or (self.m2/(self.n - 1))^.5
    self.hi = math.max(self.hi, x)
    self.lo = math.min(self.lo, x) end end

-- `Data:add(row) --> nil`<br>Add one row to a Data. If this row1, initialize `Cols`.
function Data:add(row)
  if   self.cols 
  then push(self.rows, row)
       for _,col in pairs(self.cols.all) do col:add(row[col.at]) end 
  else self.cols = Cols:new(row) 
       end end

-- `Data:adds(string | rows) --> Data`<br>Load a file or some rows into a Data.
function Data:adds(src)
  if   type(src)=="string" 
  then for   row in csv(src)   do self:add(row) end
  else for _,row in pairs(src) do self:add(row) end end
  return self end

-----------------------------------------------------------------------------------------
-- ## Distance Stuff

-- `norm(num) --> 0..1`<br>Return `x` normalized 0..1 for min..max.
function Num:norm(x)
  return x=="?" and x or (x - self.lo) / (self.hi - self.lo + 1E-32) end

-- `dist(atom,atom) --> 0..1`<br>Return distance between two syms.
function Sym:dist(x,y) return x=="?" and y=="?" and 1 or (x==y and 0 or 1) end

-- `dist(num,num) --> 0..1`<br>Return distance between two nums.
function Num:dist(x,y)
  if x=="?" and y=="?" then return 1 end
  x,y = self:norm(x), self:norm(y)
  x = x ~= "?" and x or (y<0.5 and 1 or 0)
  y = y ~= "?" and y or (x<0.5 and 1 or 0)
  return math.abs(x - y) end

-- `xdist(row,row) --> 0..1`<br>Return x column distance between two rows.
function Data:xdist(row1,row2,  X)
  X= function(col) return math.abs(col:dist(row1[col.at], row2[col.at]) ^ the.p) end
  return  (sum(self.cols.x, X) / #self.cols.x) ^ (1/the.p) end

function Data:neighbors(r1, rows)
  return keysort(rows or self.rows, function(r2) return self:xdist(r1,r2) end) end

-- `ydist(row) --> 0..1`<br>Return distance `y` to best possible `y` values.
function Data:ydist(row,   Y)
  Y= function(col) return math.abs(col:norm(row[col.at]) - col.goal) ^ the.p end
  return  (sum(self.cols.y, Y) / #self.cols.y) ^ (1/the.p) end

-- `some(int, ?rows=self.rows) --> rows`<br>Find great rows, don't look at many y-labels.
function Data:some(k,  rows,      t,out,r1,r2)
  rows = rows or self.rows
  out = {any(rows)}
  for _ = 2,k do
    t={}
    for _ = 1,math.min(the.samples, #rows) do
      r1 = any(rows)
      r2 = min(out, function(ru) return self:xdist(r1,ru) end) -- who ru closest 2?
      t[r1]= self:xdist(r1,r2)^2 end -- how close are you
    push(out, prefer(t)) end -- stochastically pick one item 
  return out end

-- `groups(rows, ?rows=self.rows) --> rows`<br>Group `rows` to their nearest `center`.
function Data:bestRest(k,     Y,X,t,best,rest,tmp)
  shuffle(self.rows)
  Y= function(r) return self:ydist(r) end
  X= function(r1,r2) return self:xdist(r1,r2) end
  t= keysort(self:some(k), Y)
  print(#t)
  u = self:neighbors(t[1], t)
  d = X(u[1],u[2])
  best,rest = {},{}
  for _,row in pairs(self.rows) do
    push(X(row,u[1]) < d/2 and best or rest,row) end
  -- best,rest = {},{}
  -- print(t.id)
  -- for _,row in pairs(self.rows) do
  --   tmp = min(t, function(centroid) return self:xdist(row, centroid.at) end)
  --   print(tmp.id)
  --   push(tmp.id == t[1].id and best or rest, row) end  
  return best, rest 
  end

-----------------------------------------------------------------------------------------
-- ## Start-up actions

-- Place to store start-up actions.
local go={}

-- Run many tests.
function go.all(_,     __) 
  for _,x in pairs(sort{"csv", "some", "xdata", "ydata"}) do
    math.randomseed(the.seed)
    go[x](__) end end

-- Reset random number seed.
function go.seed(x) 
  the.seed=coerce(x); math.randomseed(the.seed) end

-- Show some csv file rows.
function go.csv(file,   n) 
  n=0
  for row in csv(file or the.data) do 
    n=n+1
    if n> 15 then break end
    print(cat(row)) end end

-- Show some x col distance calculations.
function go.xdata(file,    data,row1,rows) 
  data = Data:new():adds(file or the.data)
  row1 = data.rows[1]
  rows = keysort(data.rows, function(row2) return data:xdist(row1,row2) end)
  for k,row in pairs(rows) do
    if k==1 or k % 60 == 0 then print(k, cat(row), data:xdist(row,row1)) end end end

-- Show some y col distance calculations.
function go.ydata(file,    data,Y) 
  data = Data:new():adds(file or the.data)
  Y    = function(row) return data:ydist(row) end
  for k,row in pairs(keysort(data.rows,Y)) do
    if k==1 or k % 60 == 0 then print(k, cat(row), Y(row)) end end end

-- From many examples, find a good one after looking at a few labels.
function go.some(file,    data,Y,b4,now)
  data = Data:new():adds(file or the.data)
  Y    = function(row) return data:ydist(row) end
  b4   = adds(sort(map(data.rows, Y)))
  print("asIs",cat{n=b4.n, mu=b4.mu, sd=b4.sd})
  now=Num:new()
  for i=1,20 do
    shuffle(data.rows)
    now:add(Y(keysort(data:some(20),Y)[1])) end
  print("now",cat{n=now.n, mu=now.mu,sd=now.sd}) end

-- sample best and rest
function go.br(file, data ,Y)
  data = Data:new():adds(file or the.data)
  Y= function(r) return data:ydist(r) end
  best,rest=data:bestRest(10) 
  print("best", adds(map(best,Y)))
  print("rest", adds(map(rest,Y)))
  end

-----------------------------------------------------------------------------------------
-- ## Start-up Actions

-- Run all `go[X](y)` for every `--X y` on the command line.
math.randomseed(the.seed)
for k,v in pairs(arg) do
  if go[v:sub(3)] then go[v:sub(3)](arg[k+1]) end end 

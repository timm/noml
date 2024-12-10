local l=require"ezlib"
local coerce,new,push,sort,map,o = l.coerce, l.new,l.push,l.sort,l.map,l.o
local items,sum,keysort = l.items, l.sum, l.keysort
local abs,log,huge = math.abs, math.log, math.huge
local pi, exp, max,min      = math.pi,math.exp, math.max, math.min

local the = {k=1, m=2, p=2, samples=32}
local Sym,Num,Cols,Data,Some = {},{},{},{},{}
local ez={Sym=Sym, Num=Num, Data=Data, Some=Some,
          the=the}

-----------------------------------------------------------------------------------------
function Sym:new(s,at) 
  return new(Sym, {txt=s or "", at=at or 0,n=0, 
                   has={}, mode=nil, most=0}) end

function Num:new(s,at) 
  return new(Num, {txt=s or "", at=at or 0, n=0, 
                   mu=0, m2=0, sd=0, hi= -huge, lo=huge,
                   goal = (s or ""):find"-$" and 0 or 1}) end

function Cols:new(names)
  return new(Cols,{names={},all={},x={},y={}}):adds(names) end

function Data:new( src)
  if type(src)=="table" then return Data:new(items(src)) end
  return new(Data,{rows={}, cols=Cols:new(src())}):adds(src or items{})  end

function Data.clone(i,src)
   return Data:new(items{i.cols.names}):adds(src or items{}) end

-----------------------------------------------------------------------------------------
function Cols.adds(i,names,   col)
  i.names = names
  for at,s in pairs(names) do
    col = push(i.all, (s:find"^[A-Z]" and Num or Sym):new(s,at))
    if not s:find"X$" then
      push(s:find"[!+-]$" and i.y or i.x, col) end end
  return i end

function Data.add(i,row) 
  push(i.rows,row)
  for _,c in pairs(i.cols.all) do c:add(row[c.at]) end
  return row end

function Data.adds(i,   src)
  for row in src do i:add(row) end 
  return i end

function Sym.add(i,x)
  if x ~= "?" then
    i.n  = i.n + 1
    i.has[x] = 1 + (i.has[x] or 0)
    if i.has[x] > i.most then i.most,i.mode = i.has[x], x end end end

function Num.add(i,x,     d)
  if x ~= "?" then
    i.n  = i.n + 1
    d    = x - i.mu
    i.mu = i.mu + d / i.n
    i.m2 = i.m2 + d * (x - i.mu)
    i.sd = i.n < 2 and 0 or (i.m2/(i.n - 1))^.5
    i.hi = max(i.hi, x)
    i.lo = min(i.lo, x) end end

function ez.adds(t,  i)
  i = i or (type(t[1])=="number" and Num or Sym):new()
  for _,x in pairs(t) do i:add(x) end
  return i end

-----------------------------------------------------------------------------------------
function Num.norm(i,x) return x=="?" and x or (x - i.lo)/(i.hi - i.lo + 1/1E32) end
function Sym.norm(i,x) return x end

function Num.delta(i,j)
  return abs(i.mu - j.mu) / ((1E-32 + i.sd^2/i.n + j.sd^2/j.n)^.5) end

function Num.cohen(i,j,   d,      sd)
  sd = (((i.n-1) * i.sd^2 + (j.n-1) * j.sd^2) / (i.n+j.n-2))^0.5
  return abs(i.mu - j.mu) <= (d or 0.35) * sd end

-----------------------------------------------------------------------------------------
function Num.dist(i,a,b)
  if a=="?" and b=="?" then return 1 end
  a,b = i:norm(a), i:norm(b)
  a = a ~= "?" and a or (b<0.5 and 1 or 0)
  b = b ~= "?" and b or (a<0.5 and 1 or 0)
  return abs(a-b) end

function Sym.dist(i,a,b) 
  if a=="?" and b=="?" then return 1 end
  return a==b and 0 or 1 end

function Data.xdist(i,row1,row2,     DIST)
  DIST = function(c) return c:dist(row1[c.at],row2[c.at])^the.p end
  return (sum(i.cols.x, DIST) / #i.cols.x) ^ (1/the.p) end

function Data.ydist(i,row,     DIST)
  DIST = function(c) return abs(c:norm(row[c.at]) - c.goal)^the.p end
  return (sum(i.cols.y, DIST) / #i.cols.y) ^ (1/the.p) end

function Data.neighbors(i,row1,  rows)
  return keysort(rows or i.rows, function(row2)  return i.xdist(row1,row2) end) end

function Data.around(i,k,  rows,      t,u,r1,r2)
  rows = rows or i.rows
  u = {l.any(rows)}
  for _ = 2,k do
    t={}
    for _ = 1,the.samples do
      r1 = l.any(rows)
      r2 = l.min(u, function(ru) return i:xdist(r1,ru) end) -- who ru closest 2?
      t[r1]= i:xdist(r1,r2)^2 end -- how close are you
    push(u, l.prefer(t)) end -- stochastically pick one item 
  return u end

function Data.arounds(i,budget,k,  rows,        Y,FUN,ks,tmp)
  rows = rows or l.shuffle(i.rows)
  Y    = function(row) return i:ydist(row) end
  FUN  = function(row) return {on=row, y=Y(row), has={}} end
  if #rows >= k and budget >= k then
    ks  = i:around(k, rows)
    tmp = map(ks,FUN)
    for j,row in pairs(rows) do
      if j > 1024 then break end
      local D = function(z) return i:xdist(row, z.on) end
      push(l.min(tmp, D).has, row)
    end
    return i:arounds(budget - k, k, sort(tmp, l.lt"y")[1].rows)
  else
    return keysort(i:around(k,rows),Y) end end

-----------------------------------------------------------------------------------------
function Sym.like(i,x,prior)
  return x=="?" and 0 or ((i.has[x] or 0) + the.m*prior) / (i.n + the.m) end

function Num.like(i,x,_ ,      v,tmp)
  if x=="?" then return 0 end
  v = i.sd^2 + 1/1E32
  tmp = exp(-1*(x - i.mu)^2/(2*v)) / (2*pi*v) ^ 0.5
  return max(0,min(1, tmp + 1/1E32)) end

function Data.loglike(i,row, nall, nh,          prior,F,L)
  prior = (#i.rows + the.k) / (nall + the.k*nh)
  F     = function(col) return L(col:like(row[col.at], prior)) end
  L     = function(n) return n>0 and log(n) or 0 end
  return L(prior) + l.sum(i.cols.x, F) end

-----------------------------------------------------------------------------------------
function Some:new(txt)
  return new(Some, {txt=txt or "", all={}, x=Num:new()}) end

function Some.add(i,x)
  i.x:add( push(i.all,x) ) end

function Some.same(i,j)
  return l.same(i.all, j.all, ez.adds) end

function Some.merge(i,j,  eps,      k)
  if abs(i.x.mu - j.x.mu) < (eps or 0.01) or i:same(j) then
    k = Some:new(i.txt)
    for _,t in pairs{i.all, j.all} do
      for _,x in pairs(t) do k:add(x) end end  end
  return k end 

function Some.merges(somes,eps,     pos,t,merged)
  pos={}
  for _,some in pairs(somes) do
    if t 
    then merged = some:merge(t[#t],eps)
         if merged then t[#t] = merged else push(t,some) end
    else t={some} end
    pos[some] = #t end
  for k,some in pairs(somes) do 
     some._meta = t[pos[some]] 
     some._meta.rank  = string.format("%c",96+pos[some]) end
  return somes end

-----------------------------------------------------------------------------------------
return ez

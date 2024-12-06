local l=require"ezlib"
local coerce,new,push,sort,map,o,csv = l.coerce, l.new,l.push,l.sort,l.map,l.o,l.csv
local sum= l.sum

local the= {p=2,samples=128}
-----------------------------------------------------------------------------------------
local Sym,Num,Cols,Data = {},{},{},{}

function Sym:new(s,at) 
  return new(Sym, {txt=s or "", at=at or 0,n=0, 
                   has={}, mode=nil, most=0}) end

function Num:new(s,at) 
  return new(Num, {txt=s or "", at=at or 0, n=0, 
                   mu=0, m2=0, sd=0, hi= -math.huge, lo=math.huge,
                   goal = (s or ""):find"-$" and 0 or 1}) end

function Cols:new(names)
  return new(Cols,{names={},all={},x={},y={}}):adds(names) end

function Data:new( src)
  return new(Data,{rows={}, cols=Cols:new(src())}):adds(src or items{})  end

function Data.clone(i,src)
   return Data:new(items{i.cols.names}):adds(src or items{}) end

-----------------------------------------------------------------------------------------
function Cols.adds(i,names,   col)
  i.names = names
  for at,s in pairs(names) do
    col = push(i.all, (s:find"^[A-Z]" and Num or Sym):new(s,at))
    push(s:find"[!+-]$" and i.y or i.x, col) end
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
    i.hi = math.max(i.hi, x)
    i.lo = math.min(i.lo, x) end end

local function adds(t,  i)
  i = i or (type(t[1])=="number" and Num or Sym):new()
  for _,x in pairs(t) do i:add(x) end
  return i end

-----------------------------------------------------------------------------------------
function Num.norm(i,x) return x=="?" and x or (x - i.lo)/(i.hi - i.lo + 1/1E32) end
function Sym.norm(i,x) return x end

function Num.dist(i,a,b)
  if a=="?" and b=="?" then return 1 end
  a,b = i:norm(a), i:norm(b)
  a = a ~= "?" and a or (b<0.5 and 1 or 0)
  b = b ~= "?" and b or (a<0.5 and 1 or 0)
  return math.abs(a-b) end

function Sym.dist(i,a,b) 
  if a=="?" and b=="?" then return 1 end
  return a==b and 0 or 1 end

function Data.xdist(i,row1,row2,     DIST)
  DIST = function(c) return c:dist(row1[c.at],row2[c.at])^the.p end
  return (sum(i.cols.x,DIST) / #i.cols.x)^1/the.p end

function Data.ydist(i,row,     DIST)
  DIST = function(c) return math.abs(c:norm(row[c.at]) - c.goal)^the.p end
  return (sum(i.cols.y,DIST) / #i.cols.y)^1/the.p end
 
 function Data.diverse(i,k,       t,tmp,row1,row2)
   t = {l.any(i.rows)}
   for _ = 2,k do
     tmp={}
     for _=1,the.samples do
       row1 = l.any(i.rows)
       row2 = l.min(t, function(row2) return i:xdist(row1,row2) end)
       tmp[row1] = i:xdist(row1,row2)^2 end
     push(t, l.sample(tmp)) end 
   return t end 

-----------------------------------------------------------------------------------------
return {Sym=Sym, Num=Num, Data=Data,adds=adds}

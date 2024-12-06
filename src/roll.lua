local l=require"rolllib"
local coerce,new,push,sort,map,o,csv = l.coerce, l.new,l.push,l.sort,l.map,l.o,l.csv

-----------------------------------------------------------------------------------------
local Sym,Num,Cols,Data = {},{},{},{}

function Sym:new(s,at) 
  return new(Sym, {txt=s or "", at=at or 0,n=0, 
                   has={}, mode=nil, most=0}) end

function Num:new(s,at) 
  return new(Num, {txt=s or "", at=at or 0, n=0, 
                   mu=0, m2=0, sd=0, hi= -math.huge, lo=math.huge,
                   goal = (s or ""):find"-$" and 0 or 1}) end

function Data:new(src)
  return new(Data,{rows={}, cols=Cols:new(src())}):adds(src)  end

function Cols:new(names)
  return new(Cols {names={},all={},x={},y={}}):adds(names) end

-----------------------------------------------------------------------------------------
function Cols.adds(i,names)
  i.names = names
  for at,s in pairs(names) do
    push(s:find"[!+-]$" and i.y or i.x, 
      push(i.all, (s:find"^[A-Z]" and Num or Sym):new(s,at))) end
  return i end

function Data.add(i,row) 
  push(i.rows,row)
  for _,c in pairs(i.cols.all) do c:add(row[c.at]) end
  return row end

function Data.adds(i,   src)
  for row in src do push(i.rows, i:add(row)) end 
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

local function addz(t,  i)
  i = i or ((type(t[1])=="number" and Num or Sym):new())
  for x in pairs(t) do i:add(x) end
  return i end

-----------------------------------------------------------------------------------------
local eg={}

function eg.one(s) print(coerce(s)) end

function eg.norm(_,    t,num)
  t={}; for _=1,50 do push(t, l.normal(10,1)) end
  num=Num:new()
  for _=1,50 do num:add(l.normal(10,1))  end
  print(addz(t).sd)
  print(num.sd) end

for k,v in pairs(arg) do
  if eg[v:sub(3)] then eg[v:sub(3)](arg[k+1] or "") end end 

return {Sym=Sym, Num=Num, Data=Data}

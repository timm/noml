local csv,push,coerce
local the = {data="../../moot/optimize/misc/auto93.csv"}

local names,x,y,nums,rows = {},{},{},{},{}

-------------------------------------------------------------------------------
local push,map,cat,any,sum,coerce,csv

function push(t,x) t[1+#t]=x; return x end

function any(t) return t[math.random(#t)] end

function sum(t,FUN,    n)
  n=0; for _,v in pairs(t) do n = n + FUN(v) end; return n end

function map(t,FUN,    u)
  u={}; for _,v in pairs(t) do u[1+#u]=FUN(  v) end; return u end

function cat(t) 
  if type(t) ~= "table" then return tostring(t) end 
  return "{" .. table.concat(map(t,cat),", ") .. "}" end

function coerce(s) 
  return math.tointeger(s) or tonumber(s) or s:match"^%s*(.-)%s*$" end

function csv(file,     FUN,src)
  FUN= function (s,t) for s1 in s:gmatch"([^,]+)" do push(t,coerce(s1)) end; return t end
  src= io.input(file)
  return function(s)
    s = io.read()
    if s then return FUN(s,{}) else io.close(src) end end end 

-----------------------------------------------------------------------------------------
local Sym,Num,Cols,Data

function Sym(s,i) return {isNum=false, at=i, txt=s, n=0} end

function Num(s,i) return {isNum=true,  at=i, txt=s, n=0, 
                          lo=math.huge,hi=-math.huge,
                          goal= (s or ""):find"-$" and 0 or 1} end

function Cols(names,   cols1) 
  cols1 = {names=names, all={}, x={}, y={}}
  for k,s in pairs(names) do 
    col = push(cols1.all, (s:find"^[A-Z]" and Num or Sym)(s,k))
    push(s:find"-$" and cols1.y or cols1.x, col) end 
  return cols1 end

function Data(names) return {rows={}, cols=Cols(names)} end

-----------------------------------------------------------------------------------------
local cell,row,rows

function cell(col1, x)
  if x ~= "?" then
    col1.n = col1.n + 1
    if col1.isNum then 
      if x < col1.lo then col1.lo = x end
      if x > col1.hi then col1.hi = x end end end 
  return x end

function row(data1,row1)
  if   data1 
  then push(data1.rows, row1)
       for _,col1 in pairs(data1.cols.all) do cell(col1,row1[col.at]) end 
  else data1 = Data(row1) end
  return data1 end

function rows(src,  data1,ADD)
  ADD = function(row1) data1 = row(data1, row1) end
  if   type(src)=="string" 
  then for   row1 in csv(src)   do ADD(row1) end
  else for _,row1 in pairs(src) do ADD(row1) end end
  return data1 end

-----------------------------------------------------------------------------------------
function norm(col1,x)
  return x=="?" and x or (x - col1.lo) / (col1.hi - col1.lo + 1/1E-32) end

function dist(col1, x,y)
  if x=="?" and y==">" then return 1 end
  x,y = norm(col1,x), norm(col1,y)
  x = x ~= "?" and x or (y<0.5 and 1 or 0)
  y = y ~= "?" and y or (x<0.5 and 1 or 0)
  return math.abs(x - y) end

function xdist(data1, row1,row2,   n,d)
  DIST=function(col1) return dist(col1, row1[col1.at], row2[col1.at])^the.p end
  return  ( sum(data1.cols.x, DIST) / #data1.cols.x ) ^ (1/the.p) end

function ydist(data1, row1,row2,   n,d)
  DIST=function(col1) return (norm(row1[col1.at]) - col1.goal) ^ the.p end
  return  ( sum(data1.cols.y, DIST) / #data1.cols.y ) ^ (1/the.p) end

-----------------------------------------------------------------------------------------
local eg={}
function eg.csv(f) 
  for row1 in csv(f or the.data) do print(cat(row1)) end end

function eg.data(file,    data) 
  data1 = rows(file or the.data)
  for k,row1 in pairs(data1.rows) do 
    if k==1 or k % 60 == 0 then print(k, ydist(data1,row1)) end end end

for k,v in pairs(arg) do
  math.randomseed(1234567891)
  if eg[v:sub(3)] then eg[v:sub(3)](arg[k+1]) end end 

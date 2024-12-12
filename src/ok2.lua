Big=1E32

local function Num(name) 
  return {lo= Big; hi= -Big, goal = name:find"-$" and 0 or 1} end

local function Data(names) 
  i= {x={},  -- indenpent columns
      y={},  -- dependent columns
      num={}, -- num[i] = {goal=0 or 1, lo=.., hi=...}
      rows={} -- set of rows
      }
  for k,s in pairs(names) do
    if s:find"^[A-Z]" then i.num[k] = Num(s) end
    if not s:find"X$" then
      if s:find"[!+-]$" then i.y[k] = i.num[k] else i.x[k] = k end end  end
  return i end

function addNum(num,x)
  if x=="?" then return x end
  x=x+0
  num.lo = math.min(x, num.lo)
  num.hi = math.max(x, num.hi) 
  return x end

function add(t,  data)
  data = data or DATA
  for k,num in pairs(data.num) do t[k] = addNum(num,t[k]) end
  push(data.rows, t) end

function ydist(t,   data)
  data = data or DATA
  for k,col in pairs(data.y) do
    n = n+1

function push(t,x) t[1+#t] =x; return x end

function csv(file,     CELLS, src)
  CELLS = function (s,t)
            for s1 in s:gmatch"([^,]+)" do t[1+#t]=s1:match"^%s*(.-)%s*$" end
            return t end
  src = io.input(file)
  return function(s)
    s = io.read()
    if s then return CELLS(s,{}) else io.close(src) end end end

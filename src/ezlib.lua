local l={}

-- ## Maths
function l.normal(mu,sd,    r)
  return (mu or 0) + (sd or 1) * math.sqrt(-2*math.log(math.random())) 
                               * math.cos(2*math.pi*math.random()) end

-- ## Lists
function l.push(t,x)  
  t[1+#t]=x; return x end

function l.items(t,    i)
  return function()
    i = (i or 0) + 1
    if i <= #t then return t[i] end end end

-- ## Sampling
function l.any(t) return t[math.random(#t)] end

function l.sample(t,    all,r,u,x,n)
  all,u=0,{}; for x,n in pairs(t) do u[1+#u]= {x,n}; all=all+n end
  r = math.random()
  for _,xn in pairs(l.sort(u,l.lt(2))) do
    x,n = xn[1],xn[2]
    r = r - n/all
    if r <= 0 then return x end end 
  return x end

-- ## Sorting
function l.lt(x) return function(a,b) return a[x] < b[x] end end

function l.sort(t,FUN) 
  table.sort(t,FUN); return t end

function l.keysort(t,FUN,     DECORATE,UNDECORATE)
  DECORATE   = function(x) return {FUN(x),x} end
  UNDECORATE = function(x) return x[2] end
  return l.map(l.sort(l.map(t,DECORATE),l.lt(1)), UNDECORATE) end

function l.min(t,FUN,      n,lo,out)
  lo = math.huge
  for _,x in pairs(t) do
    n=FUN(x)
    if n < lo then lo,out = n,x end end
  return out end

function l.shuffle(t,    j) --> list
  for i = #t, 2, -1 do j = math.random(i); t[i], t[j] = t[j], t[i] end
  return t end

-- ### Mapping
function l.map( t,FUN,...)
  local u={}; for _,v in pairs(t) do u[1+#u]=FUN(  v,...) end; return u end

function l.maps(t,FUN,...) 
  local u={}; for k,v in pairs(t) do u[1+#u]=FUN(k,v,...) end; return u end

function l.sum(t,FUN,...)
  local n=0; for _,v in pairs(t) do n=n+FUN(v,...) end; return n end 

-- ## String to things
function l.coerce(s) 
  return math.tointeger(s) or tonumber(s) or s:match"^%s*(.-)%s*$" end

function l.csv(file,     CELLS,src)
  CELLS = function (s,t)
            for s1 in s:gmatch"([^,]+)" do l.push(t,l.coerce(s1)) end; return t end
  src = io.input(file)
  return function(s)
    s = io.read()
    if s then return CELLS(s,{}) else io.close(src) end end end 

-- ## Thing to string
l.fmt = string.format

function l.o(x,     FUN,PUB) 
  if type(x) == "number" then return l.fmt("%g",x) end
  if type(x) ~= "table"  then return tostring(x) end
  PUB = function(k) return not l.o(k):find"^_" end
  FUN = function(k,v) if PUB(k) then return l.fmt(":%s %s",k, l.o(x[k])) end end
  return "{" .. table.concat(#x>0 and l.map(x,l.o) or l.sort(l.maps(x,FUN))," ").."}" end

-- ## Polymorphism
function l.new(meta, t) 
  meta.__index = meta
  meta.__tostring = meta.__tostring or l.o
  return setmetatable(t,meta) end

return l

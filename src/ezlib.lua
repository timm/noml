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

function l.keys(t,    u)
  u={}; for k,_ in pairs(t) do u[1+#u]=k end; return l.sort(u) end

-- ## Sampling
function l.any(t) return t[math.random(#t)] end

function l.many(t,  n) 
  n = n or #t
  u={}; for j=1,(n or #t) do u[1+#u] = l.any(t) end; return u end

function l.prefer(t,    all,r,u,x,n,anything)
  all,u=0,{}; for x,n in pairs(t) do u[1+#u]= {x,n}; all=all+n end
  r = math.random()
  for _,xn in pairs(l.sort(u,l.gt(2))) do
    x,n = xn[1],xn[2]
    anything = anything or x
    r = r - n/all
    if r <= 0 then return x end end 
  return anything end

function l.cliffs(xs,ys,  delta,      lt,gt,n)
  lt,gt,n,delta = 0,0,0,delta or 0.197
  for _,x in pairs(xs) do
      for _,y in pairs(ys) do
        n = n + 1
        if y > x then gt = gt + 1 end
        if y < x then lt = lt + 1 end end end
  return math.abs(gt - lt)/n <= delta end -- 0.195 
      
-- Taken from non-parametric significance test From Introduction to Bootstrap,
-- Efron and Tibshirani, 1993, chapter 20. https://doi.org/10.1201/9780429246593
-- Checks how rare are  the observed differences between samples of this data.
-- If not rare, then these sets are the same.
function l.boot(y0,z0,adds,  straps,conf,     x,y,z,yhat,zhat,n,N)
  z,y,x = adds(z0), adds(y0), adds(y0, adds(z0))
  yhat  = l.map(y0, function(y1) return y1 - y.mu + x.mu end)
  zhat  = l.map(z0, function(z1) return z1 - z.mu + x.mu end)
  n     = 0 
  for _ = 1,(straps or 512)  do
    if adds(l.many(yhat)):delta(adds(l.many(zhat))) > y:delta(z)  then n = n + 1 end end
  return n / (straps or 512) >= (conf or 0.05)  end

function l.same(x,y,adds,  delta,straps,conf)
  return l.cliffs(x,y,delta) and l.boot(x,y,adds,straps,conf) end

-- ## Sorting
function l.lt(x) return function(a,b) return a[x] < b[x] end end
function l.gt(x) return function(a,b) return a[x] > b[x] end end


function l.sort(t,FUN) 
  table.sort(t,FUN); return t end

function l.keysort(t,FUN,     DECORATE,UNDECORATE)
  DECORATE   = function(x) return {FUN(x),x} end
  UNDECORATE = function(x) return x[2] end
  return l.map(l.sort(l.map(t,DECORATE),l.lt(1)), UNDECORATE) end

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

function l.min(t,FUN,      n,lo,out)
  lo = math.huge
  for _,x in pairs(t) do
    n=FUN(x)
    if n < lo then lo,out = n,x end end
  return out end

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

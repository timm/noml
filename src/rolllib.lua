local l={}

function l.coerce(s) 
  return math.tointeger(s) or tonumber(s) or s:match"^%s*(.-)%s*$" end

function l.push(t,x)  
  t[1+#t]=x end

function l.sort(t,FUN) 
  table.sort(t,FUN); return t end

function l.map( t,FUN,...)
  local u={}; for _,v in pairs(t) do u[1+#u]=FUN(  v,...) end; return u end

function l.maps(t,FUN,...) 
  local u={}; for k,v in pairs(t) do u[1+#u]=FUN(k,v,...) end; return u end

function l.o(x,     FUN) --> str
  if type(x) == "number" then return string.format("%g",x) end
  if type(x) ~= "table"  then return tostring(x) end
  FUN = function(k,v) if not l.o(k):find"^_" then string.format(":%s %s",k,l.o(x[k])) end 
  return "{" .. table.concat(#x>0 and map(x,l.o) or sort(maps(x,FUN))," ").."}" end

function l.csv(file,     CELLS,src)
  CELLS= function (s,t) for s1 in s:gmatch"([^,]+)" do l.push(t,l.coerce(s1)) end; return t end
  src = io.input(file)
  return function(s)
    while true do
      s = io.read()
      if s then return CELLS(s,{}) else io.close(src) end end end end

function items(t,    i)
  return function()
    i = (i or 0) + 1
    if i <= #t then return t[i] end end end

function l.new(klass, t) 
  klass.__index = klass
  klass.__tostring = klass.__tostring or o
  return setmetatable(t,klass) end

return l



local l={}

function l.coerce(s) 
  return math.tointeger(s) or tonumber(s) or s:match"^%s*(.-)%s*$" end

function l.push(t,x)  
  t[1+#t]=x; return x end

function l.sort(t,FUN) 
  table.sort(t,FUN); return t end

function l.map( t,FUN,...)
  local u={}; for _,v in pairs(t) do u[1+#u]=FUN(  v,...) end; return u end

function l.maps(t,FUN,...) 
  local u={}; for k,v in pairs(t) do u[1+#u]=FUN(k,v,...) end; return u end

function l.o(x,     FUN) 
  if type(x) == "number" then return string.format("%g",x) end
  if type(x) ~= "table"  then return tostring(x) end
  FUN = function(k,v) if not l.o(k):find"^_" then return string.format(":%s %s",k,l.o(x[k])) end end
  return "{" .. table.concat(#x>0 and l.map(x,l.o) or l.sort(l.maps(x,FUN))," ").."}" end

function l.csv(file,     CELLS,src)
  CELLS = function (s,t)
            for s1 in s:gmatch"([^,]+)" do l.push(t,l.coerce(s1)) end; return t end
  src = io.input(file)
  return function(s)
    while true do
      s = io.read()
      if s then return CELLS(s,{}) else io.close(src) end end end end

function l.items(t,    i)
  return function()
    i = (i or 0) + 1
    if i <= #t then return t[i] end end end

function l.new(meta, t) 
  meta.__index = meta
  meta.__tostring = meta.__tostring or l.o
  return setmetatable(t,meta) end

return l

function push(t,x) t[1+#t]=x end

function csv(file, fun)
  function cells(s,    t)
    t={}; for s1 in s:gmatch"([^,]+)" do push(tonumber(s1) or s1) end; return t end
  src = io.input(file)
  n   = -1
  while true do
    s = io.read()
    if s then n=n+1; fun(n,cells(s)) else return io.close(src) end end end

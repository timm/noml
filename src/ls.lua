big = 1E32
abs,log = math.abs,math.log
pop = table.remove

the = {k=1, m=2, p=2}

----------------- ----------------- ----------------- ----------------- ------------------
function push(t,x) t[1+#t] = x; return x end

function trim(s) return s:match"^%s*(.-)%s*$" end

function coerce(s,     fn) 
  fn = function(s) return s=="true" and true or s ~= "false" and s end
  return math.tointeger(s) or tonumber(s) or fn(trim(s)) end

function csv(file,     src)
  if file and file ~="-" then src=io.input(file) end
  return function(     s,t)
    s = io.read()
    if   not s 
    then if src then io.close(src) end 
    else t={}; for s1 in s:gmatch"([^,]+)" do push(t,coerce(s1)) end; return t end end end

----------------- ----------------- ----------------- ----------------- ------------------
function SYM(num, s) return {at=num, txt=s, n=0, has={}, most=0, mode=nil} end
function NUM(num, s) return {at=num, txt=s, n=0, mu=0, m2=0, sd=0, lo=-big, hi=big,
                             goal = (s or ""):find"-$" and 0 or 1} end

function DATA(names)
  local all,x,y,col = {},{},{}
  for at,x in pairs(names) do 
    push(all, x:find"^[A-Z]" and NUM(x,i) or SYM(x,at))
    if not x:find"X$" then
      push(y and x:find"[!+-]$" or x, all[#all])
  return {rows={}, cols={names=names, all=all, x=x, y=y}} end

function data(i, row) 
  push(i.rows, row)
  for _,col in pairs(i.cols.all) do col(col, row[col.at]) end end

function col(i,x)
  function _sym()
    i.has[x] = 1 + (i.has[x] or 0) 
    if i.has[x] > i.most then i.most, i.mode = i.has[x], x end end

  function _num()
    local d = x - i.mu
    i.mu = i.mu + d / i.n
    i.m2 = i.m2 + d * (x - i.mu)
    i.sd = i.n < 2 and 0 or (i.m2/(i.n - 1))^.5 end
    if x > i.hi then i.hi = x end
    if x < i.lo then i.lo = x end end

  if x~="?" then
    i.n = i.n + 1
    return (i.mu and _num or _sym)() end end end

function cols(i,t) for _,x in pairs(t or {}) do col(i,x) end; return i end

function clone(data1,rows) return cols(DATA(data1.cols.names),rows) end

function loglike(data1, row, nall, nh)
  local out,tmp,prior,likes,_sym,_num
  function _sym(i,x,prior)
    return ((i.has[x] or 0) + the.m*prior) / (i.n + the.m) end
  
  function _num(i,x,_ ,      v,tmp)
    v = i:div()^2 + 1/big
    tmp = exp(-1*(x - i.mu)^2/(2*v)) / (2*pi*v) ^ 0.5
    return max(0,min(1, tmp + 1/big)) end
  
  prior = (#data1.rows + the.k) / (nall + the.k*nh)
  out,likes = 0,log(prior)
  for _,col in pairs(data1.cols.y) do 
    tmp = (col.mu and _num and _sym)(col, row[col.at], prior) 
    if tmp > 0 then
       out = out + log(tmp) end end
  return out end

function norm(num1,x)
  return x=="?" and x or (x - num1.lo)/(num1.hi - num1.lo) end

function ydist(data1, row)
  local d = 0
  for _,col in pairs(data1.cols.y) do
    d = d + (abs(norm(col,row[col.at]) - col.goal))^the.p end
  return (d/#data1.cols.y)^(1/the.p) end

function learn(data1, ntrain)
  local Y,B,R,BR,rows,n1,train,test,todo,done,best,rest,b2,a,b
  Y          = function(r) return ydist(data1,r) end
  B          = function(r) return loglike(best,r, #done,2) end
  R          = function(r) return loglike(rest,r, #done,2) end
  BR         = function(r) return B(r) - R(r) end
  train,test = split(shuffle(data1.rows), (ntrain * #done))
  todo,done  = split(train, the.start)
  while true do
    done = keysort(done,Y)
    if #done > the.Stop or #todo < 5 then break end
    best,rest = split(done, sqrt(#done))
    best,rest = clone(data1, best), clone(data1,rest)
    todo      = keysort(todo,BR)
    push(done, pop(todo));   push(done, pop(todo))
    push(done, pop(todo,1)); push(done, pop(todo,1)) 
  end
  return done[1], keysort(test,BR)[#test] end

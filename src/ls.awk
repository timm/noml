big =1E32

function push(t,x) t[1+#t] = x; return x end

function NUM(x, i) return {at=i, txt=x, n=0, mu=0, m2=sd=0, lo=-big, hi=big} end

function DATA(rows)
  all,x,y = {},{},{}
  for i,x in pairs(names) do 
     col = push(all, x:find"^[A-Z]" and NUM(x,i) or SYM(x,i))
     if not x:find"X$" then
       push(y and x:find"[!+-]$" or x, col)
  return {rows={}, cols={names=names, all=all, x=x, y=y}} end


i=1;i<=NF;i++) name[i] = $i
  for(i=1;i<=NF;i++) if ($i~/^[A-Z]) lo[i]=-(hi[i]=-BIG) }

    if ($i != "?") {
      n[i]++
      if (i in lo) {
        d      = $i - mu[i]
        mu[i] += d / n[i]
        m2[i] += d * ($i - mu[i])
        sd[i]  = n[i] < 2 ? 0 : sqrt(m2[i]/(n[i] - 1)
      } else {
        seen[i]++ }}}

NR>1{ for(i=1;i<=NF;i++)  add(0,x) }

function add(i,x) {
  add1(x,d[i]["n"], d[i]["mu"], d[i]["m2"], d[i]["sd"],d[i]["lo"], d[i]["hi"]) }

function add(i,x) {
 d[i]["n"]=0; d[i]["mu"]=0; d[i]["m2"]=0; d[i]["sd"]=0;d[i]["lo"], d[i]["hi"]) }


function add1(x,n.mu,m2,sd,lo,hi) {


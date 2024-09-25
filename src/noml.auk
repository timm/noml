# vim: set filetype=awk :  
# white space ^ == return

BEGIN {
  the,p = 2
  the.train = "../noot/..asd"
  the.most = 256
  the.seed = 1234567891
}

func add(i,x:atom,           f) { f="add2"i.is;  return @f(i,x)   }
func dist(i,x:atom,y:atom,   f) { f="dist4"i.is; return @f(i,x,y) }
func mid(i,                  f) { f="mid4"i.is;  return @f(i)     }

func DATA(i) {
  i.is="DATA"
  has(i,"rows")
  has(i,"cols") }

func clone(i:DATA,!j:DATA) {
   DATA(j)
   add(j,i.cols.names) }

func add2DATA(i:DATA, row:array,     r,c,v) {
  length(i.cols) ? _row(i, row, rand() % the.most) : COLS(i.cols, row)

func _row(i:DATA, row:array, r:int) {
  for(c in i.cols.all) {
    v = i.rows[r][c] = row[v]
    if (v != "?") add(i.cols.all[c], v)  }}
    
func COLS(i, names:list[str],     c,klass) {
  i.is="COLS"
  for(c in names) {
    i.names[c] = name = names[c]
    i[name ~ /[+-!]/ "y" : "x"][c]
    i.all[c].is = klass = name ~ /^[A-Z]/ ? "NUM" : "SYM"
    @klass(i.all[c], c, name) }}
  
func NUM(i, at:int, txt):str {
  i.is   = "NUM"
  i.at   = at 
  i.txt  = txt 
  i.hi   = -(i.lo = 1E32)
  i.mu   = i.m2 = i.sd = 0
  i.goal = txt ~ /-$/ ? 0 : 1 }

func mid(i:NUM)              { return i.mu }
func mid(i:SYM)              { return i.mode }
func mid(i:DATA, !out:array) { for(c in i.cols.all) out[c] = mid(i.cols.all[c]) }

func SYM(i, at:int, txt:str) {
  i.is   = "SYM"
  i.at   = at 
  i.n    = i.most = 0
  i.txt  = txt 
  i.mode = ""
  has(i,"has")  }

func add2SYM(i, x:atom) {
  if (x=="?") return
  i.n++
  i.has[x]++
  if (i.has[x] > i.most) {
    i.most = i.has[x]
    i.mode = x }}

func add2NUMi, x:num) {
  if (x=="?") return
  i.n++
  d     = i.mu - x
  i.mu += d/i.n
  i,m2 += d*(x - i.mu 
  i.sd  = i.n < 2 ? 0 : (i.m2/(i.n - 1))^.5
  if (x > i.hi) i.hi = x
  if (x < i.lo) i.lo = x }

func norm(i:NUM, x:number) { #-->  0..1
  return x=="?" ? x : (x - i.lo) / (i.hi - i.lo + 10^-32) }

func dist4SYM(i:SYM, a:atom, b:atom)  { #--> 0..1
  return  a==b=="?" ? 1 : a != b }

func dist4NUMS(i:NUM, a:number, b:number) { #--> number:
  if (a==b=="?") return 1
  a = norm(i,a)
  b = norm(i,b)
  a = a !="?" ? a : (b < .5 ? 1 : 0)
  b = b !="?" ? b : (a < .5 ? 1 : 0)
  return abs(a - b) }

func xDist(i:DATA, row1:row, row2:row) { #--> number:
  for(c in i.cols.x) {
    n += 1
    d += dist(i.cols.x[x], row1[c], row2[c])^the.p }
  return (d/n) * (1/the.p) }

func kmeans(i:data,k:int,n:int, samples: int,!datas:dict[str,DATA],
            r,m,rs,mids,mids) {
  for(r in i.rows) {
    if (length(mids) < k)  {
      m++
      for(x in i.cols.x) mids[m][x] = i.rows[r][x] }
    rs[r]
    if (length(rs) > sample) break }
  _kmansLoop(i,n, rs,mids,datas)
}

### how to return datas? move set p into a sub function. loop, don't call,_kmeans
func _kmeansLoop(i,loop,rs,mids0,datas,     r,k,mids1) {
  if (loop==0) return
  delete datas
  for(r in rs)  {
    k = closest2DATA(i, i.rows[r], mids)
    if (!(m in datas)) { datas[k].is="DATA"; clone(i, datas[k]) }
    add(datas[k],i.rows[r]) }
  for(k in datas) {
    new(mids1,k)
    mid(datas[k], mids1[k]) } 
  _kmeansLoop(i,loop-1,rs,mids1, datas) }
        
func closest2DATA(i,row,rows,     lo,d,out) {   
  lo=1E30
  for(r in rows) {
    d = xDist(i, row, rows[r])
    if (d < lo) {lo=d; out=r} }
  return out }

#---------------------
func new(i, ?k:atom) { 
  k = k ? k : length(i) + 1
  i[k][1] 
  del i[k][]
  return k }

#-------------------------
func o(a:array, pre:str) {
  if (typeof(a) != "array") return a
  for(i in a) 
    return pre "(" (typeof(a[i]) == "number" ? oArray(a) : oDict(a)) ")" }

func oArray(a:list,   sep,s,i) {for(i in a) {s = s sep         o(a[i]); sep=" "}; return s}
func oDict(d:dict,    sep,s,k) {for(k in d) {s = s sep ":"k " "o(d[k]); sep=" "}; return s}
   
func abs(x) { return x < 0 ? -x : x }

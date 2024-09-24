# vim: set filetype=awk :  
# white space ^ == return

func add(i,x:atom,    f) { f="add2"i.is; ^@f(i,x) }

func DATA(i) {
  i.is="DATA"
  has(i,"rows")
  has(i,"cols") }

func add2DATA(i:DATA, row:array,     r,c,v) {
  length(i.cols) ? _row(i, row, 1+length(i.rows)) : COLS(i.cols, row)

function _row(i:DATA, row:array, r:int) {
  for(c in i.cols.all) {
    v = i.rows[r][c] = row[v]
    if (v != "?") add(i.cols.all[c], v)  }}
    
func COLS(i, names:list[str],     c,klass) {
  i.is="COLS"
  for(c in names) {
    name = names[c]
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

@of("DISTANCE","between two symbols")
def dist(i:SYM, a:atom, b:atom): return 1 if a==b=="?" else a != b

@of("DISTANCE","between two numbers")
def dist(i:NUM, a:number, b:number) -> number:
  if a==b=="?": return 1
  a, b = i.norm(a), i.norm(b)
  a = a if a != "?" else (1 if b<.5 else 0)
  b = b if b != "?" else (1 if a<.5 else 0)
  return abs(a - b)

@of("DISTANCE","between two rows (x-value Minkowski)")
def xDist(i:DATA, row1:row, row2:row) -> number:
 
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
   


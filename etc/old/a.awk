#!/usr/bin/env gawk -f
# % NOML
# 

BEGIN { FS="," }
NR==1 { split($0,names,FS); DATA(data0,names) }

function add(i,x,    f) { f=i.is"add"; return @f(i,x) }

function DATA(i, names) {
  i["is"] = "DATA" 
  have(i,"rows cols x y")
  for(k in names) DATAinit(i,k,names[k]) }

function DATAinit(i,k,name) {
  i["cols"][k]["txt"] = name
  what = name  ~/^[A-Z]/ ? "NUM" : "SYM"
  @what(i["cols"][k],i,name) 
  if (name ~ /X$/) return 
  if (name ~ /[+-!]/) 
    i["y"][k] = name ~ /-$/ ? 0 : 1 
  else 
    i["x"][k] }
    
function NUM(i,at,txt) {
  i["at"]=at
  i["txt"]=txt 
  i["n"] = i["mu"] = i["m2"] =  0 
  i["lo"]=1E32; i["hi"] = -1E32 }

function SYM(i,at,txt) {
  i["at"]=at
  i["txt"]=txt 
  i["n"] = i["most"] = 0
  i["mode"] = ""
  has(i,"has") }

function array(i,k) { 
  if (k) {
    i[k][0]; delete i[j][0] 
  } else 
    return array(i, length(a)+1);
  return k }

function have(i,s,     a,k) {
 split(s,a," ")
 for(k in a) has(i,a[k]) }

function has(i, k, f)       { k=array(i,k); if (f) @f(i[k])     }
function haS(i, k, f, x)    { k=array(i,k); if (f) @f(i[k],x)   }
function hAS(i, k, f, x, y) { k=array(i,k); if (f) @f(i[k],x,y) }
# 

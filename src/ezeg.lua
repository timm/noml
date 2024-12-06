local l=require"ezlib"
local ez=require"ez"
local Data,Num = ez.Data,ez.Num
local o,csv,map = l.o,l.csv,l.map

local eg={}

function eg.one(s) print(l.coerce(s or "")) end

function eg.norm(_,    n)
  for _,r in pairs{10,20,40,80,160} do
    n = Num:new(); for _=1,r do n:add(l.normal(10,1))  end
    print(r,o{mu=n.mu, sd=n.sd}) end end

function eg.csv(_, it)
  it = csv("../../moot/optimize/misc/auto93.csv") 
  for r in it do print(o(r)) end end

function eg.data(_, it)
  it= Data:new(csv("../../moot/optimize/misc/auto93.csv")) 
  print(#it.rows,#it.cols.x,it.cols.x[1])
  end

function eg.ydist(_, it)
  it= Data:new(csv("../../moot/optimize/misc/auto93.csv")) 
  DIST = function(row) return it:ydist(row) end
  for k,row in pairs(l.keysort(it.rows,DIST)) do
    if k==1 or k % 60==0 then print(k,o(row), o(DIST(row))) end end end

function eg.xdist(_, it)
  it= Data:new(csv("../../moot/optimize/misc/auto93.csv")) 
  DIST = function(row) return it:xdist(row,it.rows[1]) end
  for k,row in pairs(l.keysort(it.rows,DIST)) do
    if k==1 or k % 60==0 then print(k,o(row), o(DIST(row))) end end end

function eg.sample(f, it,asis,tobe,Y,r)
  it= Data:new(csv(f or "../../moot/optimize/misc/auto93.csv")) 
  Y = function(row) return it:ydist(row) end
  asis= ez.adds(map(it.rows,Y))
  for _,r in pairs{6,12,24,48} do
    tobe=Num:new()
    for i = 1,20 do tobe:add(Y(l.keysort(it:diverse(r),Y)[1])) end 
    print(r,o{lo=asis.lo,mu={asis=asis.mu, tobe=tobe.mu},sd={asis=asis.sd, tobe=tobe.sd}}) end end

  
-----------------------------------------------------------------------------------------
local nothing =true
for k,v in pairs(arg) do
  math.randomseed(1234567891)
  if eg[v:sub(3)] then nothing=false; eg[v:sub(3)](arg[k+1]) end end 

if nothing then
  print("\nUsage:")
  for k,_ in pairs(eg) do print("\tlua ezeg.py --"..k) end end

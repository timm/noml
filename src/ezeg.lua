local l=require"ezlib"
local ez=require"ez"
local Data,Num = ez.Data,ez.Num
local o,csv,map = l.o,l.csv,l.map

local eg={}

function eg.one(s) print(l.coerce(s)) end

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

function eg.sample(_, it,num,Y)
  it= Data:new(csv("../../moot/optimize/misc/auto93.csv")) 
  Y = function(row) return it:ydist(row) end
  print( ez.adds(map(it.rows,Y)))
  for i = 1,20 do
     print(Y(l.keysort(it:diverse(12),Y)[1])) end end 
  
-----------------------------------------------------------------------------------------
local nothing =true
for k,v in pairs(arg) do
  math.randomseed(1234567891)
  if eg[v:sub(3)] then nothing=false; eg[v:sub(3)](arg[k+1] or "") end end 

if nothing then
  print("\nUsage:")
  for k,_ in pairs(eg) do print("\tlua ezeg.py --"..k) end end

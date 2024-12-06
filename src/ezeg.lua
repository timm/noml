local l=require"ezlib"
local ez=require"ez"
local Num=ez.Num
local o,csv = l.o,l.csv

local eg={}

function eg.one(s) print(l.coerce(s)) end

function eg.norm(_,    n)
  for _,r in pairs{10,20,40,80,160} do
    n = Num:new(); for _=1,r do n:add(l.normal(10,1))  end
    print(r,o{mu=n.mu, sd=n.sd}) end end

function eg.csv(_, it)
  it = csv("../../moot/optimize/misc/auto93.csv") 
  for r in it do print(o(r)) end end

--------------------------------------------------------
for k,v in pairs(arg) do
  math.randomseed(1)
  if eg[v:sub(3)] then eg[v:sub(3)](arg[k+1] or "") end end 

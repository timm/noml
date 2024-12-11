function Data:groups(centers, rows,     groups,group)
  rows = rows or self.rows
  groups = map(centers, function(c) return {at=c, has={}} end)
  for _,row in pairs(rows or self.rows) do
    group = min(groups, function(g) return self:xdist(row, g.at) end)
    push(group.has, row) end
  return groups end

function eg.groups(file,  data,Y,now)
  data = Data:new():adds(file or the.data)
  Y = function(row) return data:ydist(row) end
  for k,group in pairs(data:groups( data:some(20))) do
     now=Num:new()
     for _,row in pairs(group.has) do now:add(Y(row)) end 
     print(now.mu,now.n) end end


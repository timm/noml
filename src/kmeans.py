def slosh(data1, rows=None, stop=None, lvl=0, top=None, used=None):
  rows, stop, _, right, used = step(data1,rows,stop,top,True,used)
  return o(data  = DATA(data1.cols.names,rows), lvl=lvl, cut=right[0],
           right = None if lvl > stop else slosh(data1, right, stop, lvl+1, right[-1]))

def slashslosh(data1, rows=None, stop=None, lvl=0, top=None, used=None):
  rows, _, left, right, used = step(data1,rows)
  slash(data1, left,  2, 1, left[0],   used)
  slosh(data1, right, 2, 1, right[-1], used)
  return used
def kmeans(data1, k=10, loops=10, samples=512):
  def loop(n, centroids):
    datas = {}
    for row in rows:
      k = id(min(centroids, key=lambda centroid: xdist(data1,centroid,row)))
      datas[k] = datas.get(k,None) or DATA(data1.cols.names)
      data(datas[k], row)
    return datas.values() if n==0 else loop(n-1, [mid(d) for d in datas.values()])

  random.shuffle(data1.rows)
  rows = data1.rows[:samples]
  return loop(loops, rows[:k])

def diversity(data1,samples=512):
  n = the.Samples
  clone = lambda a: DATA(data1.cols.names,a)
  rows  = shuffle(data1.rows)[:samples]
  done  = []
  for k in [n,n]:
    datas = kmeans(clone(rows), k=k)
    done += [mid(d) for d in datas]
    data2 = clone(done) 
    rows  = sorted(datas, key=lambda d: ydist(data2, mid(d)))[0].rows
  return ydists(clone(done + shuffle(rows)[:n*2])).rows[0]



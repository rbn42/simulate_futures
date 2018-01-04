import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Qt5Agg')
import json
l=[]
for line in open('./trade.log'):
    if 'date' in line:
        obj=eval(line)
        l.append(obj['assets'])
plt.plot(l)
plt.show()

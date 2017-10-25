import numpy as np  
import matplotlib.pyplot as plt  
  
x=[0,1,2,3,4,5]  
y=[0,1,44,5,3,2]  
  
plt.figure()  
plt.plot(x,y)  
plt.xlabel("time(s)")  
plt.ylabel("value(m)")  
plt.title("A simple plot")  
plt.show()
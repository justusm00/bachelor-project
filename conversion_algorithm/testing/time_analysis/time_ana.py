# -*- coding: utf-8 -*-
# @Author: Your name
# @Date:   2023-02-24 16:03:22
# @Last Modified by:   Your name
# @Last Modified time: 2023-02-24 16:04:33
import numpy as np 
import matplotlib.pyplot as plt

mse=np.loadtxt("mse.txt")
x=np.linspace(0,len(mse),len(mse))

plt.plot(x,mse)
plt.show()
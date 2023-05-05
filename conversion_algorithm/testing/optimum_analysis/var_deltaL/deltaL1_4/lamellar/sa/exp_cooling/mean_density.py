# -*- coding: utf-8 -*-
# @Author: Your name
# @Date:   2022-12-09 16:16:32
# @Last Modified by:   Your name
# @Last Modified time: 2023-01-25 16:42:18
import h5py
import numpy as np
import matplotlib.pyplot as plt

#routine to plot mean density field at given x


boxlen=0 #length of box/conversion zones



#get density field
with h5py.File('coord_sample_ana.h5','r') as anafile:
    phi=np.array(anafile['density_field']).mean(axis=(3,4))
    delta_mc_phi=np.array(anafile['density_field'].attrs["DeltaMC"])
num_steps=len(phi) #number of MC sweeps
tmax=num_steps*delta_mc_phi
t=np.arange(0,tmax,delta_mc_phi)
phiA=phi[:,0]
phiB=phi[:,1]
plt.plot(t,phiA[:,idx])
plt.show()

# -*- coding: utf-8 -*-
# @Author: Your name
# @Date:   2023-03-07 17:13:45
# @Last Modified by:   Your name
# @Last Modified time: 2023-03-07 17:33:24
import numpy as np
import h5py 
import matplotlib.pyplot as plt

with h5py.File('coord_ana.h5','r') as anafile:
    phi=np.array(anafile['density_field'])
    delta_mc_phi=np.array(anafile['density_field'].attrs["DeltaMC"])
    MSD=np.array(anafile['MSD'])


with h5py.File('coord.h5', 'r') as f:
    ##number of beads per polymer
    N=int(f['parameter/reference_Nbeads'][()]) 
    ##number of polymers
    n_polym=int(f['parameter/n_polymers'][()]) 
    n_poly_type=int(f['parameter/n_poly_type'][()]) 
    ##box dimensions 
    lxyz=np.array(f['parameter/lxyz'])
    ##box discretization
    nxyz=np.array(f['parameter/nxyz'])

#bead density
rho=n_polym * N / (np.prod(lxyz))

# external field velocity in R_e/MC_step
vref=(lxyz[1]/nxyz[1])/10000

y=np.linspace(-lxyz[1]/2,lxyz[1]/2,1000)

def v_poiseuille(y,c):
    return 18*vref/rho * y**2 + c

plt.plot(y,v_poiseuille(y,0))
plt.show()




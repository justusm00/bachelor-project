# -*- coding: utf-8 -*-
# @Author: Justus Multhaup
# @Date:   2023-01-26 11:00:58
# @Last Modified by:   Your name
# @Last Modified time: 2023-02-09 13:59:12

## get density variance in cells where umbrella field is > 0
## need to run config_umbrella first
import h5py
import numpy as np

coordfile = 'coord_1.h5' ##needed only for parameters and umbrella field
anafile='coord_ana.h5' ##needed for density fields

f= h5py.File(coordfile, 'r') 
g= h5py.File(anafile, 'r') 

umbrella_field = np.array(f["umbrella_field"])
phi=np.array(g["density_field"])
N=np.array(f["parameter/reference_Nbeads"])
n_polym=np.array(f["parameter/n_polymers"])
nxyz=np.array(f["parameter/nxyz"])
lxyz=np.array(f["parameter/lxyz"])
n_types=np.array(f["parameter/n_types"])


phi_tot=np.sum(phi,axis=1)
phiA=phi[:,0,:,:,:]/phi_tot
phiB=phi[:,1,:,:,:]/phi_tot
phi_norm=np.stack((phiA,phiB),axis=1)
phi_var=np.var(phi_norm,axis=0)[umbrella_field>0]
print(phi_var.mean())


f.close()
g.close()
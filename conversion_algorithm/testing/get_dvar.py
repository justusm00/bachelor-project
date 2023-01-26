# -*- coding: utf-8 -*-
# @Author: Justus Multhaup
# @Date:   2023-01-26 11:00:58
# @Last Modified by:   Your name
# @Last Modified time: 2023-01-26 13:04:10

## get density variance in cells where umbrella field is > 0
## need to run config_umbrella first
import h5py
import numpy as np

coordfile = 'coord_sample_t50000.h5' ##needed only for parameters and umbrella field
anafile='coord_sample_ana.h5' ##needed for density fields

f= h5py.File(coordfile, 'r') 
g= h5py.File(anafile, 'r') 

umbrella_field = np.array(f["umbrella_field"])
density_field=np.array(g["density_field"])
N=np.array(f["parameter/reference_Nbeads"])
n_polym=np.array(f["parameter/n_polymers"])
nxyz=np.array(f["parameter/nxyz"])
lxyz=np.array(f["parameter/lxyz"])
scale=np.prod(nxyz)/(N*n_polym)
density_field=density_field * scale
n_types=np.array(f["parameter/n_types"])
num_umbrella_cells=int(len(umbrella_field[umbrella_field > 0]))
density_field_var=np.var(density_field,axis=0)[umbrella_field>0]

print(density_field_var.mean())


f.close()
g.close()
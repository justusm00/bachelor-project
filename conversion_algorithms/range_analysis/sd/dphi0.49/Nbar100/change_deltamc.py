# -*- coding: utf-8 -*-
# @Author: Your name
# @Date:   2023-05-23 20:03:16
# @Last Modified by:   Your name
# @Last Modified time: 2023-05-24 12:49:05
import h5py
import numpy as np
import sys


deltamc_pc=int(sys.argv[1])
coordfile=sys.argv[2]
##file that contain area51 and bead positions
f= h5py.File(coordfile, 'r+') 
e = "polyconversion/deltaMC" in f
if e:
    del f["polyconversion/deltaMC"]

dset_deltaMC = f.create_dataset("polyconversion/deltaMC", data=deltamc_pc)



f.close()
import h5py
f= h5py.File('coord_ana.h5', 'r+') 
g = h5py.File('coord.h5', 'r+') 
f["density_field"].attrs.modify("DeltaMC",15000)
g["polyconversion"].attrs.modify("DeltaMC",10)
g["polyconversion"].attrs.modify("deltaMC",10)
f.close()
g.close()

#!/opt/homebrew/Frameworks/Python.framework/Versions/3.10/bin/python3.10

#   Copyright (C) 2016-2021 Ludwig Schneider
#   Copyright (C) 2016-2017 Marcel Langenberg
#
# This file is part of SOMA.
#
# SOMA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SOMA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with SOMA.  If not, see <http://www.gnu.org/licenses/>.



## \file ConfGen.py Script to convert SOMA xml input files to hdf5 input files.
import sys
sys.path.append( "/Users/justusmulthaup/soma_mod/install/python-script" )
import numpy
import copy
import ctypes
import xml.etree.ElementTree as ET
import h5py
import argparse
import soma_type
try:
    import StringIO as stringio
except ImportError:
    import io as stringio
except ModuleNotFoundError:
    import io as stringio
## Matches the enum Bondtype of struct.h
bondDict = {}
bondDict["HARMONIC".upper()] = 0
bondDict["STIFF".upper()] = 1
bondDict["HARMONICVARIABLESCALE".upper()] = 2
NUMBER_SOMA_BOND_TYPES = 3

## Matches the enum Hamiltonian of soma_util.h
hamiltonDict = {}
hamiltonDict["SCMF0".upper()] = 0
hamiltonDict["SCMF1".upper()] = 1

## Matches the enum MobilityEnum in soma_util.h
MobilityDict = {}
MobilityDict["DEFAULT_MOBILITY"] = 0
MobilityDict["MULLER_SMITH_MOBILITY"] = 1
MobilityDict["TANH_MOBILITY"] = 2


## Class to Store for every Monomer name the corresponding type number and the corresponding half-bond identifier.
class Types:
    ## Constructor
    #
    ## @param equivalence_str String which describes equivalent particle types. It is not intended to add later equivalent types.
    def __init__(self,equivalence_str):
        self._internal_dict_exact = {}
        self._internal_dict_equiv = {}
        ## Number of stored half-bond types
        self.n_types_exact = 0
        ## Number of stored particle types
        self.n_types_equiv = 0
        self._lock = False

        assert type(equivalence_str) is str
        for line in equivalence_str.split("\n"):
            line = line.strip()
            if len(line) > 0 and line[0] != '#':
                split = []
                i=0
                while i < len(line):
                    if line[i] == Molecule.string_open:
                        close = line.find(Molecule.string_close,i+1)
                        assert close > 0
                        split.append( line[i:close] )
                        i = close
                    elif not line[i].isspace():
                        split.append(line[i])
                    i += 1

                for name in split:
                    self._set_equiv(split[0],name)
    ## Lock the instance to not allow addition of more types
    def lock_type(self):
        self._lock = True
    ## Unlock the instance to add more particle types.
    #
    # @warning Not recommended to use this functions unless you know what you do.
    # @return None
    def unlock_type(self):
        self._lock = False

    ## Update the dictionary with the given type name.
    ##
    ## @param name Name of the type.
    ## Only adds an unknown type, if instance is unlocked. Otherwise an AssertionError is raised.
    ## @private
    def _update(self,name):
        assert type(name) is str
        name = name.strip("' ")
        if self._lock:
            assert (name in self._internal_dict_exact.keys()), "Trying to add a type, but Types is locked. "+name

        if name not in self._internal_dict_exact.keys():
            self.n_types_exact += 1
            self.n_types_equiv += 1
            self._internal_dict_exact[name] = self.n_types_exact -1
            self._internal_dict_equiv[name] = self.n_types_equiv -1

    ## Returns the unique particle type id.
    ##
    ## Entries of the \a equivalence are ignored. Used for bond type lookups
    ## @param name type name
    ## @return half-bond type id
    def get_exact(self,name):
        self._update(name)
        name = name.strip("' ")
        return self._internal_dict_exact[name]

    ## Returns the particle type id.
    ##
    ## Equivalent types return the same id.
    ## Used for particle
    ## @param name Input for requested typy
    ## @return particle type id
    def get_equiv(self,name):
        self._update(name)
        name = name.strip("' ")
        return self._internal_dict_equiv[name]

    ## Set 2 names as equivalent particle types.
    def _set_equiv(self,name1,name2):
        name1 = name1.strip("' ")
        name2 = name2.strip("' ")
        if self.get_equiv(name1) != self.get_equiv(name2):
            if self.get_equiv(name1) > self.get_equiv(name2):
                tmp = name1
                name1 = name2
                name2 = tmp
            self.n_types_equiv -= 1
            for k in self._internal_dict_equiv.keys():
                if self._internal_dict_equiv[k] > self.get_equiv(name2):
                    self._internal_dict_equiv[k] -= 1
            self._internal_dict_equiv[name2] = self.get_equiv(name1)

    ## Generate a human readable string containing the type information
    def __str__(self):
        string = ""
        for k in self._internal_dict_equiv.keys():
            string += k+":\t"
            string += str(self._internal_dict_equiv[k])+"\t"
            string += str(self._internal_dict_exact[k])+"\n"
        return string

    ## Get the string name of an exact type
    def get_name(self,exact_id):
        for key in self._internal_dict_exact.keys():
            if self._internal_dict_exact[key] == exact_id:
                return key

## Describes a set of molecules with the same architecture.
class MoleculeSet:
    ## Construct a molecule set.
    ##
    ## @param inputstr Single line string containing the CurleySmiles description of the molecule.
    ## @param inter Interaction instance describing the known interactions
    def __init__(self,inputstr,inter):
        ## Original input string
        self.inputstr = str(inputstr)
        i = 0
        while not inputstr[i].isspace():
            i +=1

        split = []
        split.append(inputstr[:i].strip())
        split.append(inputstr[i:].strip())

        try:
            ## Number of molecules in this set.
            self.N = int(split[0])
        except ValueError:
            assert False,"The first part of a MoleculeSet string must be integer convertible."

        assert (not self.N < 0),"The number Molecules in a set has to be greater than 0."

        ## Molecule architecture description
        self.mol = Molecule(split[1],inter)

## Class to interpret and store a Molecule architecture.
class Molecule:
    ##Character to define a open curl
    curl_open = "{"
    ##Character to define a close curl
    curl_close = "}"
    ##Character to define a open branch
    branch_open = "("
    ##Character to define a close branch
    branch_close = ")"
    ##Character to define a open string
    string_open = "'"
    ##Character to define a close string
    string_close = "'"
    ##Character to define a tag list separator
    tag_close = "%"

    ##Constructor
    ##
    ## @param inputstr CurleySmiles string describing the molecule architecture.
    ## @param inter Interaction instance describing the known interactions.
    def __init__(self,inputstr,inter):
        inputstr = self.pumpup_str(inputstr)
        inputstr = self.remove_curls(inputstr)
        ## Input string without abbreviations and without Curls
        self.long_str = inputstr
        self.create_type_lists(self.long_str,inter.knownTypes)
        ## Number of sub units (monomers) of the molecule
        self.N = len(self.type_list_equiv)
        ## List containing all the bond information
        self.bond_list = self.get_bond_list(self.long_str,inter)

    ## Remove all abbreviations from the input string
    ##
    ## @param inputstr String with possible abbreviations
    ## @return string without any abbreviation
    def pumpup_str(self,inputstr):
        inputstr = str(inputstr).strip()
        pump_str = ""
        i = 0
        while i < len(inputstr):
            #branch close
            if inputstr[i] == self.branch_close:
                pump_str += self.branch_close
                i+=1
                if i >= len(inputstr) or inputstr[i] != self.curl_open:
                    pump_str += self.curl_open+"1"+self.curl_close
                elif i < len(inputstr):
                    close = inputstr.find(self.curl_close,i+1)
                    assert (close>=0),"Unclosed curls in inputstr."
                    pump_str += inputstr[i:close+1]
                    i = close+1
                continue
            if inputstr[i] == self.branch_open:
                pump_str += self.branch_open
                i += 1
                continue

            #string name monomer
            if inputstr[i]== self.string_open:
                close = inputstr.find(self.string_close,i+1)
                assert (close>=0),"Unclosed string in inputstr."
                pump_str += inputstr[i:close+1]
                i = close+1
            else:
                assert (inputstr[i].isalpha()),"Expected letter, but got "+str((inputstr[i],i))
                pump_str += self.string_open+inputstr[i]+self.string_close
                i+=1

            # tag list
            if i < len(inputstr) and inputstr[i].isdigit():
                 while i < len(inputstr) and (inputstr[i].isdigit() or inputstr[i] == self.tag_close):
                     pump_str += inputstr[i]
                     i+=1
            else:
                pump_str += "0"
            if pump_str[-1] != self.tag_close:
                pump_str += self.tag_close

            #curls
            if i < len(inputstr) and inputstr[i] == self.curl_open:
                close = inputstr.find(self.curl_close,i+1)
                assert (close>=0),"Unclosed curls in inputstr."
                pump_str += inputstr[i:close+1]
                i = close+1
            else:
                pump_str += self.curl_open+"1"+self.curl_close


            if i < len(inputstr) and inputstr[i] == self.branch_open:
                pump_str += self.branch_open
                i += 1

        return pump_str

    ## Remove all curly brackets from the string and repeat repeated units.
    ##
    ## @param inputstr String without abbreviations but with curlies.
    ## @return long string without curlies.
    def remove_curls(self,inputstr):
        inputstr = self.pumpup_str(inputstr)
        no_curls_str = ""
        i = 0
        while i < len(inputstr):
            if inputstr[i] == self.branch_open:
                no_curls_str += self.branch_open
                i += 1
                continue

            close = inputstr.find(self.curl_open,i)
            if close >= 0:
                N = int(inputstr[close+1:inputstr.find(self.curl_close,close+1)])
                if inputstr[close-1] == self.branch_close:
                    no_curls_str += self.branch_close
                    level = 1
                    j = len(no_curls_str)-2
                    string = ""
                    while level > 0:
                        assert j>=0
                        if no_curls_str[j] == self.branch_close:
                            level += 1
                        if no_curls_str[j] == self.branch_open:
                            level -=1
                        string = no_curls_str[j] + string
                        j -= 1

                    start = j+1
                    assert start > 0
                    end = len(no_curls_str)-1
                    assert end > 0
                    for i in range(1,N):
                        no_curls_str += no_curls_str[start:end+1]
                else:
                    end = close
                    assert end > 0
                    start = inputstr[:end].rfind(self.string_close)
                    assert start > 0,str(start)
                    start = inputstr[:start].rfind(self.string_open)
                    assert start >= 0
                    for i in range(N):
                        no_curls_str += inputstr[start:end]

            i = inputstr.find(self.curl_close,close)
            if i < 0:
                i = len(inputstr)
            else:
                i += 1
        return no_curls_str

    ## Create the type lists of the molecule
    ##
    ## @param inputstr fully proccessed input string
    ## @param knownTypes Interaction instance.
    ## @return list of particle types per monomer
    def create_type_lists(self,inputstr,knownTypes):
        type_list_equiv = []
        type_list_exact = []
        i=0
        while i < len(inputstr) :
            i = inputstr.find(self.string_open,i)
            if i < 0:break
            start = i
            end = inputstr.find(self.string_close,start+1)
            assert end >=0

            name = inputstr[start+1:end]

            type_list_equiv.append( knownTypes.get_equiv(name) )
            type_list_exact.append( knownTypes.get_exact(name) )


            i = end+1
        ## List that contains all particle types per monomer
        self.type_list_equiv = type_list_equiv
        ## List that contains all half-bond types per monomer
        self.type_list_exact = type_list_exact

    ## Function to create a list containing the branch id per monomer
    ##
    ## @param inputstr Fully proccessed input string
    ## @return List identifying the branch id per monomer.
    def get_branch_id_list(self,inputstr):
        branch_id = []
        for i in range(self.N):
            branch_id.append(0)
        i = 0
        branch= 0
        mono = 0
        while i < len(inputstr):
            while i< len(inputstr) and inputstr[i] != self.branch_open:
                if inputstr[i] == self.string_open:
                    mono += 1
                    i = inputstr.find(self.string_close,i+1)+1
                i += 1
            if i>= len(inputstr): break
            branch += 1

            branch_level = -1
            j = i
            mono_save = mono
            while branch_level != 0:
                if inputstr[j] == self.string_open:
                    branch_id[mono] = branch
                    mono += 1
                    j = inputstr.find(self.string_close,j+1)+1

                if inputstr[j] == self.branch_open:
                    if branch_level == -1:
                        branch_level = 0
                    branch_level += 1
                if inputstr[j] == self.branch_close:
                    branch_level -= 1

                j+=1
            mono = mono_save
            i += 1
        return branch_id

    ## Function to create a list containing the branch level aka recursion depth per monomer
    ##
    ## @param inputstr Fully proccessed input string
    ## @return List identifying the branch level per monomer.
    def get_branch_level_list(self,inputstr):
        i=0
        mono = -1
        branch = 0
        branch_level = []
        while i < len(inputstr):
            while i< len(inputstr):
                if inputstr[i] == self.string_open:
                    mono += 1
                    branch_level.append(branch)
                    i = inputstr.find(self.string_close,i+1)+1
                if inputstr[i] == self.branch_open:
                    branch += 1
                if inputstr[i] == self.branch_close:
                    branch -= 1
                i += 1

        return branch_level

    ## Function to get the additional bonding tags per monomer
    ##
    ## @param inputstr fully processed inputstring
    ## @return list of list containing all additional bond tags
    def get_tag_list(self,inputstr):
        i=0
        mono=-1
        tag_list = []
        while i < len(inputstr):
            i = inputstr.find(self.string_open,i)
            if i < 0:
                i = len(inputstr)
                continue

            close = inputstr.find(self.string_close,i+1)
            mono += 1
            tag_list.append([])
            next_mono = inputstr.find(self.string_open,close+1)
            if next_mono < 0:
                next_mono = len(inputstr)
            tag_start = close
            while inputstr.find(self.tag_close,i+1,next_mono)>=0:
                tag_end = inputstr.find(self.tag_close,i+1,next_mono)
                tag = int(inputstr[tag_start+1:tag_end])
                if tag != 0:
                    assert tag>0
                    tag_list[mono].append(tag)
                tag_start = tag_end
                i = tag_end
            i = next_mono

        return tag_list

    ##Add all the extra bonds via the tags to the molecule
    ##
    ## @param bond_list List containing all the bonds (output)
    ## @param branch_id_list List containg the branch id per monomer
    ## @param tag_list list containing the addtional extra tags per monomer
    ## @param inter Interaction instance with known interactions
    ## @return None
    def add_extra_bond(self,bond_list,branch_id_list,tag_list,inter):
        for i in range(self.N):
            for tag in tag_list[i]:
                for j in range(i+1,self.N):
                    if branch_id_list[i] == branch_id_list[j] and tag in tag_list[j]:
                        bond_list[i].append((j-i,inter.get_bond(self.type_list_exact[i],self.type_list_exact[j])))
                        bond_list[j].append((i-j,inter.get_bond(self.type_list_exact[i],self.type_list_exact[j])))

    ##Add all the branch point bonds to the molecule
    ##
    ## @param bond_list List containing all the bonds (output)
    ## @param branch_id_list List containg the branch id per monomer
    ## @param branch_level_list List containing the branch level per monomer
    ## @param inter Interaction instance with known interactions
    ## @return None
    def add_branch_bonds(self,bond_list,branch_id_list,branch_level_list,inter):
        for i in range(1,self.N):
            if branch_id_list[i-1] < branch_id_list[i]:
                j= i
                while branch_level_list[j]+1 != branch_level_list[i]:
                    j-=1
                bond_list[i].append((j-i,inter.get_bond(self.type_list_exact[i],self.type_list_exact[j])))
                bond_list[j].append((i-j,inter.get_bond(self.type_list_exact[i],self.type_list_exact[j])))

    ##Add all the linear back bone bonds
    ##
    ## @param bond_list List containing all the bonds (output)
    ## @param branch_id_list List containg the branch id per monomer
    ## @param inter Interaction instance with known interactions
    ## @return None
    def add_linear_bonds(self,bond_list,branch_id_list,inter):
        for i in range(self.N):
            for j in range(i+1,self.N):
                if branch_id_list[i] == branch_id_list[j]:
                    bond_list[i].append((j-i,inter.get_bond(self.type_list_exact[i],self.type_list_exact[j])))
                    bond_list[j].append((i-j,inter.get_bond(self.type_list_exact[i],self.type_list_exact[j])))
                    break


    ## Create and return a list of bonds per monomer
    ##
    ## @param inputstr fully processed input string
    ## @param inter Interaction instance of known types
    ## @return List, which creates
    def get_bond_list(self,inputstr,inter):
        bond_list = []
        for i in range(self.N):
            bond_list.append([])

        ## List of all additional tags per monomer
        self.tag_list = self.get_tag_list(inputstr)
        ## List of the branch level per monomer
        self.branch_level_list = self.get_branch_level_list(inputstr)
        ## List of the branch id per monomer
        self.branch_id_list = self.get_branch_id_list(inputstr)

        #create extra bonds
        self.add_extra_bond(bond_list,self.branch_id_list,self.tag_list,inter)

        #create branch bonds
        self.add_branch_bonds(bond_list,self.branch_id_list,self.branch_level_list,inter)

        #create linear bonds
        self.add_linear_bonds(bond_list,self.branch_id_list,inter)

        #order and remove duplicates and 0
        for i in range(self.N):
            bond_list[i] = tuple(sorted(list(set(bond_list[i])-set([0]))))

        return bond_list


    ## Create a string containing the molecule architecture as a "dot-graph"
    ##
    ## The "dot" tool fromthe Graphviz package can be used to
    ## visualiue the Architecture.
    ## @param graph_name String to name the molecule
    ## @param inter Interaction instance to name Molecule types
    ## @return String containing the dot-graph.
    def get_dot_graph(self,graph_name,inter):
        string = "digraph "+str(graph_name)+"{\n"
        for i in range(len(self.type_list_exact)):
            type = self.type_list_exact[i]
            string += "\t"+str(i)+" [label=\""+str(inter.knownTypes.get_name(type))+"\"];\n"
        string += "\n"
        for i in range(len(self.bond_list)):
            for tu in self.bond_list[i]:
                j = tu[0]+i
                if i < j:
                    string += "\t"+str(i)+" -> "+str(j)+" [arrowhead=none];\n"
        string +="}\n"
        return string
## Class to store and access the interaction of different particles.
##
## Each particle has two different types. The first one is the \a
## particle-type and this dictates the non-bonded interactions. The
## other type is called the \a half-bond type. This type specifies the
## type of bonds which are attached to this monomer. If two monomers
## are connected the two half-bond types define together the bond
## type. The matching of two half-bond types to a bond type are
## defined in the "bonds" tag.
class Interaction:
    ## Inialization of an interaction instance.
    ##
    ## @param interaction html element containing the specifications.
    ## @param knownTypes Types instance to identify strings to type ids.
    def __init__(self,interaction,knownTypes):
        ## Tags known to interaction
        knownTags = ["kappaN","chiN","bonds"]
        for child in interaction:
            if not child.tag in knownTags:
                print("WARNING: unknown tag ("+child.tag+") found in Interaction xml. Value will be ignored. Typo?")


        ## Types corresponding to this instance.
        self.knownTypes = knownTypes
        self._interaction_dict = {}
        kappaN = ""
        for kappa in interaction.iter("kappaN"):
            kappaN += kappa.text
        kappaN = float(kappaN)

        string = ""
        for chi in interaction.iter("chiN"):
            string += chi.text.strip()
        for line in string.split("\n"):
            line = line.strip()
            if len(line) > 0 and line[0] != '#':
                split = []

                i=0
                while i < len(line) and len(split) != 2:
                    if line[i] == Molecule.string_open:
                        close = line.find(Molecule.string_close,i+1)
                        assert close > 0
                        split.append( line[i:close] )
                        i = close
                    elif not line[i].isspace():
                        split.append(line[i])
                    i += 1
                split += line[i:].split()

                assert len(split) == 3
                assert (self.knownTypes.get_equiv(split[0]) != self.knownTypes.get_equiv(split[1])), "chiN may only be defined for non identical types."
                self._set_interaction(split[0],split[1],float(split[2]))

        ## Dictonary that stores the offset in the poly_arch array for every "type" of bondlist of a monomer.
        self._bond_dict = {}
        string = ""
        for chi in interaction.iter("bonds"):
            string += chi.text.strip()
        for line in string.split("\n"):
            line = line.strip()
            if len(line) > 0 and line[0] != '#':
                split = []

                i=0
                while i < len(line) and len(split) != 2:
                    if line[i] == Molecule.string_open:
                        close = line.find(Molecule.string_close,i+1)
                        assert close > 0
                        split.append( line[i:close] )
                        i = close
                    elif not line[i].isspace():
                        split.append(line[i])
                    i += 1
                split += line[i:].split()

                assert len(split) == 3
                self._set_bond(split[0],split[1],split[2] )

        for t in range(self.knownTypes.n_types_equiv):
            self._set_interaction(t,t,kappaN)

    ## Define the interaction value (chiN or kappaN) between two types.
    ##
    ## @param a string name of the first
    ## @param b string name of the second
    ## @param value (chiN or kappaN) between the types.
    def _set_interaction(self,a,b,value):
        if type(a) == str:
            a = self.knownTypes.get_equiv(a)
        if type(b) == str:
            b = self.knownTypes.get_equiv(b)
        value = float(value)
        s = tuple(sorted( [a,b] ))
        self._interaction_dict[s] = value

    ## Set the bond type between to monomer name types.
    ##
    ## @param a string name of the first
    ## @param b string name of the second
    ## @param name Name of the bond type.
    def _set_bond(self,a,b,name):
        if type(a) == str:
            a = self.knownTypes.get_exact(a)
        if type(b) == str:
            b = self.knownTypes.get_exact(b)
        if type(name) == str:
            name = bondDict[name.upper()]

        s = tuple(sorted( [a,b] ) )
        self._bond_dict[s] = name

    ## Get the interaction value between to types.
    ##
    ## @param a string name of the first
    ## @param b string name of the second
    ## @return (chiN or kappaN) between the types.
    def get_interaction(self,a,b):
        if type(a) == str:
            a = self.knownTypes.get_equiv(a)
        if type(b) == str:
            b = self.knownTypes.get_equiv(b)

        s = tuple(sorted( [a,b] ))
        return self._interaction_dict[s]

    ## Get the bond type between to monomer name types.
    ##
    ## @param a string name of the first
    ## @param b string name of the second
    ## @return bond id of the bond type.
    def get_bond(self,a,b):
        if type(a) == str:
            a = self.knownTypes.get_exact(a)
        if type(b) == str:
            b = self.knownTypes.get_exact(b)

        s = tuple(sorted( [a,b] ) )
        return self._bond_dict[s]

    ## Get the interaction matrix ready for SOMA.
    ##
    ## The diagonal contains kappaN, the off diagonal terms the chiN
    ## value between two types.
    ## @return Numpy array ready for SOMA.
    def get_interaction_matrix(self):
        matrix = numpy.zeros( (self.knownTypes.n_types_equiv,self.knownTypes.n_types_equiv), dtype=soma_type.get_soma_scalar_type() )
        for i in range(self.knownTypes.n_types_equiv):
            for j in range(self.knownTypes.n_types_equiv):
                matrix[i][j] = self.get_interaction(i,j)
        return matrix

## See C funtion documentation
def get_info(offset,bond_type,end):
    offset = numpy.int32(offset)<<4
    bond_type = numpy.uint32(bond_type)<<1
    end = numpy.uint32(end)
    return offset | bond_type | end

## See C funtion documentationd
def get_info_bl(offset_bl,type):
    ret = numpy.uint32(offset_bl)
    type = numpy.uint32(type)
    ret <<= 8
    ret |= type
    return ret

## See C funtion documentationd
def get_bond_type(info):
    info = numpy.uint32(info)
    info &= int('0xE',0)
    return info>>1

## See C funtion documentationd
def get_offset(info):
    info = numpy.int32(info)
    return info>>4

## See C funtion documentationd
def get_end(info):
    info = numpy.uint32(info)
    return info & 1

## See C funtion documentationd
def get_bondlist_offset(info_bl):
    info_bl = numpy.uint32(info_bl)
    return info_bl>>8

## See C funtion documentationd
def get_particle_type(info_bl):
    info_bl = numpy.uint32(info_bl)
    return int('0xFF',0) & info_bl


## Class to create a poly_arch array for a given set of molecules.
class PolyArch:
    ## Init and create the poly_arch array
    ##
    ## @param ms_list list of MoleculeSet instances containing the molecules.
    ## @param inter Interaction instance describing the interaction between the types.
    def __init__(self,ms_list,inter):
        ## Dict to store of bond offsets.
        self.offset_bond_dict = {}

        i= len(ms_list)
        for ms in ms_list:
            i += ms.mol.N

        self.offset_bond_dict[()] = -1
        for ms in ms_list:
            for bond_tuple in ms.mol.bond_list:
                if bond_tuple not in self.offset_bond_dict.keys():
                    self.offset_bond_dict[bond_tuple] = i
                    i += len(bond_tuple)

        ## List containing the number of monomers per polymer_type
        self.N_list = []
        for ms in ms_list:
            self.N_list.append(ms.mol.N)

        ## Offset for each polymer type
        self.poly_type_offset = numpy.zeros( (len(self.N_list),), dtype=numpy.int32)
        self.poly_type_offset[0] = 0
        for i in range(len(self.N_list)-1):
            self.poly_type_offset[i+1] = self.poly_type_offset[i] + self.N_list[i]+1


        ## Dict to store where the bonds start
        self.bondoffset_dict = {}
        for ms in ms_list:
            mol = ms.mol
            l = []
            for i in range(mol.N):
                l.append( (self.offset_bond_dict[mol.bond_list[i]],mol.type_list_equiv[i]) )

            self.bondoffset_dict[ms_list.index(ms)] = l

        #create poly arch list
        poly_arch_tuple = []
        for ms in ms_list:
            mol = ms.mol
            poly_arch_tuple.append(ms.mol.N)
            poly_arch_tuple += self.bondoffset_dict[ms_list.index(ms)]

        for k in self.offset_bond_dict.keys():
            for i in range(len(k)):
                poly_arch_tuple.append(None)

        for k in self.offset_bond_dict.keys():
            start = self.offset_bond_dict[k]
            if start > 0:
                for i in range(len(k)-1):
                    poly_arch_tuple[start+i] = (k[i][0],k[i][1],0)
                i = len(k)-1
                poly_arch_tuple[start+i] = (k[i][0],k[i][1],1)

        ## PolyArch array, but instead of binary shifting store info in tuples
        self.poly_arch_tuple = poly_arch_tuple
        poly_arch = numpy.zeros( (len(self.poly_arch_tuple),), dtype=numpy.int32)

        for i in range(len(self.poly_arch_tuple)):
            bond_info = self.poly_arch_tuple[i]
            element = numpy.int32(0)
            if type(bond_info) is int:
                element += bond_info
            else:
                if len(bond_info) == 2:
                    element = get_info_bl(bond_info[0],bond_info[1])
                if len(bond_info) == 3:
                    element= get_info( bond_info[0],bond_info[1],bond_info[2])

            poly_arch[i] = element
        ## Array with the final poly_arch information
        self.poly_arch = poly_arch


## Virtual base class for Objects living on a grid. Designed to specify area51 and external Field objects.
class GridObject(object):
    ## Init with a given number of type.s
    def __init__(self,n_types):
        self._internal_dict = {}
        ## The number of particle types of the corresponding grid.
        self.n_types = n_types

    ## Get the valus for a given grid index.
    ##
    ## @param index tuple containing the x,y,z index of the grid.
    ## @return value tuple if grid is specified, otherwise None
    def get(self,index):
        try:
            return self._internal_dict[index]
        except KeyError:
            return None

    ## Access all keys stored.
    ##
    ## @return list of all keys.
    def get_keys(self):
        return self._internal_dict.keys()

    ## Get the an x,y,z tuple from a "point" xml element.
    ##
    ## @param string xml text
    ## @return tuple
    def get_point(self,string):
        string = string.strip().split()
        assert len(string) == 3
        tu = tuple()
        for i in range(3):
            tu += (int(string[i]),)
        return tu

    ## Get the an value tuple from a "value" xml element.
    ## @param string xml text
    ## @return tuple
    def get_value(self,string):
        string = string.strip().split()
        tu = tuple()
        for i in range(len(string)):
            tu += (float(string[i]),)
        assert len(tu) == self.n_types
        return tu

    ## Get the norm of a vector.
    ##
    ## @param a tuple containing the vector
    ## @return Norm
    def get_norm(self,a):
        return numpy.sqrt( float(self.get_dot(a,a)) )

    ## Get the dot product of two vectors.
    ##
    ## @param a tuple containing argument 1
    ## @param b tuple containing argument 2
    ## @return dot product of the two 3-dim vectors.
    def get_dot(self,a,b):
        assert len(a) == 3
        assert len(b) == 3
        return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

## Class to store random elements grid points and corresponding values.
class PointCloud(GridObject):
    ## Init random grind points.
    ## @param element xml element containing the description "x y z value[]"
    ## @param n_types Number of types and therefore len of value.
    def __init__(self,element,n_types):
        super(PointCloud,self).__init__(n_types)

        string = element.text
        string = string.strip()
        for line in string.split("\n"):
            line = line.strip()
            if len(line) > 0 and line[0] != '#':
                line = line.split()
                assert len(line) == 3+self.n_types
                index = tuple()
                value = tuple()
                for i in range(3+self.n_types):
                    if i < 3:
                        index += (int(line[i]),)
                    else:
                        value += (float(line[i]),)
                self._internal_dict[index] = value

## Rectangular Grid object specifying a continguous box filled with the same values.
class Box(GridObject):
    ## Init the box object
    ##
    ## @param element xml elemet describing the box.
    ## @param n_types Number of particle types.
    def __init__(self,element,n_types):
        super(Box,self).__init__(n_types)
        knownTags = ["point","value"]
        for child in element:
            if not child.tag in knownTags:
                print("WARNING: unknown tag ("+child.tag+") found in Box xml. Value will be ignored. Typo?")

        assert len(element.findall('point')) == 2
        cl = []
        for point in element.findall('point'):
            cl.append( self.get_point(point.text) )

        value = self.get_value( element.find('value').text )

        for x in range( sorted([cl[0][0],cl[1][0]])[0],sorted([cl[0][0],cl[1][0]])[1]+1 ):
            for y in range( sorted([cl[0][1],cl[1][1]])[0],sorted([cl[0][1],cl[1][1]])[1]+1 ):
                for z in range( sorted([cl[0][2],cl[1][2]])[0],sorted([cl[0][2],cl[1][2]])[1]+1 ):
                    self._internal_dict[ (x,y,z) ] = value

## Cylinder Grid object specifying a cylinder filled with the same values.
class Cylinder(GridObject):
    ## Init a cylinder.
    ##
    ## @param element xml element specifiying a cylinder.
    ## @param n_types Number of types on the grid
    def __init__(self,element,n_types):
        super(Cylinder,self).__init__(n_types)
        knownTags = ["point","value","radius"]
        for child in element:
            if not child.tag in knownTags:
                print("WARNING: unknown tag ("+child.tag+") found in Cylinder xml. Value will be ignored. Typo?")

        assert len(element.findall('point')) == 2
        cl = []
        for point in element.findall('point'):
            cl.append( self.get_point(point.text) )

        value = self.get_value( element.find('value').text )
        radius = float(element.find('radius').text.strip())

        a = cl[0]
        u = ( cl[1][0] - cl[0][0], cl[1][1] -cl[0][1], cl[1][2] - cl[0][2])

        for x in range( int(round(sorted([cl[0][0],cl[1][0]])[0]-radius)) ,int(round(sorted([cl[0][0],cl[1][0]])[1]+1+radius)) ):
            for y in range( int(round(sorted([cl[0][1],cl[1][1]])[0]-radius)),int(round(sorted([cl[0][1],cl[1][1]])[1]+1+radius)) ):
                for z in range( int(round(sorted([cl[0][2],cl[1][2]])[0] -radius)),int(round(sorted([cl[0][2],cl[1][2]])[1]+1+radius)) ):
                    dist = self.get_distance( (x,y,z), a, u)
                    proj = self.get_dot( (x-a[0],y-a[1],z-a[2]) , u) / (self.get_norm(u))**2
                    if dist < radius and (proj>=0 and proj<=1):
                        self._internal_dict[ (x,y,z) ] = value


    ## Get the nearest distance between a line and a point.
    ##
    ## @param p point
    ## @param a point in the line
    ## @param u vector along the line
    ## @return nearest distance between the line and the point
    def get_distance(self,p,a,u):

        step1 = (float(p[0]-a[0]),float(p[1]-a[1]),float(p[2]-a[2]))

        step2 = self.get_cross( step1 , u )

        return self.get_norm(step2)/self.get_norm(u)


    ##Cross product of two vectors.
    ##
    ## @param a argument 1
    ## @param b argument 2
    ## @return a x b
    def get_cross(self,a,b):
        x = a[1]*b[2] - a[2]*b[1]
        y = a[2]*b[0] - a[0]*b[2]
        z = a[0]*b[1] - a[1]*b[0]
        return (x,y,z)

## Sphere GridObject.
class Sphere(GridObject):
    ## Init the Sphere object.
    ##
    ## @param element xml element definig the sphere.
    ## @param n_types Number of particle types on the grid.
    def __init__(self,element,n_types):
        super(Sphere,self).__init__(n_types)
        knownTags = ["point","value","radius"]
        for child in element:
            if not child.tag in knownTags:
                print("WARNING: unknown tag ("+child.tag+") found in Sphere xml. Value will be ignored. Typo?")

        assert len(element.findall('point')) == 1
        center = self.get_point(element.find('point').text)
        value = self.get_value( element.find('value').text )
        radius = float(element.find('radius').text.strip())

        for x in range( int(numpy.floor(-radius)) ,int(numpy.ceil(radius)) ):
            for y in range( int(numpy.floor(-radius)) ,int(numpy.ceil(radius)) ):
                for z in range( int(numpy.floor(-radius)) ,int(numpy.ceil(radius)) ):

                    if self.get_norm( (x,y,z) ) < radius:
                        self._internal_dict[ (x+center[0],y+center[1],z+center[2]) ] = value


## Base class for all soma-xml parsing classes.
##
## Contains the top level known tags for a SOMA xml file.
class SomaXML:
    ## List of tag names known to Configuration
    knownTags = []
    knownTags += ["interactions"]
    knownTags += ["equivalent_particle_types"]
    knownTags += ["A"]
    knownTags += ["time"]
    knownTags += ["harmonicvariablescale"]
    knownTags += ["poly_arch"]
    knownTags += ["reference_Nbeads"]
    knownTags += ["lxyz"]
    knownTags += ["nxyz"]
    knownTags += ["hamiltonian"]
    knownTags += ["area51"]
    knownTags += ["external_field"]
    knownTags += ["umbrella_field"]
    knownTags += ["analysis"]
    knownTags += ["cm_a"]
    knownTags += ["k_umbrella"]
    knownTags += ["structure_q"]
    knownTags += ["polyconversion"]
    knownTags += ["monoconversion"]
    knownTags += ["mobility_modifier"]
    knownTags += ["density_weights"]
    knownTags += ["Tmin"]
    knownTags += ["Tmax"]
    knownTags += ["alpha"]

## Class to create a hdf5 configuration file generated by an input xml file.
class Configuration(SomaXML):
    ## Init the configuration from an xml file. Writing or updating is later initiated.
    ## @param self self
    ## @param filename File to parse in
    ## @param arguments cmd-line arguments.
    ## @return None
    def __init__(self,filename,arguments):
        ## Is the Configuration fully initialized?
        self.good = False
        ## XML tree of the input file.
        self.tree = ET.parse(filename)
        ## CMD-line arguments
        self.args = arguments
        ## Root of the xml tree.
        self.root = self.tree.getroot()
        assert self.root.tag == "soma","You are not parsing a SOMA input file."
        for child in self.root:
            if not child.tag in self.knownTags:
                print("WARNING: unknown tag ("+child.tag+") found in SOMA xml. Value will be ignored. Typo?")

        ## Types instance of the Configuration
        self.types = self.create_types()
        assert self.types

        ##Interaction instance of the Configuration
        self.interaction = self.create_interaction()
        assert self.interaction

        # After init do not allow more types to be added.
        self.types.lock_type()

        ## Number of refence Beads
        self.reference_Nbeads = self.create_reference_Nbeads()
        assert type(self.reference_Nbeads) is numpy.ndarray

        ## mobility A array of the Configuration
        self.A = self.create_A()
        assert type(self.A) is numpy.ndarray

        ## umbrella constant for the configuration
        self.k_umbrella = self.create_k_umbrella()
        assert type(self.k_umbrella) is numpy.ndarray

        ## Time of the configuration
        self.time = self.create_time()
        assert type(self.time) is numpy.ndarray

        ## Minimum annealing temperature
        self.Tmin = self.create_Tmin()
        assert type(self.Tmin) is numpy.ndarray

        ## Maximum annealing temperature
        self.Tmax = self.create_Tmax()
        assert type(self.Tmax) is numpy.ndarray

    
        ## Annealing temperature decrease factor
        self.alpha = self.create_alpha()
        assert type(self.alpha) is numpy.ndarray

        ## harmonic_harmonic_normb_variable_scale of the configuration
        self.harmonic_normb_variable_scale = self.create_harmonic_normb_variable_scale()

        ## List of all MoleculesSets
        self.molecule_set_list = self.create_molecule_set_list()

        ## PolyArch instance of the Configuration
        self.poly_arch = self.create_poly_arch()

        tmp = numpy.zeros((1,),dtype=numpy.uint32)
        tmp[0] = len(self.molecule_set_list)
        ## Number of polymer types
        self.n_poly_type = copy.deepcopy(tmp)

        ## Mobility of the center of mass for every polymer.
        self.cm_a = self.create_cm_a()

        tmp[0] = 0
        tmp_long = numpy.zeros((1,),dtype = numpy.uint64)
        for ms in self.molecule_set_list:
            tmp_long[0] += ms.N
        ##Total Number of polymers
        self.n_polymers = copy.deepcopy(tmp_long)

        tmp[0] = self.types.n_types_equiv
        ## Number particle types.
        self.n_types = copy.deepcopy(tmp)

        tmp[0] = len(self.poly_arch.poly_arch)
        ## Length of the poly_arch array
        self.poly_arch_length = copy.deepcopy(tmp)

        ## Interaction matrix
        self.xn = self.interaction.get_interaction_matrix()

        ## Box dimension in units of Re
        self.lxyz = self.create_lxyz()

        ## Grid dimension in grid points
        self.nxyz = self.create_nxyz()

        ## Hamiltonian of system
        self.hamiltonian = self.create_hamiltonian()

        ## List of the type of each polymer
        self.poly_type = numpy.zeros((self.n_polymers[0],),dtype=numpy.uint32)

        offset = 0
        for t in range(len(self.molecule_set_list)):
            i = 0
            while i < self.molecule_set_list[t].N:
                self.poly_type[i+offset] = t
                i += 1
            offset += self.molecule_set_list[t].N

        self.poly_tag = numpy.arange(self.n_polymers[0],dtype=numpy.uint64)

        ## Area51 array
        self.area51 = self.create_area51()

        ## External Field array
        self.external_field = self.create_external_field()

        ##String Field array
        self.umbrella_field = self.create_umbrella_field()

        #Density weights
        self.density_weights = self.create_density_weights()

        ## initialize the poly conversion class
        self.poly_conversion = Configuration.PolyConversion(self.root,self.nxyz,self.poly_arch,self.types)

        ## initialize the mono conversion class
        self.mono_conversion = Configuration.MonoConversion(self.root,self.nxyz,self.poly_arch,self.types)

        ## initalize the MobilityModifier class
        self.mobility_modifier = Configuration.MobilityModifier(self.root,self.n_types[0],self.n_poly_type[0])

        self.good = True

    ## Write the configuration to a hdf5-file.
    ##
    ## @param filename Filename of the new hdf5 file. If it exists it will be overwritten.
    ## @param openstr String rep to identify how to open the file. Default "w" for overwrite.
    ## @return None
    def write_hdf5(self,filename,openstr="w"):
        if not self.good:
            print("ERROR: not fully initialized Configurations cannot be written to hdf5.")

        with h5py.File(filename,openstr) as f:
            if not "parameter" in f:
                f.create_group("parameter")

            create_list = []
            create_list += [("/version",numpy.asarray([1],dtype=numpy.uint))]
            create_list += [("/parameter/A",self.A)]
            create_list += [("/parameter/lxyz",self.lxyz)]
            create_list += [("/parameter/nxyz",self.nxyz)]
            create_list += [("/parameter/hamiltonian",self.hamiltonian)]
            create_list += [("/parameter/k_umbrella",self.k_umbrella)]
            create_list += [("/parameter/xn",self.xn)]
            create_list += [("/parameter/time",self.time)]
            create_list += [("/parameter/n_types",self.n_types)]
            create_list += [("/parameter/n_poly_type",self.n_poly_type)]
            create_list += [("/parameter/n_polymers",self.n_polymers)]
            create_list += [("/parameter/reference_Nbeads",self.reference_Nbeads)]
            create_list += [("/parameter/poly_type_offset",self.poly_arch.poly_type_offset)]
            create_list += [("/parameter/poly_arch_length",self.poly_arch_length)]
            create_list += [("/parameter/poly_arch",self.poly_arch.poly_arch)]
            create_list += [("/parameter/Tmin",self.Tmin)]
            create_list += [("/parameter/Tmax",self.Tmax)]
            create_list += [("/parameter/alpha",self.alpha)]
            create_list += [("/poly_type",self.poly_type)]
            create_list += [("/poly_tag",self.poly_tag)]
            create_list += [("/parameter/density_weights",self.density_weights)]
            if type(self.cm_a) is numpy.ndarray:
                create_list += [("/parameter/cm_a",self.cm_a)]
            if type(self.harmonic_normb_variable_scale) is numpy.ndarray:
                create_list += [("/parameter/harmonic_normb_variable_scale",self.harmonic_normb_variable_scale)]


            for element in create_list:
                if element[0] in f:
                    del f[element[0]]
                f.create_dataset(element[0],data=element[1])



            if "/area51" in f:
                del f["/area51"]

            if type(self.area51) is numpy.ndarray:
                f.create_dataset("/area51",data=self.area51)
            if "/external_field" in f:
                del f["/external_field"]
            if type(self.external_field) is numpy.ndarray:
                f.create_dataset("/external_field",data=self.external_field)

                for element in self.root.find("external_field").iter("time"):
                    index=-1
                    for child in element:
                        if child.tag=="period":
                            tmp_file = stringio.StringIO(child.text)
                            period = numpy.loadtxt( tmp_file, dtype=numpy.float32)
                            f["external_field"].attrs[child.tag] = period
                        else:
                            index=index+1
                            tmp_file = stringio.StringIO(child.text)
                            array = numpy.loadtxt( tmp_file, dtype=numpy.float32)
                            f["external_field"].attrs[child.tag] = array
                            if index==0:
                                tmp_size=array.size
                                assert (tmp_size == array.size),"Error prefactors must have the same length."

                    f["external_field"].attrs["serie_length"] = tmp_size
            if "/umbrella_field" in f:
                del f["/umbrella_field"]
            if type(self.umbrella_field) is numpy.ndarray:
                f.create_dataset("/umbrella_field",data=self.umbrella_field)

            if "polyconversion" in f:
                del f["polyconversion"]
            if self.poly_conversion.delta_mc[0] != 0 :
                f.create_group("polyconversion")
                f.create_dataset("polyconversion/deltaMC",data=self.poly_conversion.delta_mc)
                f.create_dataset("/polyconversion/array",data=self.poly_conversion.array,dtype=numpy.uint8)
                f.create_dataset("/polyconversion/input_type",data=self.poly_conversion.pc_list[:,0])
                f.create_dataset("/polyconversion/output_type",data=self.poly_conversion.pc_list[:,1])
                f.create_dataset("/polyconversion/end",data=self.poly_conversion.pc_list[:,2])
                if self.poly_conversion.rate_list != []:
                    f.create_dataset("polyconversion/rate",data=self.poly_conversion.rate_list)
                    f.create_dataset("/polyconversion/n_density_dependencies",data=self.poly_conversion.ndd_list)
                    f.create_dataset("/polyconversion/density_dependencies",data=self.poly_conversion.dd_list)

            if "monoconversion" in f:
                del f["monoconversion"]
            if self.mono_conversion.delta_mc[0] != 0 :
                f.create_group("monoconversion")
                f.create_dataset("monoconversion/deltaMC",data=self.mono_conversion.delta_mc)
                f.create_dataset("/monoconversion/array",data=self.mono_conversion.array,dtype=numpy.uint8)
                f.create_dataset("/monoconversion/input_type",data=self.mono_conversion.pc_list[:,0])
                f.create_dataset("/monoconversion/output_type",data=self.mono_conversion.pc_list[:,1])
                f.create_dataset("monoconversion/block_size",data=self.mono_conversion.block_size)

                f.create_dataset("/monoconversion/end",data=self.mono_conversion.pc_list[:,2])
                if self.mono_conversion.rate_list != []:
                    f.create_dataset("monoconversion/rate",data=self.mono_conversion.rate_list)
                    f.create_dataset("/monoconversion/n_density_dependencies",data=self.mono_conversion.ndd_list)
                    f.create_dataset("/monoconversion/density_dependencies",data=self.mono_conversion.dd_list)

            if "mobility" in f:
                del f["mobility"]
            f.create_group("mobility")
            f.create_dataset("mobility/poly_type_mc_freq",data=self.mobility_modifier.poly_type_mc_freq)
            f.create_dataset("mobility/type",data=numpy.asarray([self.mobility_modifier.type],dtype=numpy.uint32))
            if self.mobility_modifier.type != MobilityDict["DEFAULT_MOBILITY"]:
                f.create_dataset("mobility/param",data=self.mobility_modifier.param)


    ## Update an existing hdf5-file with the read parameter if possible.
    ## @param filename File name of the hdf5 file. It has to exist.
    ## @return None
    def update_hdf5(self,filename):
        if not self.good:
            print("ERROR: not fully initialized Configurations cannot be written to hdf5.")

        with h5py.File(filename,"r") as f:
            ensure_list = []
            ensure_list += [("/parameter/n_polymers",self.n_polymers)]
            for e in ensure_list:
                data = f[e[0]][0:]
                assert ((data == e[1]).all()),"Error "+e[0]+" property is not identical, but has to be constant."

            #check polymer N of old and new
            old_polytype = f['/poly_type'][:]
            new_polytype = copy.deepcopy(old_polytype)
            old_polyarch = f['/parameter/poly_arch'][:]
            old_polytypeoffset = f['/parameter/poly_type_offset'][:]
            try:
                old_polytag = f["/poly_tag"][:]
            except KeyError:
                old_polytag = np.arange(self.n_polymers[0],dtype=np.uint64)

            type_list = [self.molecule_set_list[0].N]
            for ms in self.molecule_set_list[1:]:
                type_list.append( type_list[-1] + ms.N )

            for i in range(self.n_polymers[0]):
                poly = old_polytag[i]          #use the tags to obtain the correct order of polymers
                old_type = old_polytype[i]
                old_N = old_polyarch[ old_polytypeoffset[old_type] ]

                new_type = 0
                while poly >= type_list[new_type]:
                    new_type += 1

                new_N = self.poly_arch.poly_arch[ self.poly_arch.poly_type_offset[new_type]]

                assert (old_N == new_N), "Error you changed N of a polymer. This is impossible. "+str((old_N,new_N,poly))
                new_polytype[i] = old_type;

            self.poly_type = new_polytype
            self.poly_tag = f["poly_tag"][:]
            self.time[0] = f["/parameter/time"][0]
            print("The time attribute will not be updated.")

        print("Updating configuration is possible. So we overwrite the new properties.")
        self.write_hdf5(filename,"r+")


    ## Create the Interaction instance.
    ## @return Interaction instance
    def create_interaction(self):
        assert len(self.root.findall('interactions')) == 1
        interaction = Interaction(self.root.find('interactions'),self.types)
        return interaction

    ## Create the Types instance.
    ## @return Types instance
    def create_types(self):
        equivalence_str = ""
        for equi in self.root.iter('equivalent_particle_types'):
            equivalence_str += equi.text
        types = Types(equivalence_str)
        return types

    ## Create the "A" mobility array
    ## @return A array
    def create_A(self):
        dt_found = False
        a_array = numpy.zeros( (self.types.n_types_equiv,),dtype=soma_type.get_soma_scalar_type())
        dt_str = ""
        for dt in self.root.find('A').iter('dt'):
            dt_str += dt.text.strip()
        # If a dt has been specified the array is initialized by that.
        if len(dt_str) > 0:
            dt_found = True
            dt = float(dt_str)
            for i in range(a_array.shape[0]):
                a_array[i] = dt/self.reference_Nbeads[0]


        a_str = ""
        for a in self.root.iter('A'):
            a_str += a.text
        a_dict = {}
        for line in a_str.split("\n"):
            line = line.strip()
            if len(line) > 0 and line[0] != '#':
                line = line.split()
                assert (len(line) == 2),("A entry should be composed by 'type_name value', but got "+str(line))
                a_dict[self.types.get_equiv(line[0])] = float(line[1])
        if not dt_found:
            assert(len(a_dict) == self.types.n_types_equiv),"Each particle type needs a mobility if no dt is specified."
        else:
            assert(len(a_dict) <= self.types.n_types_equiv),"You can not specify more mobilities, than types available."
        for i in a_dict.keys():
            a_array[i] = a_dict[i]

        return a_array

    ## Create the "k_umbrella" strength of the umbrella potential
    ## @return k_umbrella Array
    def create_k_umbrella(self):
        k_array = numpy.zeros( (self.types.n_types_equiv,),dtype=soma_type.get_soma_scalar_type())

        k_str = ""
        for k in self.root.iter('k_umbrella'):
            k_str += k.text
        k_dict = {}
        for line in k_str.split("\n"):
            line = line.strip()
            if len(line) > 0 and line[0] != '#':
                line = line.split()
                assert (len(line) == 2),("A entry should be composed by 'type_name value', but got "+str(line))
                k_dict[self.types.get_equiv(line[0])] = float(line[1])

        for i in k_dict.keys():
            k_array[i] = k_dict[i]

        return k_array

    ## Create the "density_weights"
    ## @return density_weights Array
    def create_density_weights(self):
        density_weights = numpy.zeros( (self.types.n_types_equiv,),dtype=soma_type.get_soma_scalar_type())
        density_weights += 1

        dw_str = ""
        for dw in self.root.iter('density_weights'):
            dw_str += dw.text
        dw_dict = {}
        for line in dw_str.split("\n"):
            line = line.strip()
            if len(line) > 0 and line[0] != '#':
                line = line.split()
                assert (len(line) == 2),("A entry should be composed by 'type_name value', but got "+str(line))
                dw_dict[self.types.get_equiv(line[0])] = float(line[1])

        for i in dw_dict.keys():
            density_weights[i] = dw_dict[i]

        if density_weights.any() < 0:
            raise RuntimeError("Invalid negative density weights found")
        if density_weights.sum() == 0:
            raise RuntimeError("Invalid density weights with a sum of 0")

        #normalize weights
        old_sum = density_weights.sum()
        density_weights *= (density_weights.size/old_sum)

        assert abs(density_weights.sum() - self.types.n_types_equiv) < 1e-8, "Check density weight sum"+str(density_weights)
        print(density_weights)
        return density_weights


    ## Create the mobility array for each polymer type center of mass.
    ## @return cm_a array
    def create_cm_a(self):
        if len(self.root.findall("cm_a")) == 0:
            return None

        array = numpy.zeros( (self.n_poly_type[0],),dtype=soma_type.get_soma_scalar_type())

        string = ""
        for element in self.root.iter('cm_a'):
            string += element.text
        l = string.strip().split()
        if len(l) != self.n_poly_type[0]:
            print("ERROR: no valid cm_a string found. Set mobility to 0 for all types.")
            return None
        i = 0
        for element in l:
            array[i] = float(element)
            i+=1

        return array


    ## Create the "time" attribute
    ## @return time array
    def create_time(self):
        time_str = ""
        for time in self.root.iter('time'):
            time_str += time.text
        time_str = time_str.strip()

        time = 0
        if len(time_str) > 0:
            time = int(time_str)
        time_array = numpy.zeros((1,),dtype=numpy.uint32)
        time_array[0] = time
        return time_array


    ## Create the "Tmin" attribute
    ## @return Tmin array
    def create_Tmin(self):
        Tmin_str = ""
        for Tmin in self.root.iter('Tmin'):
            Tmin_str += Tmin.text
        Tmin_str = Tmin_str.strip()
        Tmin_array = numpy.zeros((1,),dtype=soma_type.get_soma_scalar_type())
        if len(Tmin_str) > 0:
            Tmin = float(Tmin_str)
            Tmin_array[0] = Tmin
        return Tmin_array

    ## Create the "Tmax" attribute
    ## @return Tmax array
    def create_Tmax(self):
        Tmax_str = ""
        for Tmax in self.root.iter('Tmax'):
            Tmax_str += Tmax.text
        Tmax_str = Tmax_str.strip()
        Tmax_array = numpy.zeros((1,),dtype=soma_type.get_soma_scalar_type())
        if len(Tmax_str) > 0:
            Tmax = float(Tmax_str)
            Tmax_array[0] = Tmax
        return Tmax_array

    ## Create the "alpha" attribute
    ## @return alpha array
    def create_alpha(self):
        alpha_str = ""
        for alpha in self.root.iter('alpha'):
            alpha_str += alpha.text
        alpha_str = alpha_str.strip()
        alpha_array = numpy.zeros((1,),dtype=soma_type.get_soma_scalar_type())
        if len(alpha_str) > 0:
            alpha = float(alpha_str)
            alpha_array[0] = alpha
        return alpha_array

    ## Create the "create_harmonic_normb_variable_scale" attribute
    ## @return create_harmonic_normb_variable_scale array
    def create_harmonic_normb_variable_scale(self):
        harmonic_normb_variable_scale_str = ""
        for harmonic_normb_variable_scale in self.root.iter('harmonicvariablescale'):
            harmonic_normb_variable_scale_str += harmonic_normb_variable_scale.text
        harmonic_normb_variable_scale_str = harmonic_normb_variable_scale_str.strip()

        if len(harmonic_normb_variable_scale_str) > 0:
            harmonic_normb_variable_scale = numpy.zeros((1,),dtype=soma_type.get_soma_scalar_type())

            harmonic_normb_variable_scale[0] = float(harmonic_normb_variable_scale_str)
            return harmonic_normb_variable_scale
        else:
            return False

    ## Create the "reference_Nbeads" attribute.
    ## @return reference_Nbeads array
    def create_reference_Nbeads(self):
        string = ""
        for element in self.root.iter('reference_Nbeads'):
            string += element.text
        string = string.strip()

        reference_Nbeads = numpy.zeros((1,),dtype=numpy.uint32)
        reference_Nbeads[0] = int(string)
        return reference_Nbeads

    ## Create the MoleculeSet list.
    ## @return MoleculeSet list
    def create_molecule_set_list(self):
        string = ""
        for element in self.root.iter('poly_arch'):
            string += element.text
        string = string.strip()

        ms_list = []
        for ms_input in string.split("\n"):
            ms_input = ms_input.strip()
            if len(ms_input) > 0 and ms_input[0] != '#':
                ms_list.append(MoleculeSet(ms_input,self.interaction))

                assert (len(ms_list) > 0),"You have to specify polymer architectures."
        return ms_list

    ## Create the PolyArch instance.
    ## @return PolyArch instance
    def create_poly_arch(self):
        return PolyArch(self.molecule_set_list,self.interaction)

    ## Create the box dimensions.
    ## @return box dimension array
    def create_lxyz(self):
        string = ""
        for element in self.root.iter('lxyz'):
            string += element.text
        string = string.strip()

        string = string.split()
        assert len(string) == 3
        tmp = numpy.zeros((3,),dtype=soma_type.get_soma_scalar_type())
        for i in range(3):
            tmp[i] = float(string[i])
            assert tmp[i] > 0
        return tmp

    ## Create the grid dimensions.
    ## @return grid dimension array
    def create_nxyz(self):
        string = ""
        for element in self.root.iter('nxyz'):
            string += element.text
        string = string.strip()

        string = string.split()
        assert len(string) == 3
        tmp = numpy.zeros((3,),dtype=numpy.uint32)
        for i in range(3):
            tmp[i] = int(string[i])
            assert tmp[i] > 0
        return tmp

    ## Create the area51 (forbidden area)
    ## @return area51 array
    def create_area51(self):
        child_list = []
        knownTags = ["point_cloud","box","cylinder","sphere"]
        for element in self.root.iter('area51'):
            for child in element:
                if not child.tag in knownTags:
                    print("WARNING: unknown tag ("+child.tag+") found in Area51 xml. Value will be ignored. Typo?")

            for pc in element.findall('point_cloud'):
                child_list.append( PointCloud(pc,1) )

            for box in element.findall('box'):
                child_list.append( Box(box,1) )

            for cy in element.findall('cylinder'):
                child_list.append( Cylinder(cy,1) )

            for sp in element.findall('sphere'):
                child_list.append( Sphere(sp,1) )



        tmp = False
        if len(child_list) > 0:
            tmp = numpy.zeros((self.nxyz[0],self.nxyz[1],self.nxyz[2]),dtype=numpy.int8)
            for child in child_list:
                for k in child.get_keys():
                    (x,y,z) = k
                    if not self.args['area51_no_pbc']:
                        (xa,ya,za) = (k[0] % self.nxyz[0],k[1] % self.nxyz[1],k[2] % self.nxyz[2])
                    else:
                        (xa,ya,za) = (x,y,z)
                    if xa >= 0 and xa < self.nxyz[0] and ya >= 0 and ya < self.nxyz[1] and za >= 0 and za < self.nxyz[2]:
                        tmp[xa][ya][za] += child.get( (x,y,z) )[0]

            tmp = numpy.clip(tmp,0,1)

        if type(tmp) is numpy.ndarray :
            return tmp.astype(numpy.uint8)
        return False

    ## Class that parses the XML and stores the information for poly conversion zones
    class PolyConversion:
        ## Constructor of the PolyConversion class. Initialized with the root of the XML parser
        def __init__(self,root,nxyz,poly_arch,knownTypes):
            self.array = None
            self.pc_list = None
            self.delta_mc = numpy.asarray( [0], dtype=numpy.uint32)
            child_list = []
            pc_list = []
            rate_list = []
            dd_list = []
            raw_dd_list = []
            
            knownTags = ["point_cloud","box","cylinder","sphere","conversion_list","DeltaMC","conversion_rate","density_dependency"]
            for element in root.iter("polyconversion"):
                for child in element:
                    if not child.tag in knownTags:
                        print("WARNING: unknown tag ("+child.tag+") found in Polyconversion xml. Value will be ignored. Typo?")

                for pc in element.findall('point_cloud'):
                    child_list.append( PointCloud(pc,1) )

                for box in element.findall('box'):
                    child_list.append( Box(box,1) )

                for cy in element.findall('cylinder'):
                    child_list.append( Cylinder(cy,1) )

                for sp in element.findall('sphere'):
                    child_list.append( Sphere(sp,1) )

                for delta in element.findall("DeltaMC"):
                    try:
                        deltaMC = int(delta.text)
                    except ValueError:
                        raise RuntimeError("DeltaMC for poly conversion must be integer convertible but got: "+str(delta.text))

                for pc in element.findall("conversion_list"):
                    for line in pc.text.split("\n"):
                        line = line.strip()
                        if line == "" or line[0] == '#':
                            continue
                        parts = line.split()
                        if len(parts) != 3:
                            raise RuntimeError("A conversion list line has 3 elements: input_type output_type end_of_reaction=0/1. But got: "+line)
                        try:
                            input_type = int(parts[0])
                            output_type = int(parts[1])
                            end = int(parts[2])
                        except ValueError:
                            raise RuntimeError("A conversion list must consist of 3 integer, but got: "+line)
                        if input_type > len(poly_arch.poly_type_offset):
                            RuntimeError("Invalid poly input type "+str(input_type)+". Only "+str(len(poly_arch.poly_type_offset))+" poly types known.")
                        if output_type > len(poly_arch.poly_type_offset):
                            RuntimeError("Invalid poly output type "+str(output_type)+". Only "+str(len(poly_arch.poly_type_offset))+" poly types known.")
                        Ninput = poly_arch.poly_arch[poly_arch.poly_type_offset[input_type]]
                        Noutput = poly_arch.poly_arch[poly_arch.poly_type_offset[output_type]]
                        if Ninput != Noutput:
                            RuntimeError("Invalid conserion attempt! Input type "+str(input_type)+" has "+str(Ninput)+" beads but output type "+str(output_type)+" has "+str(Noutput)+" types.")

                        pc_list.append([input_type,output_type,bool(end)])


                for rt in element.findall("conversion_rate"):
                    for line in rt.text.split("\n"):
                        line = line.strip()
                        if line == "" or line[0] == '#':
                            continue
                        parts = line.split()
                        if len(parts) != 1:
                            raise RuntimeError("Conversion rate should be given as single float per conversion/line. But got: "+line)
                        try:
                            conversion_rate = float(parts[0])
                            rate_list.append(conversion_rate)
                        except ValueError:
                            raise RuntimeError("Conversion rate for poly conversion must be float convertible but got: "+str(rt.text))
                if rate_list != []:
                    assert len(rate_list) == len(pc_list), "ERROR: There should be given a rate for every conversion. Defined {} conversions, but only got {} rates.".format(len(pc_list), len(rate_list))
                
                for dd in element.findall("density_dependency"):
                    for line in dd.text.split("\n"):
                        line = line.strip()
                        if line == "" or line[0] == '#':
                            continue
                        parts = line.split()
                        if len(parts) != knownTypes.n_types_exact:
                            raise RuntimeError("Invalid density dependence format, give dependecies for all " + self.knownTypes.n_types_exact + "types. But got: "+len(parts))
                        try:
                            raw_dd_list.append(numpy.asarray(parts, dtype=int))
                        except ValueError:
                            raise RuntimeError("A density dependency list must consist only of integers, but got: "+line)
                if raw_dd_list == []:
                    raw_dd_list = numpy.zeros((len(pc_list), knownTypes.n_types_exact))
                raw_dd_list = numpy.asarray(raw_dd_list, dtype=numpy.uint32)
                ndd_list = numpy.sum(raw_dd_list, axis=1, dtype=numpy.uint32)
                for dependencies in raw_dd_list:
                    for i in range(knownTypes.n_types_exact):
                        for j in range(dependencies[i]):
                            dd_list.append(i)
                dd_list = numpy.asarray(dd_list, dtype=numpy.uint32)
                assert numpy.sum(ndd_list) == len(dd_list), "Total number of dependencies given in ndd does not match the number of dependencies in the list."

                        

            pbc = True
            if len(child_list) > 0:
                array = numpy.zeros(shape=nxyz,dtype=numpy.uint8)
                for child in child_list:
                    for k in child.get_keys():
                        (x,y,z) = k
                        if not pbc:
                            (xa,ya,za) = (k[0] % nxyz[0],k[1] % nxyz[1],k[2] % nxyz[2])
                        else:
                            (xa,ya,za) = (x,y,z)
                        if xa >= 0 and xa < nxyz[0] and ya >= 0 and ya < nxyz[1] and za >= 0 and za < nxyz[2]:
                            array[xa][ya][za] = child.get( (x,y,z) )[0] +1 #+1 because zero indicates no reaction

                pc_list = numpy.asarray(pc_list,dtype=numpy.uint32)
                if not pc_list[-1,2]:
                    raise RuntimeError("The poly type conversion list should finish with an end flag set. "+str(pc_list[-1,2])+" "+str(bool(pc_list[-1,2])))

                if numpy.max(array) > pc_list.shape[0]:
                    raise RuntimeError("The index in the array "+str(numpy.max(array)-1)+" is larger than the reaction list "+str(pc_list.shape[0]))

                self.array = array
                self.pc_list = pc_list
                self.delta_mc = numpy.asarray([deltaMC],dtype=numpy.uint32)
                self.rate_list = numpy.asarray(rate_list,dtype=soma_type.get_soma_scalar_type())
                self.ndd_list = ndd_list
                self.dd_list = dd_list
    ## Class that parses the XML and stores the information for poly conversion zones
    class MonoConversion:
        ## Constructor of the PolyConversion class. Initialized with the root of the XML parser
        def __init__(self,root,nxyz,poly_arch,knownTypes):
            self.array = None
            self.pc_list = None
            self.delta_mc = numpy.asarray( [0], dtype=numpy.uint32)
            child_list = []
            pc_list = []
            rate_list = []
            block_size = numpy.asarray( [1], dtype=numpy.uint32)
            dd_list = []
            raw_dd_list = []
            
            knownTags = ["point_cloud","box","cylinder","sphere","conversion_list","DeltaMC", "block_size","conversion_rate","density_dependency"]
            for element in root.iter("monoconversion"):
                for child in element:
                    if not child.tag in knownTags:
                        print("WARNING: unknown tag ("+child.tag+") found in Monoconversion xml. Value will be ignored. Typo?")

                for pc in element.findall('point_cloud'):
                    child_list.append( PointCloud(pc,1) )

                for box in element.findall('box'):
                    child_list.append( Box(box,1) )

                for cy in element.findall('cylinder'):
                    child_list.append( Cylinder(cy,1) )

                for sp in element.findall('sphere'):
                    child_list.append( Sphere(sp,1) )

                for delta in element.findall("DeltaMC"):
                    try:
                        deltaMC = int(delta.text)
                    except ValueError:
                        raise RuntimeError("DeltaMC for poly conversion must be integer convertible but got: "+str(delta.text))

                for pc in element.findall("conversion_list"):
                    for line in pc.text.split("\n"):
                        line = line.strip()
                        if line == "" or line[0] == '#':
                            continue
                        parts = line.split()
                        if len(parts) != 3:
                            raise RuntimeError("A conversion list line for monomer conversion has 3 elements: input_monomer_name output_monomer_name end_of_reaction=0/1. But got: "+line)
                        try:
                            input_type = knownTypes.get_exact(parts[0])
                            output_type = knownTypes.get_exact(parts[1])
                            end = int(parts[2])
                        except ValueError:
                            raise RuntimeError("A conversion list must consist of valid monomer type names and 1 integer, but got: "+line)

                        pc_list.append([input_type,output_type,bool(end)])


                for rt in element.findall("conversion_rate"):
                    for line in rt.text.split("\n"):
                        line = line.strip()
                        if line == "" or line[0] == '#':
                            continue
                        parts = line.split()
                        if len(parts) != 1:
                            raise RuntimeError("Conversion rate should be given as single float per conversion/line. But got: "+line)
                        try:
                            conversion_rate = float(parts[0])
                            rate_list.append(conversion_rate)
                        except ValueError:
                            raise RuntimeError("Conversion rate for poly conversion must be float convertible but got: "+str(rt.text))
                if rate_list != []:
                    assert len(rate_list) == len(pc_list), "ERROR: There should be given a rate for every conversion. Defined {} conversions, but only got {} rates.".format(len(pc_list), len(rate_list))
                
                for dd in element.findall("density_dependency"):
                    for line in dd.text.split("\n"):
                        line = line.strip()
                        if line == "" or line[0] == '#':
                            continue
                        parts = line.split()
                        if len(parts) != knownTypes.n_types_exact:
                            raise RuntimeError("Invalid density dependence format, give dependecies for all " + str(knownTypes.n_types_exact) + "types. But got: "+len(parts))
                        try:
                            raw_dd_list.append(numpy.asarray(parts, dtype=int))
                        except ValueError:
                            raise RuntimeError("A density dependency list must consist only of integers, but got: "+line)
                if raw_dd_list == []:
                    raw_dd_list = numpy.zeros((len(pc_list), knownTypes.n_types_exact))
                raw_dd_list = numpy.asarray(raw_dd_list, dtype=numpy.uint32)
                ndd_list = numpy.sum(raw_dd_list, axis=1, dtype=numpy.uint32)
                for dependencies in raw_dd_list:
                    for i in range(knownTypes.n_types_exact):
                        for j in range(dependencies[i]):
                            dd_list.append(i)
                dd_list = numpy.asarray(dd_list, dtype=numpy.uint32)
                assert numpy.sum(ndd_list) == len(dd_list), "Total number of dependencies given in ndd does not match the number of dependencies in the list."

                for bs in element.findall("block_size"):
                    for line in bs.text.split("\n"):
                        line = line.strip()
                        if line == "" or line[0] == '#':
                            continue
                        parts = line.split()
                        if len(parts) != 1:
                            raise RuntimeError("Block size should be given as single integer per conversion/line. But got: "+line)
                        try:
                            block_size[0] = numpy.uint32(parts[0])
                        except ValueError:
                            raise RuntimeError("Block size for poly conversion must be integer convertible but got: "+str(rt.text))

                pbc = True
                array = numpy.zeros(shape=nxyz,dtype=numpy.uint8)
                if len(child_list) > 0:
                    for child in child_list:
                        for k in child.get_keys():
                            (x,y,z) = k
                            if not pbc:
                                (xa,ya,za) = (k[0] % nxyz[0],k[1] % nxyz[1],k[2] % nxyz[2])
                            else:
                                (xa,ya,za) = (x,y,z)
                            if xa >= 0 and xa < nxyz[0] and ya >= 0 and ya < nxyz[1] and za >= 0 and za < nxyz[2]:
                                array[xa][ya][za] = child.get( (x,y,z) )[0] +1 #+1 because zero indicates no reaction

                pc_list = numpy.asarray(pc_list,dtype=numpy.uint32)
                if not pc_list[-1,2]:
                    raise RuntimeError("The mono type conversion list should finish with an end flag set. "+str(pc_list[-1,2])+" "+str(bool(pc_list[-1,2])))

                if numpy.max(array) > pc_list.shape[0]:
                    raise RuntimeError("The index in the array "+str(numpy.max(array)-1)+" is larger than the reaction list "+str(pc_list.shape[0]))

                self.array = array
                self.pc_list = pc_list
                self.delta_mc = numpy.asarray([deltaMC],dtype=numpy.uint32)
                self.rate_list = rate_list
                self.block_size = block_size
                self.ndd_list = ndd_list
                self.dd_list = dd_list
                

    ## Class that parses the XML and stores the information density dependent mobility modifications
    class MobilityModifier:
        ## Constructor of the MobilityModifier class. Initialized with the root of the XML parser
        def __init__(self,root,ntypes,n_poly_types):
            self.type = MobilityDict["DEFAULT_MOBILITY"]
            self.param = []

            self.poly_type_mc_freq = numpy.ones(n_poly_types,dtype=numpy.uint32);
            tmp_freq_array = []

            knownTags = ["type","param","poly_type_mc_freq"]
            for element in root.iter("mobility_modifier"):
                for child in element:
                    if not child.tag in knownTags:
                        print("WARNING: unknown tag ("+child.tag+") found in mobility_modifier xml. Value will be ignored. Typo?")

                for t in element.findall('type'):
                    text = t.text.strip().upper()
                    if text not in MobilityDict:
                        raise RuntimeError("Unknown mobility type for 'mobility_modifier': got "+str(text)+" expecting "+str(MobilityDict.keys()))
                    self.type = MobilityDict[text]

                for param in element.findall('param'):
                    text = param.text.strip().split()
                    for val in text:
                        self.param.append( float(val) )

                for freq in element.findall('poly_type_mc_freq'):
                    text = freq.text.strip().split()
                    for val in text:
                        val = int(val)
                        if val < 1:
                            raise RuntimeError("The mobility/poly_type_mc_freq must not contain values smaller 1, but got "+str(val))
                        tmp_freq_array.append(val)


            if self.type == MobilityDict["MULLER_SMITH_MOBILITY"]:
                if len(self.param) != 2*ntypes:
                    raise RuntimeError("MULLER_SMITH_MOBILITY require 2*ntypes parameter, but got "+str(len(self.param),ntypes))

            if self.type == MobilityDict["TANH_MOBILITY"]:
                if len(self.param) != 2*ntypes + ntypes**2:
                    raise RuntimeError("TANH_MOBILITY requires 2*ntypes + ntypes^2 paramters, but got "+str(len(self.param), types))

            if len(self.param) == 0:
                self.param = None
            else:
                self.param = numpy.asarray(self.param,dtype=soma_type.get_soma_scalar_type())

            if len(tmp_freq_array) != 0:
                if len(tmp_freq_array) != n_poly_types:
                    raise RuntimeError("Invalid number of poly_type_mc_freq in mobility_modifier. Must match the number of polymer types."+str( (len(tmp_freq_array),n_poly_types) ) )
                self.poly_type_mc_freq = numpy.asarray(tmp_freq_array,dtype=numpy.uint32)
            if 0 in self.poly_type_mc_freq:
                raise RuntimeError("The mobility/poly_type_mc_freq must not contain a 0. The min value is 0.")



    ## Create the external field.
    ## @return external field array
    def create_external_field(self):
        child_list = []
        knownTags = ["point_cloud","box","cylinder","sphere","time"]
        for element in self.root.iter('external_field'):
            for child in element:
               # if child.tag == "time":
               #     for grandchild in child:
               #         tmp_file = stringio.StringIO(grandchild.text)
               #         array = numpy.loadtxt( tmp_file, dtype=numpy.float32)

               #         here = AnaGen.AnaElement( soma_type.get_soma_scalar_type(), (0,array.size), 0 )
               #         self.conf_dict["dynamical_structure_factor"] = copy.deepcopy(here)
               #         child.attr[grandchild.tag] = array
               #         child.attr["length"]=array.size

                if not child.tag in knownTags:
                    print("WARNING: unknown tag ("+child.tag+") found in external_field xml. Value will be ignored. Typo?")

            for pc in element.findall('point_cloud'):
                child_list.append( PointCloud(pc,self.n_types[0]) )

            for box in element.findall('box'):
                child_list.append( Box(box,self.n_types[0]) )

            for cy in element.findall('cylinder'):
                child_list.append( Cylinder(cy,self.n_types[0]) )

            for sp in element.findall('sphere'):
                child_list.append( Sphere(sp,self.n_types[0]) )


        tmp = False
        if len(child_list) > 0:
            tmp = numpy.zeros((self.n_types[0],self.nxyz[0],self.nxyz[1],self.nxyz[2]),dtype=soma_type.get_soma_scalar_type())
            for child in child_list:
                for k in child.get_keys():
                    (x,y,z) = k
                    if not self.args['external_field_no_pbc']:
                        (xa,ya,za) = (k[0] % self.nxyz[0],k[1] % self.nxyz[1],k[2] % self.nxyz[2])
                    else:
                        (xa,ya,za) = (x,y,z)

                    if xa >= 0 and xa < self.nxyz[0] and ya >= 0 and ya < self.nxyz[1] and za >= 0 and  za < self.nxyz[2]:
                        for t in range(self.n_types[0]):
                            tmp[t][xa][ya][za] += child.get( (x,y,z) )[t]


        return tmp

    ## Create the string field.
    ## @return string field array
    def create_umbrella_field(self):
        child_list = []
        knownTags = ["point_cloud","box","cylinder","sphere"]
        for element in self.root.iter('umbrella_field'):
            for child in element:
                if not child.tag in knownTags:
                    print("WARNING: unknown tag ("+child.tag+") found in umbrella_field xml. Value will be ignored. Typo?")

            for pc in element.findall('point_cloud'):
                child_list.append( PointCloud(pc,self.n_types[0]) )

            for box in element.findall('box'):
                child_list.append( Box(box,self.n_types[0]) )

            for cy in element.findall('cylinder'):
                child_list.append( Cylinder(cy,self.n_types[0]) )

            for sp in element.findall('sphere'):
                child_list.append( Sphere(sp,self.n_types[0]) )


        tmp = False
        if len(child_list) > 0:
            tmp = numpy.zeros((self.n_types[0],self.nxyz[0],self.nxyz[1],self.nxyz[2]),dtype=soma_type.get_soma_scalar_type())
            for child in child_list:
                for k in child.get_keys():
                    (x,y,z) = k
                    if not self.args['umbrella_field_no_pbc']:
                        (xa,ya,za) = (k[0] % self.nxyz[0],k[1] % self.nxyz[1],k[2] % self.nxyz[2])
                    else:
                        (xa,ya,za) = (x,y,z)

                    if xa >= 0 and xa < self.nxyz[0] and ya >= 0 and ya < self.nxyz[1] and za >= 0 and  za < self.nxyz[2]:
                        for t in range(self.n_types[0]):
                            tmp[t][xa][ya][za] += child.get( (x,y,z) )[t]


        return tmp


    ## Create the hamiltonian hdf5 field
    ## @return hamiltonian data array
    def create_hamiltonian(self):
        string = ""
        tmp = numpy.zeros((1,),dtype=numpy.int32)
        tmp[0] = hamiltonDict["SCMF0"]
        for element in self.root.iter('hamiltonian'):
            string += element.text.upper()
        string = string.strip()
        if len(string) > 0:
            assert (string in hamiltonDict.keys()),"ERROR: unkown hamiltonian "+str(string)+" requested. Options are: "+str(hamiltonDict.keys())
            tmp[0] = hamiltonDict[string]
        return tmp


#Late import of the module to compensate circular imports.
import AnaGen
## Run the conversion of an input xml file according to arguments. For more details run ./ConfGen.py --help
##
## @param argv Argument vector to parse.
## @return Errorcode
def main(argv):
    parser = argparse.ArgumentParser(description="Script to create SOMA h5 input files from a given SOMA xml file.")
    parser.add_argument('-i',metavar='input_file',type=str,nargs=1,required=True,help="Input SOMA xml file.")
    parser.add_argument('-o',metavar='output_file',type=str,nargs=1,help="Name of the output file. Will be  overwritten.")
    parser.add_argument('--no-hdf5-output',action="store_true",help="Do not generate an ouput hdf5 file, but parse the input and print out user info (if not suppressed).",default=False)
    parser.add_argument('--no-user-output',action="store_true",help="Suppress user ouput.",default=False)
    parser.add_argument('--update',action="store_true",help="Update an existing hdf5 configuration file instead of creating a new one. You are responsible, that the update is applicaple to the existing configuration.")
    parser.add_argument('--dot-graph',action="store_true",help="Print string representation of the Molecules for the \"dot\" tool of the Graphviz package.")
    parser.add_argument('--ana-filename',metavar='ana filename',type=str,nargs=1,required=False,help="Output filename of the analysis hdf5 file.")
    parser.add_argument('--no-ana-output',action="store_true",help="Do not write an hdf5 analysis file.",default=False)
    parser.add_argument('--area51-no-pbc',action="store_true",help="Define that Area51 GridObjects are not folded with the periodic boundary conditions. Grid sites outside the simulation box are ignored.",default=False)
    parser.add_argument('--external-field-no-pbc',action="store_true",help="Define that External_Field GridObjects are not folded with the periodic boundary conditions. Grid sites outside the simulation box are ignored.",default=False)
    parser.add_argument('--umbrella-field-no-pbc',action="store_true",help="Define that Umbrella_Field GridObjects are not folded with the periodic boundary conditions. Grid sites outside the simulation box are ignored.",default=False)


    arguments = vars(parser.parse_args())

    filename = arguments['i'][0]
    extension = filename.rfind(".xml")
    if extension < 0 or extension+len(".xml") != len(filename):
        print("ERROR: "+filename+" does not end with .xml")
        return
    if arguments['o']:
        outfile = arguments['o'][0]
        extension = outfile.rfind(".h5")
        if extension < 0 or extension+len(".h5") != len(outfile):
            print("ERROR: "+outfile+" does not end with .h5")
            return
    else:
        outfile = filename[:extension]+".h5"

    ana_out_file = filename[:extension]+"_ana.h5"
    if arguments["ana_filename"] :
        ana_out_file = arguments["ana_filename"][0]

    #Parse the configuration file
    conf = Configuration(filename,arguments)

    if not arguments['no_user_output']:
        print("Type Table:\nName\tParticleType\tHalfBondType")
        print(conf.types)
        print("Interaction Matrix:")
        print(conf.interaction.get_interaction_matrix())

        if arguments['dot_graph']:
            for i in range(len(conf.molecule_set_list)):
                ms = conf.molecule_set_list[i]
                print(ms.mol.get_dot_graph("Molecule"+str(i),conf.interaction))

    if not arguments['no_hdf5_output'] and not arguments['update']:
        conf.write_hdf5(outfile)

    if not arguments['no_hdf5_output'] and arguments['update']:
        conf.update_hdf5(outfile)

    analysis = AnaGen.AnalysisFile(outfile,filename)
    if not arguments['no_ana_output']:
        analysis.write_hdf5(ana_out_file)

if __name__ == "__main__":
    main(sys.argv)

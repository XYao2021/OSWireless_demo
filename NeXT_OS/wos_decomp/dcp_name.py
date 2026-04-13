#######################################################
# Date: 03/19/2016
# Author: Zhangyu Guan
# Project Manager: Tommaso Melodia, Zhangyu Guan
# Name space of c2d decomposition
#######################################################

#------------------------------------------
#             general
#------------------------------------------
prefix  =   '__'                        # prefix
suffix  =   '___'                       # suffix

zflen   =   2                           # the fixed length of string index

#------------------------------------------
#             set of members
#------------------------------------------

# Selecting 10 from 20 yields 184756 different combinations
# with around 97% probability, a unique combination can be generated with shuffle()
allnum = 20                             # the maximum number of members in set
subnum = 10                             # number of member in a subset
singlenum = 1                           # number of single element (e.g., network)  

#------------------------------------------
#             NUM
#------------------------------------------
xpd     =       'xpd'                   # expanded NUM problem
cstr    =       'cstr'                  # constraint
xpdutlt =       'xpdutlt'               # expanded utility
inst    =       'inst'                  # instance
generator =     'generator'             # generator
set     =       'set'                   # set

#------------------------------------------
#             member type (mt)
#------------------------------------------
mt_subset  = 'mt_subset'                # member type: subset

#------------------------------------------
#             vertical decomposition
#------------------------------------------
sym             =   'sym'                       # indication of symbolic domain
inst_sym        =   'inst_sym'                  # instance in symbolic domain
dualcoef        =   'dualcoef'                  # dual coefficient
lbd             =   'lbd'                       # labmda
vsub            =   'vsub'                      # vertical subproblem
hsub            =   'hsub'                      # horizontal subproblem
hcls            =   'hcls'                      # suffix of hsub class name

#------------------------------------------
#             protocol layer
#------------------------------------------
phy             =   'phy'                       # physical layer
tspt            =   'tspt'                      # transport layer


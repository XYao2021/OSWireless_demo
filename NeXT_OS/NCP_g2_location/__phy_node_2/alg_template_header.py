
#######################################################
# Automatically Generated Solution Algorithm
#------------------------------------------------------
#[[[cog
#   import cog, datetime
#   cog.outl("# Code Date: %s" % datetime.datetime.now())
#]]]
#[[[end]]]
# Author: Zhangyu Guan
#######################################################

#Add the path for Lagrangian coefficients and network parameters
from __future__ import absolute_import
import sys
import net_name

sys.path.insert(0, '../NeXT-OS/wos-network')

#Insert the path of the algorithm
#[[[cog
#   import __alg_name
#   cog.outl("sys.path.insert(0, '%s')"%__alg_name.algo_name)
#]]]
#[[[end]]]

# Import optimization module
from scipy.optimize import minimize
from numpy import *

# Import Lagrangian coefficients and network parameters
#[[[cog
#   import cog, datetime
#   import __alg_name
#   cog.outl("from __lag_in_%s import *"%__alg_name.hid)
#   cog.outl("from __net_para_%s import *"%__alg_name.hid)
#]]]
#[[[end]]]




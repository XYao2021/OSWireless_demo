#######################################################
# Automatically Generated Penalization Algorithm
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
from numpy import *

#Insert the path of the algorithm
#[[[cog
#   import __alg_name
#   cog.outl("sys.path.insert(0, '%s')"%__alg_name.algo_name)
#]]]
#[[[end]]]

# Import parameters involved in this penalization term
#[[[cog
#   import cog, __alg_name 
#   cog.outl("from __lag_in_%s import *" % __alg_name.hid)
#   cog.outl("from __net_para_%s import *" % __alg_name.hid)
#]]]
#[[[end]]]

def calc_pnl():
    # Calculate the penalization term
    #[[[cog
    #   import cog, pnl_term 
    #   cog.outl("pnl_val = %s" % pnl_term.value)
    #]]]
    #[[[end]]]
    return pnl_val



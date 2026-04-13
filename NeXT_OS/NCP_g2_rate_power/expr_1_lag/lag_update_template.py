############################################################
# Automatically Generated Solution Algorithm
#------------------------------------------------------
#[[[cog
#   import cog, datetime
#   cog.outl("# Code Date: %s" % datetime.datetime.now())
#]]]
#[[[end]]]
# Author: Zhangyu Guan
############################################################
from __future__ import absolute_import
import sys
sys.path.insert(0, '../NeXT-OS/wos-network')

#Insert the path of the algorithm
#[[[cog
#   import lag_name
#   cog.outl("sys.path.insert(0, '%s')"%lag_name.alg_name)
#]]]
#[[[end]]]

# Lag parameters for updating Lagrangian coefficient
#[[[cog
#       import cog
#       import lag_name
#       cog.outl('from __lag_para_%s import *'%lag_name.value)
#]]]
#[[[end]]]

# Network parameters for updating Lagrangian coefficient
#[[[cog
#       import cog
#       import lag_node
#       cog.outl('from __net_para_%s import *'%lag_node.value)
#]]]
#[[[end]]]

def call_back():
    #[[[cog
    #       import cog, lag_der
    #       cog.outl('var_term = %s'%lag_der.value)
    #]]]
    #[[[end]]]
 
    new_lag = cur_val + lag_step * var_term
    
    new_lag = max(new_lag, 0)
    
    return new_lag
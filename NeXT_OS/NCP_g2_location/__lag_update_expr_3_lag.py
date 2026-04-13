############################################################
# Automatically Generated Solution Algorithm
#------------------------------------------------------
# Code Date: 2023-07-12 13:02:29.009446
# Author: Zhangyu Guan
############################################################
from __future__ import absolute_import
import sys
sys.path.insert(0, '../NeXT-OS/wos-network')

#Insert the path of the algorithm
sys.path.insert(0, '../NeXT-OS/NCP-g2_location')

# Lag parameters for updating Lagrangian coefficient
from __lag_para_expr_3_lag import *

# Network parameters for updating Lagrangian coefficient
from __net_para_node_2 import *

def call_back():
    var_term = ((ssrate_session_0)-lkcap_link_2)
 
    new_lag = cur_val + lag_step * var_term
    
    new_lag = max(new_lag, 0)
    
    return new_lag
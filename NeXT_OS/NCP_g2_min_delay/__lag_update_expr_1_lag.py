############################################################
# Automatically Generated Solution Algorithm
#------------------------------------------------------
# Code Date: 2023-07-12 13:02:07.320599
# Author: Zhangyu Guan
############################################################
from __future__ import absolute_import
import sys
sys.path.insert(0, '../NeXT-OS/wos-network')

#Insert the path of the algorithm
sys.path.insert(0, '../NeXT-OS/NCP-g2_min_delay')

# Lag parameters for updating Lagrangian coefficient
from __lag_para_expr_1_lag import *

# Network parameters for updating Lagrangian coefficient
from __net_para_src import *

def call_back():
    var_term = ((theta_0_0)-lkcap_link_0 - ssrate_session_0)
 
    new_lag = cur_val + lag_step * var_term
    
    new_lag = max(new_lag, 0)
    
    return new_lag
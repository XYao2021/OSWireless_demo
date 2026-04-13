#######################################################
# Automatically Generated Penalization Algorithm
#------------------------------------------------------
# Code Date: 2025-05-12 15:57:53.054733
# Author: Zhangyu Guan
#######################################################

from __future__ import absolute_import
import sys, os, inspect

sys.path.append("../")
sys.path.append("../wos_dir/")
sys.path.append("../wos_network/")
sys.path.append("../../")
sys.path.append("../../NeXT_PPS")
sys.path.append("../../../")

sys.path.insert(0, '../wos_network')
sys.path.insert(0, '../wos_dir')
sys.path.insert(0, '../../NeXT_PPS')

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))

sys.path.insert(0, parent_dir + '\OSW_G2_elmtlib\element_library')

#Add the path for Lagrangian coefficients and network parameters
# from __future__ import absolute_import
import sys
import net_name_g2
sys.path.insert(0, '../NeXT_OS/wos_network')
from numpy import *

#Insert the path of the algorithm
sys.path.insert(0, '../NeXT_OS/NCP_g2_rate_power')

# Import parameters involved in this penalization term
from __lag_in_node_0 import *
from __net_para_node_0 import *

def calc_pnl():
    # Calculate the penalization term
    pnl_val = expr_1_lag*lkgain_link_0*lkpwr_link_0/(lkitf_link_0**2*(lkgain_link_0*lkpwr_link_0/lkitf_link_0 + 1)*log(2))
    return pnl_val



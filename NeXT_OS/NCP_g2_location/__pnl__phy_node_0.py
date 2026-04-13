#######################################################
# Automatically Generated Penalization Algorithm
#------------------------------------------------------
# Code Date: 2023-07-12 13:02:25.986279
# Author: Zhangyu Guan
#######################################################

#Add the path for Lagrangian coefficients and network parameters
from __future__ import absolute_import
import sys
import net_name
sys.path.insert(0, '../NeXT-OS/wos-network')
from numpy import *

#Insert the path of the algorithm
sys.path.insert(0, '../NeXT-OS/NCP-g2_location')

# Import parameters involved in this penalization term
from __lag_in_node_0 import *
from __net_para_node_0 import *

def calc_pnl():
    # Calculate the penalization term
    pnl_val = [[expr_1_lag*lkpwr_link_0*(4*coord_x_link_0 - 4*fx_crd_x_link_0)/(lkitf_link_0**2*(1 + lkpwr_link_0/(lkitf_link_0*((coord_x_link_0 - fx_crd_x_link_0)**2 + (coord_y_link_0 - fx_crd_y_link_0)**2)**2))*((coord_x_link_0 - fx_crd_x_link_0)**2 + (coord_y_link_0 - fx_crd_y_link_0)**2)**3*log(2)) - expr_1_lag*lkpwr_link_0**2*(4*coord_x_link_0 - 4*fx_crd_x_link_0)/(lkitf_link_0**3*(1 + lkpwr_link_0/(lkitf_link_0*((coord_x_link_0 - fx_crd_x_link_0)**2 + (coord_y_link_0 - fx_crd_y_link_0)**2)**2))**2*((coord_x_link_0 - fx_crd_x_link_0)**2 + (coord_y_link_0 - fx_crd_y_link_0)**2)**5*log(2))],[expr_1_lag*lkpwr_link_0*(4*coord_y_link_0 - 4*fx_crd_y_link_0)/(lkitf_link_0**2*(1 + lkpwr_link_0/(lkitf_link_0*((coord_x_link_0 - fx_crd_x_link_0)**2 + (coord_y_link_0 - fx_crd_y_link_0)**2)**2))*((coord_x_link_0 - fx_crd_x_link_0)**2 + (coord_y_link_0 - fx_crd_y_link_0)**2)**3*log(2)) - expr_1_lag*lkpwr_link_0**2*(4*coord_y_link_0 - 4*fx_crd_y_link_0)/(lkitf_link_0**3*(1 + lkpwr_link_0/(lkitf_link_0*((coord_x_link_0 - fx_crd_x_link_0)**2 + (coord_y_link_0 - fx_crd_y_link_0)**2)**2))**2*((coord_x_link_0 - fx_crd_x_link_0)**2 + (coord_y_link_0 - fx_crd_y_link_0)**2)**5*log(2))]]
    return pnl_val




#######################################################
# Automatically Generated Solution Algorithm
#------------------------------------------------------
# Code Date: 2025-05-12 15:57:52.999545
# Author: Zhangyu Guan
#######################################################

#Add the path for Lagrangian coefficients and network parameters
from __future__ import absolute_import
import sys
import net_name_g2

sys.path.insert(0, '../NeXT-OS/wos-network')

#Insert the path of the algorithm
sys.path.insert(0, '../NeXT-OS/NCP-g2_rate_power')

# Import optimization module
from scipy.optimize import minimize
from numpy import *

# Import Lagrangian coefficients and network parameters
from __lag_in_node_0 import *
from __net_para_node_0 import *




########################################################
#              Define Objective Function
########################################################
def func(objvar, sign=-1.0):
	utlt = -expr_1_lag*log(lkgain_link_0*objvar/lkitf_link_0 + 1)/log(2)
	pnl = - sum(pnl_coefficient*(lkpwr_link_0 - objvar))
	ovl_utlt = utlt + pnl
	return ovl_utlt

########################################################
#                    Constraints
########################################################
cons = (
{'type': 'ineq',
'fun':lambda objvar: objvar - net_name_g2.lkpwr_lwr_default},
{'type': 'ineq',
'fun':lambda objvar: net_name_g2.lkpwr_upr_default - objvar})

########################################################
#                    Optimization
########################################################
def wnos_optimize():
    result = minimize(func, net_name_g2.lkpwr_lwr_default, constraints=cons, method='SLSQP', options={'disp': False})
    return result


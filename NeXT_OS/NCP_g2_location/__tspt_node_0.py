
#######################################################
# Automatically Generated Solution Algorithm
#------------------------------------------------------
# Code Date: 2023-07-12 13:02:25.339375
# Author: Zhangyu Guan
#######################################################

#Add the path for Lagrangian coefficients and network parameters
from __future__ import absolute_import
import sys
import net_name

sys.path.insert(0, '../NeXT-OS/wos-network')

#Insert the path of the algorithm
sys.path.insert(0, '../NeXT-OS/NCP-g2_location')

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
	utlt = expr_1_lag*objvar + expr_2_lag*objvar + expr_3_lag*objvar - log(objvar)
	pnl = - sum(pnl_coefficient*(ssrate_session_0 - objvar))
	ovl_utlt = utlt + pnl
	return ovl_utlt

########################################################
#                    Constraints
########################################################
cons = (
{'type': 'ineq',
'fun':lambda objvar: objvar - net_name_g2.ssrate_lwr_default},
{'type': 'ineq',
'fun':lambda objvar: net_name_g2.ssrate_upr_default - objvar})

########################################################
#                    Optimization
########################################################
def wnos_optimize():
    result = minimize(func, net_name_g2.ssrate_lwr_default, constraints=cons, method='SLSQP', options={'disp': False})
    return result


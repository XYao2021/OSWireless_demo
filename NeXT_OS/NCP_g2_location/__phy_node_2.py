
#######################################################
# Automatically Generated Solution Algorithm
#------------------------------------------------------
# Code Date: 2023-07-12 13:02:26.722586
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
from __lag_in_node_2 import *
from __net_para_node_2 import *




########################################################
#              Define Objective Function
########################################################
def func(objvar, sign=-1.0):
	utlt = -expr_3_lag*log(1 + lkpwr_link_2/(lkitf_link_2*((objvar[0] - fx_crd_x_link_2)**2 + (objvar[1] - fx_crd_y_link_2)**2)**2))/log(2)
	pnl = - sum(sum(pnl_coefficient, axis = 1)*(np.array([coord_x_link_2, coord_y_link_2]) - np.array([objvar[0], objvar[1]])))
	ovl_utlt = utlt + pnl
	return ovl_utlt

########################################################
#                    Constraints
########################################################
cons = (
{'type': 'ineq',
'fun':lambda objvar: objvar - net_name_g2.coord_x_lwr_default},
{'type': 'ineq',
'fun':lambda objvar: net_name_g2.coord_x_upr_default - objvar})

########################################################
#                    Optimization
########################################################
def wnos_optimize():
    result = minimize(func, [net_name_g2.coord_x_lwr_default, net_name_g2.coord_y_lwr_default], constraints=cons, method='SLSQP', options={'disp': False})
    return result


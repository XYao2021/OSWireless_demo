#######################################################
# Automatically Generated Soultion Algorihtm
#------------------------------------------------------
# Code Date: 2020-02-18 01:13:54.467983
# Author: Zhangyu Guan, Tommaso Melodia
# Project Manager: Tommaso Melodia
#######################################################

# Configure directory
import os, sys
p = os.getcwd()										  # Current directory
p = os.path.dirname(p)      						  # Parent directory
sys.path.insert(0, p+'/WNOSPYv2/wos-protocol')        # Directory of protocotols
sys.path.insert(0, p+'/WNOSPYv2/wos-network')         # Directory of network parameters
sys.path.insert(0, p+'/wnospyv2/wos-protocol')        # Directory of protocotols
sys.path.insert(0, p+'/wnospyv2/wos-network')         # Directory of network parameters

# Import protoco-related parameters
import ptcl_name

# Import network-related module
import net_name

# Import optimization module
from scipy.optimize import minimize
from numpy import *

########################################################
#              Define Objective Function
########################################################
def func(opt_var, sign=-1.0):
	return sign*1000*(opt_var*(-sum(ptcl_name.sess_links_lbd)) + log(opt_var))

########################################################
#                    Constraints
########################################################
cons = (
{'type': 'ineq',
'fun':lambda opt_var: opt_var - net_name.rate_lwr_default},
{'type': 'ineq',
'fun':lambda opt_var: net_name.rate_upr_default - opt_var})

########################################################
#                    Optimization
########################################################
def wnos_optimize():
	result = minimize(func, net_name.rate_lwr_default, constraints=cons, method='SLSQP', options={'disp': False})
	print '-1*(' + str(ptcl_name.link_sngl_lbd) + '*log(' + str(ptcl_name.lkgain00) + '*opt_var/(' + str(ptcl_name.lkitf00) + '+' + str(ptcl_name.lknoise00) + ') + 1)/log(2) + (opt_var - ' + str(ptcl_name.lkpwr00) + ') * sum(' + str(ptcl_name.para_pnl) + '))'
	return result

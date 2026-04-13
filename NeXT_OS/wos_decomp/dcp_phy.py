#######################################################
# Date: 03/19/2016
# Author: Zhangyu Guan
# Project Manager: Tommaso Melodia, Zhangyu Guan
# horizontal decomposition for physical layer subproblems
#######################################################

import sys
sys.path.insert(0, './wos-network')

# from external folder
import net_name, net_func

# from local folder
import dcp_name

# from sympy
from sympy import *


def hdcp_vsub(obj_xpd, str_vsub):
    '''
    func: horizontally decmopose a vertical subproblems
    return: generate a set of subproblems, with corresponding objects created and added into xpd 
    obj_xpd: object of the expanded network control problem
    str_vsub: name string of the vertical subproblem
    '''
    
    print('Coming soon...')
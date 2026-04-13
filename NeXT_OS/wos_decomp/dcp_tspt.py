#######################################################
# Date: 03/19/2016
# Author: Zhangyu Guan
# Project Manager: Tommaso Melodia, Zhangyu Guan
# horizontal decomposition for transport layer subproblems
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
    
    # obtain the symbolic network control problem
    obj_vsub = obj_xpd.get_netelmt(str_vsub)   
    symncp = obj_vsub.symexpr    
    symncp = symncp.expand()              # convert to expanded format
    
    # process every component of the symbolic expression    
    #print('Parsing transport layer subproblem...')
    for symexpr in symncp.args:
        #print('\n')        
        #print(x)     
        sys.stdout.write('.')
        sys.stdout.flush()
        alloc_to_sub(obj_xpd, symexpr)    # allocate the symexpr component to a subproblem
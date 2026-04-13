#######################################################
# Date: 07/16/2016
# Author: Zhangyu Guan
# Project Manager: Tommaso Melodia, Zhangyu Guan
# Function: add penalization item to utility 
#######################################################

import sys
sys.path.insert(0, './wos-network')
sys.path.insert(0, './wos-decomp')

# from wos-network
import net_func

# from wos-decomp
import dcp_vps, dcp_name

# from current directory 
import alg_name, alg_lexpr, alg_extnl

# from sympy
from sympy import *

def pnl(obj_lexpr):
    '''
    obj_lexpr: object of the expression
    
    func: add penalization to the utility expression based on polynomial regression
    return: updated utility function
    '''
    
    ## form the penalization expression in string
    
    # mvp: multivarible polynomial model 
    str_pnl = alg_name.mvp
    
    # string to sympy
    sym_pnl = sympify(str_pnl)
    
    # derivative
    sym_pnl_diff = diff(sym_pnl, alg_name.pnlvar)
       
    #add sum() to the penalization item
    str_pnl = sympify('sum(' + str(sym_pnl_diff) + ')')
    
    # update penalization item
    obj_lexpr.idi_pnl  = sympify(str_pnl)
    
    #print(alg_name.stars)
    #print(obj_lexpr.idi_pnl)
    
    
    
    
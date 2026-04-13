#######################################################
# Date: 05/01/2016
# Author: Zhangyu Guan
# Project Manager: Tommaso Melodia, Zhangyu Guan
# main functions for algorithm generation
#######################################################

import sys
sys.path.insert(0, './wos-network')
sys.path.insert(0, './wos-decomp')
sys.path.insert(0, './wos-alglib')

# from wos-network
import net_name

# from wos-decomp
import dcp_name, dcp_xpd

# from wos-alglib
import alglib_main

# from local directory
import alg_func, alg_name, alg_lexpr

def alg(obj_xpd):
    '''
    func: generate numerical solution algorithms for each distributed network control problem
    return: an object containing all informaiton of the algorithms
    obj_xpd: object of the expanded network control problem, containing all horizontal distributed problems
    '''
    
    # creat an object for algorithms
    obj_netalg = alg_func.crt_netalg(obj_xpd)
        
    # Genrate long expressions by wirting out all intermediate expressions, e.g., SINR
    # In the resulting expression, all elements are leaf expression, i.e., expression that cann't 
    # be further expressed using smaller sub-expressions
    alg_lexpr.gen_longexpr(obj_netalg)
    
    # # add penalized item to each horizontal subproblem
    # alg_pnl.add_pnlitem(obj_alg)
    
    # # generate numerical solution algorithms
    # alg_nsl.gen_alg(obj_alg)
    
    # Generate solution algorithm, i.e., executable code to solve the optimization problem
    alglib_main.gnrt_alg_code(obj_netalg)
    
    
    
    
    
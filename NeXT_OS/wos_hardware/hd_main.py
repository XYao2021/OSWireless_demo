#######################################################
# Date: 05/01/2016
# Author: Zhangyu Guan
# Project Manager: Tommaso Melodia, Zhangyu Guan
# main file for network control problem decomposition
#######################################################

import sys
sys.path.insert(0, './wos-network')

# from wos-network
import net_name

def ntwk_opt(ntwk, operation):
    '''
    bridge function of functions in this folder (wos-decomp) and funtions in other folders
    '''
    if operation == net_name.max:
        ntwk_max(ntwk)
    elif operation == net_name.min:
        ntwk_min(ntwk)
    else:
        print('Error: Undefined network operation!')
        exit(0)
        

def ntwk_min(ntwk):
    '''
    minimize network utility
    '''
    print('Minimization currently not supported!')
    exit(0)
    
def ntwk_max(ntwk):
    '''
    maximize network utility
    '''    
    print('Maximization currently not supported!')
    exit(0)    
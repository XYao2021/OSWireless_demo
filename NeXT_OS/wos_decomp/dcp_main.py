#######################################################
# Date: 05/01/2016
# Author: Zhangyu Guan
# Project Manager: Tommaso Melodia, Zhangyu Guan
# main file for network control problem decomposition
#######################################################

import sys
sys.path.insert(0, './wos-network')
sys.path.insert(0, './wos-algorithm')

# from wos-network
import net_name

# from wos-algorithm
import alg_main

# from local folder
import dcp_name, dcp_xpd, dcp_vdcp, dcp_hdcp

def numdcp(ntwk):
    '''
    NUM problem decomposition
    ntwk: network object
    '''
    print('\nDecomposing centralized network control problem into distributed ones...')  
    #print('Generating expanded NUM...')
    
    # generate an expanded NUM problem
    obj_xpd = dcp_xpd.gen_xpd(ntwk)
    
    #exit(0)

    # vertical decomposition
    #print('Starting vertical decomposition...')
    #print('Entering symbolic domain...')        
    dcp_vdcp.vdcp(obj_xpd)
        
    # horizontal decomposition
    #print('Starting horizontal decomposition...')
    dcp_hdcp.hdcp(obj_xpd)

    #exit(0)
   
    # call algorithms generation functions
    print('\n\nGenerating numerical distributed solution algorithms...')
    alg_main.alg(obj_xpd)
   
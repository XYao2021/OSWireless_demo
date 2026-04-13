#######################################################
# Date: 04/12/2017
# Author: Zhangyu Guan
# Project Manager: Tommaso Melodia, Zhangyu Guan
#
# Module description: Algorithm library used to generate optimization algorithms automatically. 
# This module is different from wos-algorithm, which defines expressions of distributed
# network control problems and signalling; this module defines the template of solution algorithm
#
# The eventual outcome of this module is a set of solution algorithms that can be complied and run immediately
#######################################################

import sys
sys.path.insert(0, './wos-network')
sys.path.insert(0, './wos-decomp')
sys.path.insert(0, './wos-algorithm')

# from wos-network
import net_name

# from wos-decomp
import dcp_name, dcp_xpd

# from current folder
import alglib_name, alglib_func

import time

def gnrt_alg_code(obj_netalg):
    '''
    func: generate the code of numerical solution algorithms for each distributed network control problem
      
    obj_netalg: network algorithm object containing obj_xpd with long expression for each optimization problem
       
    Return: generated executable code for solution algorithm of each optimization problem
    '''
    
    ######################################################################
    # Test code: display all subproblems to prepare for loop
    # pass
    ######################################################################
       
    # A loop generating algorithm code for a subproblem in each iteration 
    # before looping, reset index of current suproblem 
    obj_netalg.reset_hsub_index()  
    print('Distributed optimization algorithms generated:\n')
    while True:
        ##################################################################
        # Get next subproblem for which the algorithm code will be generated
        # For the returned subproblem, a code template object has been created,
        # and the next step job is to complete information of the code tempalte
        obj_subprob = alglib_func.get_next_subprob(obj_netalg)
        if obj_subprob == None:
            # The last subproblem has been processed, terminate loop
            
            # Time when algorithm generation is finished
            finish_time = time.time()
            print('Time Elapsed:', finish_time - net_name.start_time, 'seconds')
            
            break
        
        #print('Debug:')
        #obj_subprob.code.ping()
        #exit(0)                 
        
        #print('Debug:')
        #print(obj_subprob.code.alg_name)
        #exit(0)
        
        ##################################################################
        # Generate algorithm code
        #print('Starting to generate solution algroithm...')
        obj_subprob.gnrt_alg()
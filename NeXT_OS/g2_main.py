#######################################################
# OSWireless G2 Demonstration
#######################################################
import time
print('==================================================================================================')
print('Starting GigaOS [OSWireless-G2]...')
##############################################
# Import the required modules
##############################################

# Add search paths
import sys, os, inspect
sys.path.insert(0, './wos-network')
sys.path.insert(0, './wos-ncp')
sys.path.insert(0, './wos-dir')
sys.path.insert(0, '../NeXT-PPS')

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))

sys.path.insert(0, parent_dir+'\OSW_G2_elmtlib\element_library') 

# OSWireless G2 modules
import net_name_g2                            # constant name definitions
from net_ntwk_g2 import new_ntwk_g2           # Network Class
import net_func_g2                            # Basic Network Function Class

from ncp_g2 import ncp_g2 as ncp              # network control problem

import ncp_xlayer_decomp_g2 as xlydcp_g2      # cross-layer decomposition
import ncp_dist_decomp_g2 as dstdcp_g2        # distributed decomposition
import alg_gen_g2 as ag                          # algorithm generation

import mobi_config_g2

import attach_ntwk_elements
import create_connection
import install_model
import constr_exprs
##############################################
# Create network
##############################################

ntwk_type = net_name_g2.adhoc
nt = new_ntwk_g2(ntwk_type)

print('==================================================================================================')
print('Blank "%s" Network Created'%ntwk_type)
print('==================================================================================================')

'''
Attach different network view elements
'''
attach_ntwk_elements.attach_ntwk_elmt(nt)

'''
Creating connections between nodes, links and sessions
'''
create_connection.crt_cnct(nt)

'''
Install models for each network behavioral element
'''
install_model.inst_mdl(nt)

'''
Construct the network control problem
'''

# Create a blank network control problem
nt_ctl = ncp(nt)

'''
Construct expressions
'''
constr_exprs.expr_cnst(nt)
exit()

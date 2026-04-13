#######################################################
# OSWireless G2 Demonstration
#######################################################
import time
print('==================================================================================================')
print('Starting OSWireless-2nd Gen...')
##############################################
# Import the required modules
##############################################

# Add search paths
import sys, os, inspect
sys.path.append("./wos-dir/")
sys.path.append("./wos-ncp/")
sys.path.append("./wos-network/")
sys.path.append("../")
sys.path.append("../NeXT-PPS")
sys.path.append("../../")

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
import netcfg_g2
from ncp_g2 import ncp_g2 as ncp              # network control problem

import ncp_xlayer_decomp_g2 as xlydcp_g2      # cross-layer decomposition
import ncp_dist_decomp_g2 as dstdcp_g2        # distributed decomposition
import alg_gen_g2 as ag                          # algorithm generation
##############################################
# Create network
##############################################

# Create a blank network
ntwk_type = net_name_g2.adhoc
nt = new_ntwk_g2(ntwk_type)

print('==================================================================================================')
print('Blank "%s" Network Created'%ntwk_type)
print('--------------------------------------------------------------------------------------------------')
'''
Attach different network elements
'''
# Adding node network element
nt.attach(net_name_g2.node, 8) 

# Adding link network element
nt.attach(net_name_g2.link, 6)

# Adding session network element
nt.attach(net_name_g2.session, 2)

# Adding antenna network element
nt.attach(net_name_g2.antenna, 0)

'''
Interconnect network elements
'''

antenna_list = nt.get_list(net_name_g2.antenna)

# Connect nodes and links 
link_list = nt.get_list(net_name_g2.link)  
nt.connect('link_0', ['node_0', 'node_1'])
nt.connect('link_1', ['node_1', 'node_2'])
nt.connect('link_2', ['node_2', 'node_3'])
nt.connect('link_3', ['node_4', 'node_5'])
nt.connect('link_4', ['node_5', 'node_6'])
nt.connect('link_5', ['node_6', 'node_7'])


# Conenct links and sessions
session_list = nt.get_list(net_name_g2.session) 
nt.connect('session_0', ['link_0', 'link_1', 'link_2'])
nt.connect('session_1', ['link_3', 'link_4', 'link_5'])

attribute_list = nt.get_list(net_name_g2.attribute)

lkcap_attribute_list = nt.get_list(net_name_g2.lkcap)
lksinr_attribute_list = nt.get_list(net_name_g2.lksinr)
lkinrate_attribute_list = nt.get_list(net_name_g2.lkinrate)
ssdelay_attribute_list = nt.get_list(net_name_g2.ssdelay)
lkdelay_attribute_list = nt.get_list(net_name_g2.lkdelay)

print('--------------------------------------------------------------------------------------------------')
 
    
'''
Attach Model to the attributes
'''
nt.install_model(net_name_g2.lkcap, 'lkcap__micro__script__def')
nt.install_model(net_name_g2.lksinr, 'lksinr__script__def')
nt.install_model(net_name_g2.lkinrate, 'model_1', ['ssrate'])
nt.install_model(net_name_g2.ssdelay, 'model_1', ['lkdelay'])

nt.install_model(net_name_g2.lkdelay, 'script__mm1', ['lkcap', 'lkinrate'])

'''
Construct the network control problem
'''

# Create a blank network control problem
nt_ctl = ncp(nt)
netcfg_g2.ntctl = nt_ctl

for sess in session_list: 
    sessobj = nt.get_netelmt_g2(sess) 

for link in link_list: 
    linkobj = nt.get_netelmt_g2(link)
    linkobj.___lkcap___.para_type = 'leaf_para'

'''
Construct expressions
'''

expr = {'expr_xpd': '', 'expr_ori': ''}

for sess in session_list:                                                # Loop over the session in session list
    ses_rate_expr = nt.get_expr_g2(sess, net_name_g2.ssdelay)               # Get the expression for session delay 
    expr = nt_ctl.mkexpr_new_g2(expr, ses_rate_expr, '+')                 # This is sum of all log session rates
expr_name,info = nt_ctl.record_expr_g2(expr)                             # Record the constructed expression with a unique name


##Add the bounding constraint for session rate

# for sess in session_list: 
    # sess_obj = nt.get_netelmt_g2(sess)
    # nt.add_cstr_g2(sess_obj, 'ssrate_default', net_name_g2.ssrate) #Add constraint (LHS>=RHS - add_cstr_geq)

nt_ctl.ping() 
print('==================================================================')

for link in link_list:
    linkobj = nt.get_netelmt_g2(link)

expr_list = nt_ctl.expr_list

nt_ctl.set_para_g2('expr_0', 'utility')                                             # Set the utility expression
nt_ctl.set_para_g2(expr_list[1:], 'constraint')             # Set the constraint expressions

###############################################
# Vertical decomposition
###############################################
# create a dcp (decomposition) object
vdcp = xlydcp_g2.ncp_xlayer_decomp_g2(nt_ctl)      
vdcp.ping()
#exit()
###############################################
# Horizontal decomposition
###############################################
hdcp = dstdcp_g2.ncp_dist_decomp_g2(vdcp)
hdcp.ping()
#exit()
###############################################
# Set optimization variables
###############################################
nt_ctl.set_para_g2([net_name_g2.ssrate, net_name_g2.lkcap], 'optimization_variables')

###############################################
# Algorithm Generation
###############################################
# configuration for algorithhm generation
ag_cfg = ag.alg_config_g2()
alg = ag.alg_gen_g2(hdcp)
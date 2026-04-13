#######################################################
# OSWireless G2 Demonstration
#######################################################
import time
print('==================================================================================================')
print('Starting OSWireless-2nd Gen with two USRPs...')

##############################################
# Import the required modules
##############################################

# Add search paths
import os, sys, inspect
sys.path.append("./wos-dir/")
sys.path.append("./wos-ncp/")
sys.path.append("./wos-network/")
sys.path.append("../")
sys.path.append("../NeXT-PPS")

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# current_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(current_dir)
# print("current directory:" ,current_dir)
# print("parent directory:" ,parent_dir)

sys.path.insert(0, current_dir+'/OSW_G2_elmtlib/element_library')
# print("Updated sys.path:",sys.path)
# print(os.path.exists(parent_dir + '/OSW_G2_elmtlib/element_library/node.py'))

# OSWireless G2 modules
import net_name_g2                            # constant name definitions
from net_ntwk_g2 import new_ntwk_g2           # Network Class
import net_func_g2                            # Basic Network Function Class

from ncp_g2 import ncp_g2 as ncp              # network control problem

import ncp_xlayer_decomp_g2 as xlydcp_g2      # cross-layer decomposition
import ncp_dist_decomp_g2 as dstdcp_g2        # distributed decomposition
import alg_gen_g2 as ag                       # algorithm generation

# print(f"Using Python interpreter: {sys.executable}")

##############################################
# Create network
##############################################

# Create a blank network
ntwk_type = net_name_g2.adhoc
nt = new_ntwk_g2(ntwk_type)

print("Network type:", ntwk_type,)
# print("Network:", nt)


# # Debugging print statement before attaching elements and check available elements in net_name_g2
# print("Attaching element:", net_name_g2.node)
# print("Defined network elements:", dir(net_name_g2))

print('==================================================================================================')
print('Blank "%s" Network Created'%ntwk_type)
print('--------------------------------------------------------------------------------------------------')

'''
Attach different network elements
'''
# Adding node network element
# nt.attach(net_name_g2.node, 8)
# nt.attach(net_name_g2.mimo_node, 8, addi_info = {'num_ant':2})
# nt.attach(net_name_g2.link, 6)
# nt.attach(net_name_g2.session, 2)
# node_list = nt.get_list('node')

nt.attach(net_name_g2.node, 2)
nt.attach(net_name_g2.link, 1)
nt.attach(net_name_g2.session, 1)

node_list = nt.get_list('node')
print("Node list:",node_list)


print('--------------------------------------------------------------------------------------------------')

antenna_list = nt.get_list(net_name_g2.antenna)
# print("Antenna list:",antenna_list)

# Connect nodes and links 
link_list = nt.get_list('link')
# print("link list:", link_list)

nt.connect('link_0', ['node_0', 'node_1'])
# nt.connect('link_1', ['node_1', 'node_2'])
# nt.connect('link_2', ['node_2', 'node_3'])
# nt.connect('link_3', ['node_4', 'node_5'])
# nt.connect('link_4', ['node_5', 'node_6'])
# nt.connect('link_5', ['node_6', 'node_7'])


# Connect links and sessions
session_list = nt.get_list(net_name_g2.session)

nt.connect('session_0', ['link_0'])
# nt.connect('session_0', ['link_0', 'link_1', 'link_2'])
# nt.connect('session_1', ['link_3', 'link_4', 'link_5'])

attribute_list = nt.get_list(net_name_g2.attribute)

lkcap_attribute_list = nt.get_list(net_name_g2.lkcap)
lksinr_attribute_list = nt.get_list(net_name_g2.lksinr)
    
'''
Attach Model to the attributes
'''

nt.install_model(net_name_g2.lkcap, 'lkcap__micro__script__def')
nt.install_model(net_name_g2.lksinr, 'lksinr__script__def')

'''
Construct the network control problem
'''

# Create a blank network control problem
nt_ctl = ncp(nt)

'''
Construct expressions
'''

expr = {'expr_xpd': '', 'expr_ori': ''}

for sess in session_list:                                                # Loop over the session in session list
    ses_rate_expr = nt.get_expr_g2(sess, net_name_g2.ssrate)             # Get the expression for session rate
    log_ses_expr = nt_ctl.mkexpr_new_g2(ses_rate_expr, 'log')            # This is log of session rate
    expr = nt_ctl.mkexpr_new_g2(expr, log_ses_expr, '+')                 # This is sum of all log session rates
# expr = nt_ctl.mkexpr_new_g2(expr, '(-1)', '*')                           # Obtain A-B using the logic A + B*(-1)
expr_name,info = nt_ctl.record_expr_g2(expr)                             # Record the constructed expression with a unique name


for link in link_list:                                                   # Loop over the links in link list
    lkobj = nt.get_netelmt_g2(link)                                      # Get the link object
    lkcap_expr = nt.get_expr_g2(link, net_name_g2.lkcap)                 # Get the expression for link capacity
    itmd_expr = ''                                                       # Initialize an empty intermediate expression
    for ses in lkobj.session_set:                                        # Loop over the sessions sharing this link
        ses_rate_expr = nt.get_expr_g2(ses, net_name_g2.ssrate)          # Get the expression for session rate
        itmd_expr = nt_ctl.mkexpr_new_g2(itmd_expr, ses_rate_expr, '+')  # Construct an intermediate expr by adding all the session rates
    expr = nt_ctl.mkexpr_new_g2(itmd_expr, lkcap_expr, '-')              # Construct the expression A-B
    expr_name,info = nt_ctl.record_expr_g2(expr, link)                   # Record the constructed expression with a unique name


expr_list = nt_ctl.expr_list


nt_ctl.set_para_g2('expr_0', 'utility')                     # Set the utility expression
nt_ctl.set_para_g2(expr_list[1:], 'constraint')             # Set the constraint expressions
nt_ctl.ping()
#exit()

###############################################
# Vertical decomposition
###############################################
# create a dcp (decomposition) object
vdcp = xlydcp_g2.ncp_xlayer_decomp_g2(nt_ctl)
vdcp.ping()

# print("\nRUN UP TO HERE ??????????----------------------------?????????? RUN UP TO HERE\n")

###############################################
# Horizontal decomposition
###############################################
hdcp = dstdcp_g2.ncp_dist_decomp_g2(vdcp)
hdcp.ping()
#exit()

# print("Run up to here........................")

###############################################
# Set optimization variables
###############################################
nt_ctl.set_para_g2([net_name_g2.ssrate, net_name_g2.lkpwr], 'optimization_variables')

###############################################
# Algorithm Generation
###############################################
# configuration for algorithhm generation
ag_cfg = ag.alg_config_g2()
alg = ag.alg_gen_g2(hdcp)
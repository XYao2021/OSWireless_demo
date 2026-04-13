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


##############################################
# Create network
##############################################

# Create a blank network
ntwk_type = net_name_g2.adhoc
nt = new_ntwk_g2(ntwk_type)

print('==================================================================================================')
print('Blank "%s" Network Created'%ntwk_type)
print('==================================================================================================')

'''
Attach different network elements
'''
# Adding node network element
nt.attach(net_name_g2.node, 8, addi_info={'num_ant':1}) 

# Adding link network element
nt.attach(net_name_g2.link, 6)

# Adding session network element
nt.attach(net_name_g2.session, 2)

# Adding mimo node element
nt.attach(net_name_g2.mimo_node, 10, addi_info={'num_ant':2})
print('--------------------------------------------------------------------------------------------------')

'''
Interconnect network elements
'''
antenna_list = nt.get_list(net_name_g2.antenna)

node_list = nt.get_list('node')

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

print('--------------------------------------------------------------------------------------------------')

attribute_list = nt.get_list(net_name_g2.attribute)

lkcap_attribute_list = nt.get_list(net_name_g2.lkcap)
lksinr_attribute_list = nt.get_list(net_name_g2.lksinr)
lkgain_attribute_list = nt.get_list(net_name_g2.lkgain)
lkdist_attribute_list = nt.get_list(net_name_g2.lkdist)
print('--------------------------------------------------------------------------------------------------')
 
    
'''
Attach Model to the attributes
'''

nt.install_model(net_name_g2.lkcap, 'script__def')
nt.install_model(net_name_g2.lksinr, 'script__def')

############################LINK GAIN#############################################
nt.install_model(net_name_g2.lkgain, 'script__gain__diststr', ['lkdist'])     # Link Gain TYPE 1

for link in link_list:                                                   # Loop over the links in link list
    lkobj = nt.get_netelmt_g2(link)
    lkgain_name = lkobj.___lkgain___.name
    model_parameter_list = []
    lkdistobj = lkobj.___lkdist___
    
############################LINK GAIN#############################################
model_parameter_list = ['coord_x', 'fx_crd_x', 'coord_y', 'fx_crd_y']
nt.install_model(net_name_g2.lkdist, 'script__dist__4coord', model_parameter_list)    # Link Distance TYPE 1

# option 2
for link in link_list:                                                   # Loop over the links in link list
    lkobj = nt.get_netelmt_g2(link)
    lkdist_name = lkobj.___lkdist___.name
    model_parameter_list = []
    coordx1obj = lkobj.___coord_x___
    coordx2obj = lkobj.___fx_crd_x___
    coordy1obj = lkobj.___coord_y___
    coordy2obj = lkobj.___fx_crd_y___
    model_parameter_list.append(coordx1obj)
    model_parameter_list.append(coordx2obj)
    model_parameter_list.append(coordy1obj)
    model_parameter_list.append(coordy2obj)
    #nt.install_model(net_name_g2.lkdist, 'script__dist__4coordobj', model_parameter_list)

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
expr = nt_ctl.mkexpr_new_g2(expr, '(-1)', '*')                           # Obtain A-B using the logic A + B*(-1)
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
 
    
for link in link_list:
    linkobj = nt.get_netelmt_g2(link)
nt_ctl.ping()

expr_list = nt_ctl.expr_list

nt_ctl.set_para_g2('expr_0', 'utility')                                             # Set the utility expression
nt_ctl.set_para_g2(['expr_1', 'expr_2', 'expr_3', 'expr_4', 'expr_5', 'expr_6'], 'constraint')             # Set the constraint expressions

# SET THE EXPANSION FLAG, if true, the dual expression will be expanded if false, the dual expression will be simplified

mobi_config_g2.expansion_flag = False
#exit()
###############################################
# Vertical decomposition
###############################################
# create a dcp (decomposition) object
vdcp = xlydcp_g2.ncp_xlayer_decomp_g2(nt_ctl)      
vdcp.ping()

###############################################
# Horizontal decomposition
###############################################
hdcp = dstdcp_g2.ncp_dist_decomp_g2(vdcp)
hdcp.ping()

###############################################
# Set optimization variables
###############################################
nt_ctl.set_para_g2([net_name_g2.ssrate, net_name_g2.coord_x, net_name_g2.coord_y], 'optimization_variables')

###############################################
# Algorithm Generation
###############################################
# configuration for algorithhm generation
ag_cfg = ag.alg_config_g2()
alg = ag.alg_gen_g2(hdcp)
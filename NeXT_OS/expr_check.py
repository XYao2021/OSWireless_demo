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
# Add specific number of antennas to the node network element
num_antennas = 1
node_list = nt.get_list('node')
for node in node_list:
    new_elmnts_list, all_elmnts_list = nt.attach(net_name_g2.antenna, num_antennas)
    
    # Connect the node network elements and the antenna elements
    nt.connect(node, new_elmnts_list)

antenna_list = nt.get_list('antenna')

# Connect nodes and links 
link_list = nt.get_list('link')  
nt.connect('link_0', ['node_0', 'node_1'])
nt.connect('link_1', ['node_1', 'node_2'])
nt.connect('link_2', ['node_2', 'node_3'])
nt.connect('link_3', ['node_4', 'node_5'])
nt.connect('link_4', ['node_5', 'node_6'])
nt.connect('link_5', ['node_6', 'node_7'])


# Conenct links and sessions
session_list = nt.get_list('session') 
nt.connect('session_0', ['link_0', 'link_1', 'link_2'])
nt.connect('session_1', ['link_2', 'link_3', 'link_4', 'link_5'])

attribute_list = nt.get_list('attribute')
#print('All Attributes List', attribute_list)

lkcap_attribute_list = nt.get_list('lkcap_attribute')
lksinr_attribute_list = nt.get_list('lksinr_attribute')
lkinrate_attribute_list = nt.get_list('lkinrate_attribute')
ssdelay_attribute_list = nt.get_list('ssdelay_attribute')
lkdelay_attribute_list = nt.get_list('lkdelay_attribute')

print('--------------------------------------------------------------------------------------------------')
 
'''
Construct the network control problem
'''

# Create a blank network control problem
nt_ctl = ncp(nt)
netcfg_g2.ntctl = nt_ctl
#print(nt_ctl)

for sess in session_list: 
    sessobj = nt.get_netelmt_g2(sess) 
    #print(sessobj.__dict__)

for link in link_list: 
    linkobj = nt.get_netelmt_g2(link) 
    linkobj.___lkcap___.para_type = 'leaf_para'

'''
Construct expressions
'''

expr = {'expr_xpd': '', 'expr_ori': ''}
'''
Attach Model to the attributes
'''
print('-------------------------------------')
print('Testing Link SINR Expressions')
print('-------------------------------------')
nt.attach_model(lksinr_attribute_list, 'script__def')
for link in link_list:                                                   # Loop over the links in link list
    lksinr_expr = nt.get_expr_g2(link, net_name_g2.lksinr) 
    print(lksinr_expr)
    
print('-------------------------------------')
print('Testing Link Capacity Expressions')
print('-------------------------------------')
nt.attach_model(lkcap_attribute_list, 'default')
for link in link_list:                                                   # Loop over the links in link list
    lkcap_expr = nt.get_expr_g2(link, net_name_g2.lkcap) 
    print(lkcap_expr)

print('-------------------------------------')
print('Testing Link Aggregate Rate Expressions')
print('-------------------------------------')
nt.attach_model(lkinrate_attribute_list, 'script__def')
for link in link_list:                                                   # Loop over the links in link list
    lkinrate_expr = nt.get_expr_g2(link, net_name_g2.lkinrate) 
    print(lkinrate_expr)

print('-------------------------------------')
print('Testing Link Delay Expressions')
print('-------------------------------------')
nt.attach_model(lkdelay_attribute_list, 'script__mm1')
for link in link_list:                                                   # Loop over the links in link list
    lkdelay_expr = nt.get_expr_g2(link, net_name_g2.lkdelay)  
    print(lkdelay_expr)
    
print('-------------------------------------')
print('Testing Session Delay version 1 Expressions')
print('-------------------------------------')
nt.attach_model(ssdelay_attribute_list, 'script__mm1')
for sess in session_list:                                                # Loop over the session in session list
    ses_rate_expr = nt.get_expr_g2(sess, net_name_g2.ssdelay)
    print(ses_rate_expr)

print('-------------------------------------')
print('Testing Session Delay version 2 Expressions')
print('-------------------------------------')
nt.attach_model(ssdelay_attribute_list, 'script__mm1__2')
for link in link_list: 
    linkobj = nt.get_netelmt_g2(link) 
    linkobj.___lkcap___.para_type = 'leaf_para'
for sess in session_list:                                                # Loop over the session in session list
    ses_rate_expr = nt.get_expr_g2(sess, net_name_g2.ssdelay)
    print(ses_rate_expr)

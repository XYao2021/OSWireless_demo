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
nt.attach(net_name_g2.agent, 3) 
# Adding link network element
nt.attach(net_name_g2.link, 4)
# Adding tasks
nt.attach(net_name_g2.task, net_name_g2.num_of_tasks)

# '''
# Interconnect network elements
# '''
nt.connect('link_0', ['agent_0', 'agent_1'])
nt.connect('link_1', ['agent_1', 'agent_2'])


nt.connect('agent_0', nt.get_list('task'))
nt.connect('agent_1', nt.get_list('task'))
nt.connect('agent_2', nt.get_list('task'))


link_list = nt.get_list('link')

nt.install_model(net_name_g2.assign, 'script__util__assign', ['assign'])
nt.install_model(net_name_g2.task, 'script__util__assign', ['task'])

'''
Construct the network control problem
'''

# Create a blank network control problem
nt_ctl = ncp(nt)

'''
Construct expressions
'''

expr = {'expr_xpd': '', 'expr_ori': ''}


# Construct Utility expression
for task in nt.get_list('task'):
    util_expr = nt.get_expr_g2(task, net_name_g2.reward) 
    assign_expr = nt.get_expr_g2(task, net_name_g2.assign)
    assign_util_expr = nt_ctl.mkexpr_new_g2(assign_expr, util_expr, '*') 
    expr = nt_ctl.mkexpr_new_g2(expr, assign_util_expr, '+')         
expr = nt_ctl.mkexpr_new_g2(expr, '(-1)', '*') 
expr_name,info = nt_ctl.record_expr_g2(expr) 

# Construct constraint expressions
# Maximum number of tasks allocated to one agent
for agent in nt.get_list('node'):
    agent_obj = nt.get_netelmt_g2(agent)
    itmd_expr = {'expr_xpd': '', 'expr_ori': ''}
    assign_expr = nt.get_expr_g2(agent, net_name_g2.assign) 
    itmd_expr = nt_ctl.mkexpr_new_g2(itmd_expr, assign_expr, '+')  
    agent_task_limit_name = agent + '_'+ net_name_g2.task_limit
    itmd_expr = nt_ctl.mkexpr_new_g2(itmd_expr, agent_task_limit_name, '-')
    expr_name,info = nt_ctl.record_expr_g2(itmd_expr)  
    setattr(nt, '_'+agent_task_limit_name, agent_obj)
    
# Maximum number of agents a task can be allocated to
for task in nt.get_list('task'):
    task_obj = nt.get_netelmt_g2(task)
    print(task_obj.__dict__)
    itmd_expr = {'expr_xpd': '', 'expr_ori': ''}
    assign_expr = nt.get_expr_g2(task, net_name_g2.assign) 
    itmd_expr = nt_ctl.mkexpr_new_g2(itmd_expr, assign_expr, '+')  
    task_alloc_limit_name = task + '_'+ net_name_g2.task_limit
    itmd_expr = nt_ctl.mkexpr_new_g2(itmd_expr, task_alloc_limit_name, '-')
    expr_name,info = nt_ctl.record_expr_g2(itmd_expr) 
    setattr(nt, '_'+task_alloc_limit_name, task_obj)
    
nt_ctl.ping()

expr_list = nt_ctl.expr_list

nt_ctl.set_para_g2(expr_list[0], 'utility')                                             # Set the utility expression
nt_ctl.set_para_g2(expr_list[1:], 'constraint')             # Set the constraint expressions

net_name_g2.agent_task_flag = True
exit()
###############################################
# Vertical decomposition
###############################################
# create a dcp (decomposition) object
vdcp = xlydcp_g2.ncp_xlayer_decomp_g2(nt_ctl)      
vdcp.ping()
print('--------------------------------------------------------------------------------------------------')

###############################################
# Horizontal decomposition
###############################################
hdcp = dstdcp_g2.ncp_dist_decomp_g2(vdcp)
hdcp.ping()
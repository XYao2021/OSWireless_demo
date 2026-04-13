# Add search paths
import sys
import os
import inspect

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
sys.path.insert(0, parent_dir + '\OSW_G2_elmtlib\element_library')

# Configure directory

p = os.getcwd()  # Current directory
p = os.path.dirname(p)  # Parent directory
sys.path.insert(0, p + '/TBSDN')  # Directory of testbed

# Set initial Lagrangian coefficient for power minimization and rate maximization
# Small value for rate maximization, large value for power minimization
link_sngl_lbd = 3  # Power minimization

# The dictionary is used to record the Lagrangian coefficients received from all links along the path of a session
# Everytime the dictionary is updated, the vector needs to be updated.
#
# Vector of Lagrangian coefficients associated to a session, i.e., received from all links along the session path
sess_links_lbd_dict = {}
sess_links_lbd = [1]

# Channel gain for current link
# Updated in ptcl_func.updt_lnkgain()
lkgain00 = 1

# Link power (transmit gain), updated in ptcl_func.updt_lnkgain()
lkpwr00 = 1

# Interference measured over this link
lkitf00 = 1

# Interference measured at receiver side, will be sent to the corresponding transmitter to update lkitf00
lkitf_rcvr_side = 1

# Noise measured over this link
lknoise00 = 1e-8  # Hard coded, will not be updated

# Transport layer rate
# This rate is used to set netcfg.narrow_rate for TBSDN
# keyword needs to be updated when narrow_rate udpated
narrow_rate = 200000

# Parameters for updating Lagrangian coefficients. Similar to sess_links_lbd and sess_links_lbd_dict, 
# everytime a new parameter is received, para_updt_Lag_dict will be udpated and then para_updt_Lag is
# udpated accordingly
para_updt_Lag_dict = {}
para_updt_Lag = [0]

# Symbolic version of alglib_phypnl.pnl, updated when generating the penalization in alglib_func.gnrt_pnl
# This is not used, since sym_phypnl is used in another separate program TBSDN. 
sym_phypnl = None

# Parameters for penalization
para_pnl_dict = {}
para_pnl = [0]

#############################################
#      Code for messages signaling
#############################################
code_lkitf_rcvr = 1  # Interference measured at receiver side
code_tsmt_gain = 2  # Transmit gain
code_Lagrangian = 3  # Lagrangian coefficient calculated for each link (updated by transmitter of the link)
code_ssrate = 4  # Parameters used to udpate Lagrangian coefficients at each transmitter
code_pnl = 5  # Penalization parameters

# Enalbe DPL-based optimization, configured in wos-demo.py by APIs.   
# 'BR': Best Response
# 'DPL': Decmoposition by Partial Linearization
# price = ['BR', 'DPL']
price = 'DPL'
# price = 'BR'

# Step size for Lagrangian coefficient updating, a small value
Lag_step = 0.3  # Power minimization
# Lag_step = 0.005           # Rate maximization

# Step size for updating transmit gain
# Implemented based on "Decomposition by Partial Linearization: Parallel
# Optimization of Multi-Agent Systems", Scutari, IEEE TSP, 2013.

epsilon = 0.5  # take values from (0, 1)
gamma = 0.1  # Step size initialization
phy_idx = 1  # Iteration index

# Parameters for updating transmission rate
epsilon_tspt = 0.5  # 0.5
gamma_tspt = 1  # 0.1
tspt_idx = 1

# Transport layer rate, in Kbps
tspt_rate = 5
keyword = {'ssrate00': tspt_rate}

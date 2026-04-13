#######################################################
# Name space of network elements and attributes
#######################################################
import sys
outf = open('output.txt','w')

#------------------------------------------
#                 network
#------------------------------------------
ntwk       = 'ntwk'                          # network element
adhoc      = 'Ad Hoc'                        # --- ad hoc network
cell       = 'Cellular'                      # --- cellular network
drone_cell = 'Drone Cellular'                # --- Drone cellular network

#------------------------------------------
#                 general
#------------------------------------------
para       = 'para'                          # parameter element: pwr, rate...
default    = '_default'                      # default parameter
vardb      = 'vardb'                         # refer to the database of variables

if_rgst    = 'if_rgst'                       # whether to register an element in ntwk
yes        = 'yes'                           # yes
no         = 'no'                            # no

all        = 'ALL'                           # to indicate the range of variables: all sessions, all src nodes
mltp       = 'MLTP'                          # >= 1, used when exact number is not known
every      = 'EVERY'                         # keyword: each, representing each network element 
sub        = 'SUB'                           # a subset
single     = 'SINGLE'                        # single network element

hid        = 'hid'                           # horizontal node id, for distributed decomposition

blank_list = '[]'

#------------------------------------------
#                 node
#------------------------------------------
node            = 'node'                     # node element
ndset           = 'ndset'                    # set of all node elements
# src        = 'src'                         # source node
# dst        = 'dst'                         # destination node
# rin        = 'rin'                         # regular intermediate node
node_type  = [node]                          # node type list

ndpwr      = 'ndpwr'                         # trans power
ndlink     = 'ndlink'                        # the links associated to a node

spwr       = 'spwr'                          # src node power

rate       = 'rate'                          # node outgoing rate
srate      = 'srate'                         # src node rate
          
ndfreq     = 'ndfreq'                        # operating frequency (bandwdith)
sfreq      = 'sfreq'                         # src operating frequency (bandwdith)

rin_lbl    = ''                              # label for regular node: empty string
src_lbl    = 's'                             # label for source node    
dst_lbl    = 'd'                             # label for destination node    

#------------------------------------------
#                 link
#------------------------------------------       
lkrcvr     = 'lkrcvr'                        # reciever node of a link
lkcap      = 'lkcap'                         # capacity of link   
lkpwr      = 'lkpwr'                         # link power
lkfrq      = 'lkfrq'                         # frequency used by a link
lksinr     = 'lksinr'                        # link SINR
lktsmt     = 'lktsmt'                        # transmitter of link
lkrcvr     = 'lkrcvr'                        # receiver of link
lkgain     = 'lkgain'                        # link channel gain
lknoise    = 'lknoise'                       # link noise power
lkitf      = 'lkitf'                         # link interference power
lkset      = 'lkset'                         # set of links used by a session
ntlk       = 'ntlk'                          # the set of all links in the network
itfpwr     = 'itfpwr'                        # power of interference link
lkdelay    = 'lkdelay'                         # link delay
lkinrate   = 'lkinrate'                      # link incoming rate
lkoutrate  = 'lkoutrate'                     # link outgoing rate
itflkset   = 'itflkset'                      # the set of interfering links

lkdist = 'lkdist'

#------------------------------------------
#         Logic Link, Jan. 21, 2020
#------------------------------------------
lk_logic        = 'lk_logic'                 # refers to logical link   - added 2020-01
lkset_logic     = 'lkset_logic'              # the set of logic links


#------------------------------------------
#                 session
#------------------------------------------
ses        = 'ses'                           # session element, replaced by ntses; opened to reuse name - 2/2020 AA
'''
 Need session element 'ses' for introducing delay; delay can be defined at the network level.
 A network can have a total delay; a session element has session delay. 
 delay is due to link, a node does not introduce delay
 Every session has links. All the links associated with the session introduces a delay - link_delay
 Then Total delay = sum of all link delay associated with src and dst nodes. 
'''                                       
sess_set   = 'sess_set'                      # set of sessions- not same as ntses
                                              
ntses      = 'ntses'                         # set of sessions in the network 

ssrate     = 'ssrate'                        # session rate
aggr_rate = 'aggr_rate'                      # aggregate incoming rate

ss_prnt_cls = 'session'                  # parent class of one session
lk_prnt_cls = 'link'                    # parent class of one net link

src        = 'src'                           # src of sessions
dst        = 'dst'                           # dst of sessions

tsmt_nd    = 'tsmt_nd'                       # transmit node of a link
rcvr_nd    = 'rcvr_nd'                       # receiver node of a link

sslink     = 'sslink'                        # set of links of a session

ssset      = 'ssset'                         # set of sessions using a link

ssdelay    = 'ssdelay'                       # session delay element

link       = 'link'                          # link element

session    = 'session'                       # session element

antenna    = 'antenna'                       # antenna element

ntlkset    = 'ntlkset'                       # set of links in the network

lkses      = 'lkses'                         # session set associated to a link  

lkses_logic = 'lkses_logic'                  # session associated to a logical link - 02/04/2020
                                             # each session has only 1 logical link

queue = 'queue'
                                           
mimo_node = 'mimo_node'

directional_antenna = 'directional_antenna'

microwave_node = 'microwave_node'
microwave_mimo_node = 'microwave_mimo_node'
microwave_link = 'microwave_link'

sixghz_node = 'sixghz_node'
sixghz_mimo_node = 'sixghz_mimo_node'
sixghz_directional_antenna = 'sixghz_directional_antenna'
sixghz_link = 'sixghz_link'

mmwave_node = 'mmwave_node'
mmwave_mimo_node = 'mmwave_mimo_node'
mmwave_directional_antenna = 'mmwave_directional_antenna'
mmwave_link = 'mmwave_link'

thz_node = 'thz_node'
thz_mimo_node = 'thz_mimo_node'
thz_directional_antenna = 'thz_directional_antenna'
thz_link = 'thz_link'

default = 'default'
coord = 'coord'
coord_x = 'coord_x'
coord_y = 'coord_y'
coord_z = 'coord_z'
fx_crd_x = 'fx_crd_x'
fx_crd_y = 'fx_crd_y'
fx_crd_z = 'fx_crd_z'

attribute = 'attribute'

micro_lkcap = 'micro_lkcap'
 #------------------------------------------
#                 protocol and layer 
#------------------------------------------
# general protocol
ptcl       = 'protocol'

# physical layer
CDMA       = {'name':'cdma', 'layer':'physical', 'alg': None}
phy_list   = [CDMA['name']]                 # list of physical-layer protocols currently supported

# transport layer
TCP_VEGAS  = {'name':'tcp_vgs', 'layer':'transport', 'alg': 'vegas'}                          
tspt_list  = [TCP_VEGAS['name']]            # list of transport-layer protocols currently supported


#session layer
#FIXED_RATE added for session layer using logical links with fixed capacity
FIXED_RATE = {'name':'fixed_rate','layer':'link','alg':None}
sess_list = [FIXED_RATE['name']]


#------------------------------------------
#                 network expressions
#------------------------------------------
expr_db    = 'expr_db'                      # expression data base
expr_hldr  = 'expr_hldr'                    # expression holder
utility    = 'utlt'                         # utility expression
constraint = 'cstr'                         # constraint expression

fmlr       = 'fmlr'                         # formula of expression
varlst     = 'varlst'                       # variable list of expression


#------------------------------------------
#                 network operation
#------------------------------------------
MAX        = 'max'                          # network utility maximization
MIN        = 'min'                          # network utility minimization


#------------------------------------------
#                 fluid model
#------------------------------------------
fldmdl     = 'fldmdl'                       # network fluid model
dtmn       = 'determinstic'                 # determinstic fluid model


#------------------------------------------
#         parameter and variables
#------------------------------------------
leaf_para  = 'leaf_para'                    # leaf parameter, cannot be represented using other parameters
itmd_para  = 'itmd_para'                    # intermediate parameter, needs to be represented by other parameters
xtnl_para  = 'xtnl_para'                    # external parameter
mesr_para  = 'mesr_para'                    # parameter that will be measured on the fly
fit_para   = 'fit_para'                     # parameter whose model will be fitted, e.g., based on learning

# variables can be defined for these network elements; the variable definition function can be generalized
var_hldr_list  = [node, ntses, ndlink]        


#------------------------------------------
#         element relationship
#------------------------------------------         
elmt_asct = 'elmt_asct'                     # network element to which a parameter is associated

#------------------------------------------
#         numbers
#------------------------------------------  
max_exprcnt = 999


#------------------------------------------
#         protocol layer
#------------------------------------------ 
tspt    =   'tspt'                          # transport layer
phy     =   'phy'                           # physical layer
link    =   'link'                          # link layer

# list of all layers, used in dcp_hsub to determine the layer for a subproblem
lst_layer = [tspt, phy]


#------------------------------------------
#         external variable
#------------------------------------------ 
isxtnl     =       'isextnl'                # to mark if an element is external
pre_xtnl   =       '_pxnl_'                 # prefix for external element
suf_xtnl   =       '_sxnl_'                 # suffix for external element


#------------------------------------------
#         variable subtype
#------------------------------------------ 
power = 'power'                             # transmit power. variables belonging to this category include lkpwr, spwr...
rate = 'rate'                               # transmission rate. variables belonging to this category include ssrate...


#------------------------------------------
# variable default lower and upper bounds
#------------------------------------------ 
max_pwr_in_dB = 25.0
min_pwr_in_dB = 5.0
lkpwr_lwr_default = 10 ** (min_pwr_in_dB/10)          		# USRP Transmit Gain ), absolute value
lkpwr_upr_default = 10 ** (max_pwr_in_dB/10)      	        # 2, 15 are in dB

max_rate_in_bps = 200000
min_rate_in_bps = 1000
ssrate_lwr_default = min_rate_in_bps/1000                        		# in kbit/seek
ssrate_upr_default = max_rate_in_bps/1000

ssrate_lwr_default_val = 50
#--------------------------------------------------
# parameters used for defining signaling exchange
#--------------------------------------------------
chngain = 'chngain00'

#--------------------------------------------------
# Support operations
#-------------------------------------------------
# Operation 'dum' does nothing to the optimization variable rather than
# indicating that the variable comes from utility function; 
# Operation 'dum' is inserted when updating utility function and then removed when generating solution algorithm
lst_oper = ['log', 'exp', 'sqrt', 'sin', 'cos', 'dum']

# Control scheme, updated in wos-demo, used in PPS -> netcfg.py
scheme = 2

# Coefficient to avoid errors in solving optimization problem using Python solver
coef = 1000

# Record the starting time of network control problem decomposition
start_time = 0

# List of nodes to load the source
node_list = []


sess_rate_list = {}
sess_rate_list['ses0'] = 1.5
sess_rate_list['ses1'] = 2.5
sess_rate_list['ses2'] = 2
sess_rate_list['ses3'] = 2
sess_rate_list['ses4'] = 2
sess_rate_list['ses5'] = 2
sess_rate_list['ses6'] = 2
sess_rate_list['ses7'] = 2
sess_rate_list['ses8'] = 2
sess_rate_list['ses9'] = 2
sess_rate_list['ses10'] = 2

ssrate_thresh = {}
ssrate_thresh['session_0'] = 1.5
ssrate_thresh['session_1'] = 3
######## addition of new attributes ######

default_val = 'default_val'

##########################################
mm1 = 'mm1'
theta = 'theta'

itmd_vars = {'mm1':'theta'}

intmd_var_dict = {}

#########################################
# Dictionary containing all the NCP names.. This will be used when storing the algorithms
dict_ncp_names_file ={}
dict_ncp_names_file['demo'] = 'rate-power'
dict_ncp_names_file['mindly'] = 'delay'
dict_ncp_names_file['mobi'] = 'mobility'
dict_ncp_names_file['demo1'] = 'g2_rate_power'
dict_ncp_names_file['delay'] = 'g2_min_delay'
dict_ncp_names_file['delay_2'] = 'g2_min_delay'
dict_ncp_names_file['mobile'] = 'g2_location'

dict_ncp_names_file['demo1_func_approx'] = 'g2_rate_power_func_approx'
dict_ncp_names_file['driver_design'] = 'g2_rate_power_func_approx_driver'
########################################
func_approx = 'func_approx'
reinforce = 'rl'
########################################
q_learning = 'q_learning'
sarsa = 'sarsa'
########################################
soln_mthd = {}
soln_mthd['func_approx'] = 'fa'
soln_mthd['rl'] = 'rl'
########################################
coord_dict ={}
coord_dict[0] = [0,0,0]
coord_dict[1] = [1,1,1]
coord_dict[2] = [2,2,2]
coord_dict[3] = [3,3,3]
coord_dict[4] = [4,4,4]
coord_dict[5] = [5,5,5]
coord_dict[6] = [6,6,6]
coord_dict[7] = [7,7,7]
coord_dict[8] = [8,8,8]
coord_dict[9] = [9,9,9]

links = ['link_1_2', 'link_2_3', 'link_3_4', 'link_3_4', 'link_5_7', 'link_8_6', 'link_7_8', 'link_8_6']
coord_list = {'coord_x':'coord_x', 'coord_y':'coord_y'}#, 'coord_z':'coord_z'}
#coord_list2 = {'coord_x':'crd_x', 'coord_y':'crd_y'}#, 'coord_z':'crd_z'}
coord_list2 = {'coord_x':'fx_crd_x', 'coord_y':'fx_crd_y'}#, 'coord_z':'crd_z'}


coord_x_lwr_default = 1
coord_y_lwr_default = 1

coord_x_upr_default = 100
coord_y_upr_default = 100

###########################################
expr = {'expr_xpd': '', 'expr_ori': ''}

net_func_g2 = 'net_func_g2'
netelmt_g2 = 'netelmt_g2'

###########################################
mmwave_lkcap = 'mmwave_lkcap'

###############################################################################
###############################################################################
########################### TASK ALLOCATION PROBLEM ###########################
###############################################################################
###############################################################################
agent = 'agent'
task = 'task'
agent_task_flag = False

util = 'util'
assign = 'assign'
assign2 = 'assign2'

reward = 'reward'

list_hid_change = [agent, task]
num_of_tasks = 4
task_alloc_limit = 'task_alloc_limit'
alloc_limit = 'alloc_limit'
agent_task_limit = 'agent_task_limit'
task_limit = 'task_limit'

driver_plane_filename = 'driver_plane_info.py'

#possible patterns for decomposition

known_pattern_type = {}
known_pattern_type['1/(a - b)'] = {'decomp': 'Indirect',
                                   'type': 'type_1',
                                   'aux': 'theta',
                                   'layer':'tspt'}
                                   
known_pattern_type['1/(-a + log(b*c/d + 1)/log(2))'] = {'decomp': 'Indirect',
                                                        'type': 'type_2',
                                                        'aux': 'theta',
                                                        'layer':'tspt'}
                                   
known_pattern_type['1/(a - b + c)'] = {'decomp': 'Hybrid',
                              'type': 'type_2'}

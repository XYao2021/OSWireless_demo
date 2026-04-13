##! /usr/bin/python
import time
import math
import numpy as np
from random import randint
import socket
import inspect
# from addpath import *

import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
target_folder = os.path.join(project_root, "NeXT_OS")
sys.path.append(target_folder)
target_folder = os.path.join(target_folder, "wos_network")
sys.path.append(target_folder)

import scheme_py
# from Desktop.Research.OS_Wireless.OSWireless_demo.OSWireless_B210.OSW_G2.NeXT_OS import ptcl_name
import ptcl_name  # ptcl_name is in NeXT-OSdirectory
import net_name_g2 as net_name  # net_name_g2.py is in NeXT-OS --> wos-network directory
from network_config import *

options = get_args()

"""--------------------------------- General Parameters --------------------------------"""

nd_id = ['src1', 'rly1', 'dst1']
nd_type = ['tx', 'relay', 'rx']

serial_usrp_src1 = '30CD424'
serial_usrp_rly1 = '30CD3F7'
serial_usrp_dst1 = '3169C62'

ip_usrp = [serial_usrp_src1, serial_usrp_rly1, serial_usrp_dst1]

# Define the IP address separately
IP_PC1 = '127.0.0.1'  # Transmitter PC IP address
IP_PC2 = '127.0.0.1'  # Relay PC IP address
IP_PC3 = '127.0.0.1'  # Receiver PC IP address

# Session 1 PC addresses
ip_pc_src1 = IP_PC1
ip_pc_rly1 = IP_PC2
ip_pc_dst1 = IP_PC3

# 127.0.0.1 for transmitting / 0.0.0.0 for receiving
ip_pc = [ip_pc_src1, ip_pc_rly1, ip_pc_dst1]

udp_port_listen = [5001, 5003, 5005]
udp_port_send = [5000, 5002, 5004]

prev_hop_serial = [None, serial_usrp_src1, serial_usrp_rly1]
prev_hop_usrp = prev_hop_serial
prev_hop_pc = [None, ip_pc_src1, ip_pc_rly1]

next_hop_serial = [serial_usrp_dst1, serial_usrp_dst1, None]  # XY: should be destination USRP?
next_hop_usrp = next_hop_serial
next_hop_pc = [ip_pc_dst1, ip_pc_dst1, None]

serial_to_addr = {serial_usrp_src1: ip_pc_src1, serial_usrp_rly1: ip_pc_rly1, serial_usrp_dst1: ip_pc_dst1}
serial_to_port = {serial_usrp_src1: udp_port_listen[0], serial_usrp_rly1: udp_port_listen[1], serial_usrp_dst1: udp_port_listen[2]}

source_usrp_serial = [None, serial_usrp_src1, serial_usrp_rly1]
source_usrp = source_usrp_serial
source_pc = [None,  ip_pc_src1, ip_pc_rly1]

dest_usrp_serial = [serial_usrp_rly1, serial_usrp_dst1, None]
dest_usrp = dest_usrp_serial
dest_pc = [ip_pc_rly1, ip_pc_dst1, None]

idx_thisnode = None
nodeid = None  # role name

# change this to 0 to mute notes display
disp_note = 0
note1 = 'Next step work: connect correlator blocks; implement CSI collection function; adaptive algorithm.'
note2 = 'In netcfg.py, set disp_note = 0 to run the program.'

tx_time_stamp_dict = {}

"""--------------------------------- Layer 2 Parameters --------------------------------"""

number_of_blocks = 1  # Number of 255 Bytes blocks composing a L2 packet
l2_size_block = 128  # Fixed in Bytes, maximum = 4096/2 = 2048
l2_size = l2_size_block * number_of_blocks
l2_capacity = 0

n_pkt_cnt = 0  # Link Layer (Layer 2) packet counter
l2_th_coeff = 0.75
lnk_thpt = 0.001
l2_retransmission_threshold = 10
timeout_l2 = 10 * number_of_blocks  # time to wait for Layer 2 ACK message

l2_window = [1, 1, 1]

payload_size = None

# point to point PER thresholds
l2_th_PER_low = 0.05  # 0.05
l2_th_PER_high = 0.4  # 0.1

"""--------------------------------- Layer 4 Parameters --------------------------------"""

number_of_frames = 2  # Number of later 2 frames per layer 4 packet has

l4_size = l2_size * number_of_frames  # 256
l4_header_length = 42  # 8 + 13 + 13 + 8
l4_control_rate_flag = 1  # rate limitation 1->limited 0->unlimited

tspt_rate = 256 * 1.9 * 5.1  # 12/11/2017, Guan, in bps -> XY: bits per second?
l4_maximum_rate = tspt_rate / 8  # Bytes per second
l4_maximum_packets_per_second = max(1, int(np.ceil(l4_maximum_rate / l4_size)))

l4_packets_to_send = 10000

# Window size implements sliding window transport layer protocol at sources
l4_window = [6, 6, 1]

l2_header_length = 28  # Was 28: 2 bytes pktno + 13 bytes src + 13 bytes dst
chunk_size = l2_size - l2_header_length  # Called in lyr4.py

# Total number of received packets
n_tot = 0

ack_time_stamp_dict = {}  # This dictionary wll be used to store the timestamp in the ACK

timeout_l4 = timeout_l2 * number_of_frames * number_of_blocks * 2 * 7  # time in second to wait for layer 4 ack

# retransmission limit
l4_retransmission_threshold = 10  # 20

throughput_list = []

"""--------------------------------- Coding rate Parameters --------------------------------"""

ch_coding_rate = [0.14, 0.16, 0.18, 0.20, 0.22, 0.24, 0.20, 0.22, 0.24, 0.26, 0.28, 0.30]

"""--------------------------------- Control Module Parameters --------------------------------"""

tx_gain = 15

# 1 - optimized; 0 - not optimized
b_optpwr = 0
b_optrate = 0

# select control algorithm -> Both are not implemented
# alg = 'JOCP'
alg = 'WNOS'

"""--------------------------------- Channel state Parameters --------------------------------"""

obj_rcvr_blk = None  # set to receiver objective if the receiver is created

# Initialize the channel gain to all zeros
num_node = 3
chn_gain = np.zeros((num_node, num_node))

# Id of nodes: [src1, dst1]
# Row: index of node1, starting from 0
# Column: index of node2, starting from 0
# Example: chn_gain[0, 1] represents the channel gain from src1 to dst1

# Configure the channel gain matrix based on the measured channel gain values
# Need to modify according to the number of nodes we have
chn_gain[0, 2] = 0.0037
chn_gain[1, 1] = chn_gain[0, 2]
chn_gain[2, 0] = chn_gain[0, 2]

chn_idx_thisnode = [1, 2, None]

tx_ampl = 0.8  # transmit amplitude
rx_gain = 10.0  # receiver gain of usrp

# dB -> absolute for UHD gain of USRP
tx_gain_abs = 10 ** (tx_gain / 10)  # transmitter side
rx_gain_abs = 10 ** (rx_gain / 10)  # receiver side

# very small value to approximate 0 in denominator
SMALL_VALUE = 1e-20

sir_thisnode = None  # SIR information measured online, initialized to None
alpha = 0.5  # coefficient of running average

"""--------------------------------- Scheme Parameters --------------------------------"""

scheme = 1

if scheme == 1:
    b_br = 'on'  # br -> best response
    b_pwr_ctl = 'off'
    b_Lag_ctl = 'off'
    b_rate_ctl = b_Lag_ctl

    # Use the maximum power and rate
    tx_gain = net_name.max_pwr_in_dB  # transmit gain of usrp
    tspt_rate = net_name.max_rate_in_bps  # Initial transport layer rate in bps

if scheme == 2:
    b_br = 'off'
    b_pwr_ctl = 'on'
    b_Lag_ctl = 'on'
    b_rate_ctl = b_Lag_ctl

if scheme == 3:
    b_br = 'off'
    b_pwr_ctl = 'off'
    b_Lag_ctl = 'on'
    b_rate_ctl = b_Lag_ctl

if scheme == 4:
    b_br = 'off'
    b_pwr_ctl = 'off'
    b_Lag_ctl = 'off'
    b_rate_ctl = b_Lag_ctl

if scheme == 5:
    b_br = 'off'
    b_pwr_ctl = 'on'
    b_Lag_ctl = 'off'
    b_rate_ctl = b_Lag_ctl

if scheme == 6:
    b_br = 'off'
    b_pwr_ctl = 'on'
    b_Lag_ctl = 'on'
    b_rate_ctl = 'off'

# This scheme can be used to use constant power and rate until the expiration of the corresponding counter. Once the counter expires, the optimization algorithm will be executed.
# The counter for power control is pwr_count and rate_count for rate control
if scheme == 7:
    b_br = 'off'
    b_pwr_ctl = 'on'
    b_Lag_ctl = 'on'
    b_rate_ctl = b_Lag_ctl
    pwr_count = 15
    rate_count = 15

# Delay Minimization Scheme
if scheme == 8:
    b_br = 'off'
    b_pwr_ctl = 'on'
    b_Lag_ctl = 'on'
    b_rate_ctl = b_Lag_ctl
    aux_var = 'theta'
    # step_par = 'constant'
    step_par = 'variable'

# Mobility scheme
if scheme == 9:
    b_br = 'off'
    b_pwr_ctl = 'off'
    b_Lag_ctl = 'off'
    b_rate_ctl = b_Lag_ctl

"""---------------------------------- Signalling Parameters ------------------------------------"""

usrp_serial = [serial_usrp_src1, serial_usrp_rly1, serial_usrp_dst1]

pre_para_pnl_updt_time = -1  # penalization times -> XY: what is this for?

# All USRP serials
all_usrp_serial = [serial_usrp_src1, serial_usrp_rly1, serial_usrp_dst1]
all_usrp_ip = all_usrp_serial  # XY: should this be replaced by the ip list?

# Transmit gain of all transmitters, randomly generated above
# This parameter is used to calculate transmit power and interference
# Updated in running time by signaling exchange
# Transmit gain is set to 0 for destination nodes

tx_gain_allnode = [tx_gain, tx_gain, 0]

# Source USRP serial of sessions
source_usrp_session_serial = [serial_usrp_src1, serial_usrp_src1, serial_usrp_src1]  # XY: Why need this?
source_usrp_session = source_usrp_session_serial

# Serial numbers of sender-type nodes of a session
usrp_serial_sender_of_session = {serial_usrp_src1: [serial_usrp_src1], serial_usrp_rly1: [serial_usrp_rly1]}

values_net_para = {}

# The interference parameters are used in protocol files (ptcl_func and ptcl_name)
#       src1  rly1  dst1
itf_src1 = [0, 0, 0]
itf_rly1 = [0, 0, 0]
itf_dst1 = [0, 0, 0]

# Interference relation matrix
itf_relation = np.matrix([itf_src1, itf_rly1, itf_dst1])

# The following parameters called in the update functions in signalling.py
sess_rate = {}
delay_history = []

itx_pnl = 0

# Map serial to node index
usrp_serial_2_ndidx = {serial_usrp_src1: 0, serial_usrp_rly1: 1, serial_usrp_dst1: 2}

lag_history = []
narrow_rate = ptcl_name.narrow_rate  # transmit rate in bps

# Indication of whether Lagrangian has reached zero. 0: No; 1: Yes
# Updated in signaling.py
b_zero_lag = 0

# Time when node starts to run
time_start = time.time()
prev_time = time_start

pwr_time_history = []  # Record time
pwr_history = [tx_gain]  # Record power

# The initial point for the two counters are initialized
rate_init_counter = 0
pwr_init_counter = 0

rate_list = []

lag_2_dict = False
lag_2_dict2 = False

tspt_flag = False

"""---------------------------------- Protocol Parameters ------------------------------------"""

"""------------------------------- Channel Coding Parameters ----------------------------------"""

# XY: The physical layer packet size in bits -> Need to be replaced
l1_size = int(l2_size_block * (1 + ch_coding_rate[2]) - 1)  # variable, default half l2 packet

"""---------------------------------- Unused Parameters ------------------------------------"""

# # Point to the node object, updated in mynd.py
# thisnode = None
#
# # select physical layer: 'NARROWBAND' or 'OFDM'
# phy = 'NARROWBAND'
# # phy = 'OFDM'
#
# # narrowband parameters: transmitter and receiver must be set for the same parameters
# narrow_modulation = 'gmsk'  # 'bpsk', 'gmsk'
#
# """
# 								Candidate schemes
# 		When the control objective is power minimization, scheme 6 should be used
# 		1: Best Response, use the maximum power and layer-4 transmission rate
# 		2: power and rate control
# 		3: only rate control
# 		4: No Control, fixed power and layer-4 transmission rate
# 		5: only power control
# 		6: For power minimization, without rate control, with power control, with Lagrangian updating
# """
#
#
# index = 0
# opt_val = None
#
# # transmit parameters
# sps = 4  # samples per symbol
#
# # Digital gain of transmitter and receiver, hard coded
# tx_digital_gain = 1  # transmitter digital gain, default 1; seems not being used
# rx_digital_gain = 1  # receiver digital gain, default 1;  seems not being used
#
# # differential modulation or not
# differential = False  # use non_differential modulation to match the preamble correlator at receiver side
#
# "					Channel gain information, measured offline for now								"
#
# # Location of all USRPs
# # Map each USRP to initial location coordinates -> XY: Why there are x, y, z?
#
# location = {serial_usrp_src1: {'x': 0, 'y': 0, 'z': 0}, serial_usrp_dst1: {'x': 3, 'y': 0, 'z': 0}}
# coord_list = ['x', 'y']
#
# # For backward compatibility
# location[ip_usrp_src1] = location[serial_usrp_src1]
# location[ip_usrp_dst1] = location[serial_usrp_dst1]
#
# # For backward compatibility
# usrp_ip_2_ndidx = {ip_usrp_src1: 0, ip_usrp_dst1: 1}
#
# # For backward compatibility
# usrp_ip_sender_of_session = {ip_usrp_src1: [ip_usrp_src1]}
#
# # Arguments for UHD (using serial)
# args = ['serial=' + serial_usrp_src1, 'serial=' + serial_usrp_dst1]
#
# # UDP listening ports associated to USRP
# port_usrp_dic = {serial_usrp_src1: udp_port_listen[0], serial_usrp_dst1: udp_port_listen[1],
# 				 ip_usrp_src1: udp_port_listen[0], ip_usrp_dst1: udp_port_listen[1]}
#
# # PC addresses associated with USRPs
# pc_usrp_dic = {serial_usrp_src1: ip_pc_src1, serial_usrp_dst1: ip_pc_dst1, ip_usrp_src1: ip_pc_src1,
# 			   ip_usrp_dst1: ip_pc_dst1}
#
# # Dictionary of neighboring nodes
# neighbors_dic = {serial_usrp_src1: [serial_usrp_dst1], serial_usrp_dst1: [serial_usrp_src1],
# 				 ip_usrp_src1: [ip_usrp_dst1], ip_usrp_dst1: [ip_usrp_src1]}
#
# #   Transmit/Receive Frequency Configuration
# f1 = 2.0e9
#
# # Configuration for one session: src1 -> dst1
# tx_freq = [f1, None]
# rx_freq = [None, f1]
#
# total_bytes = l4_packets_to_send * number_of_frames * l2_size
#
#
# ####################################################################################
# #                           Network Runtime Information
# ####################################################################################
#
# # Record Throughput
# thpt_history = []
# time_idx = []
#
# # Configure initial Lagrangane coefficent for different control problems
# # Large value for power minimization, small value for rate maximization
# if scheme != 6:
#     ptcl_name.link_sngl_lbd = 0.01
#     ptcl_name.Lag_step = 0.0005
# else:
#     pass  # Use default values in ptcl_name
#
# sgl_pwr_thisnode = None  # average received signal power of this node, updated in csi.py
#
# values_net_para2 = {}
#
# lag_dict = {}
#
# # node_list = ['src1', 'src2', 'rly11', 'rly12', 'rly21', 'rly22']
# node_list = ['src1']
#
#
# expr_lag = None
#
# #################################################
#
# load_idx_pwr = 0
# load_idx_rate = 0
#
# pwr_file = []
# rate_file = None
#
# pnl_history = []
#
# tx_pkt = 0
#
# phy_cnt = 1

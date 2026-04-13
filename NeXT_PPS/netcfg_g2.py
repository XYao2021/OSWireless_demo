##! /usr/bin/python
########################################################################################################################################################################
#               Framing
########################################################################################################################################################################
#
# layer 2 (Datalink)	 ________________________________________________________________________________________
#	STRUCTURE			|_______pktno_mac_______________|_______src_ip_usrp_____________|_______dst_ip_usrp_____|
#	BYTES				|			2					|			13					|			13
#
#	FIELD						WRITE								READ
#	pktno_mac					struct.pack('h', pktno_mac)			(pktno_mac,) = struct.unpack('h', down_packet[0:2])
#	source_ip_usrp				+ str(self.layer_2_ip_uspr)			mac_packet[2:14]
# 	dst_ip_usrp					+ str(self.layer_2_next_hop_ip_uspr)mac_packet[14:26]
#
#
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------
# layer 4 (Transport)#   ____________________________________________________________________________________________________________
#	STRUCTURE			|_______pktno_l4________________|_______src_ip_l4_______________|_______dst_ip_l4_______|_____timestamp_____|
#	BYTES				|			8					|			13					|			13			|			8
#
#	FIELD						WRITE								READ.
#	pktno_l4					struct.pack('l', pktno_l4)			(l4_ack_pktno,) = struct.unpack('l', ack_l4[:8])
#	source_ip_l4				+ self.ip_usrp 						l4_packet_sender = ack_l4[8:20]
# 	dst_ip_l4					+ dest_usrp 						l4_packet_receiver = ack_l4[20:32]
#	timestamp 					+  struct.pack('d', timestamp)		(timestamp,) = struct.unpack('d', ack_l4[32:40])
#
#
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------
# control channel (Transport): it has a different structure according to message_code value
#																		 ------------
#	-2: channel coding update
#						 _______________________________________________________________________________________________________________
#	STRUCTURE			|________message_code___________|_________src_ip_usrp___________|_______dst_ip_usrp_____|__________value_______|
#	BYTES				|				2				|				13				|				13		|			4
#
#	FIELD						WRITE								READ
#	message_kind_code			struct.pack('h', -2)		 		(pktno_mac,) = struct.unpack('h', down_packet[0:2])
#	src_ip_usrp				+ str(self.ip_address_usrp)				mac_source_ip =   mac_packet[2:14]
# 	dst_ip_usrp				+ str(self.layer_2_next_hop_ip_uspr) 	mac_destination_ip =   mac_packet[14:26]
#	value					+ struct.pack('f', ch_coding_rate)		(new_rate,) = struct.unpack('f', payload[26:30])
#
#	-1: channel coding update
#						 _______________________________________________________________________________________________________________
#	STRUCTURE			|________message_code___________|_________src_ip_usrp___________|_______dst_ip_usrp_____|__________value_______|
#	BYTES				|				2				|				13				|				13		|			4
#
#	FIELD						WRITE								READ
#	message_kind_code			struct.pack('h', -1)		 		(pktno_mac,) = struct.unpack('h', down_packet[0:2])
#	src_ip_usrp				+ str(self.ip_address_usrp)				mac_source_ip =   mac_packet[2:14]
# 	dst_ip_usrp				+ str(self.layer_2_next_hop_ip_uspr) 	mac_destination_ip =   mac_packet[14:26]
#	value					+ struct.pack('f', ch_coding_rate)		(new_rate,) = struct.unpack('f', payload[26:30])
#
#
#	2: 2nd layer ack
#	 					 _______________________________________________________________________________________________________________________
#	STRUCTURE			|_______message_code____________|_______pktno_mac_______________|_______src_ip_usrp_____________|_______dst_ip_usrp_____|
#	BYTES				|				2				|			2					|			13					|			13
#
#	FIELD						WRITE								READ
#	message_kind_code			struct.pack('h', 2)					(pktno_mac,) = struct.unpack('h', down_packet[0:2])
#	pktno_mac					struct.pack('h', pktno_mac)			(pktno_mac,) = struct.unpack('h', down_packet[0:2])
#	source_ip_usrp				+ str(self.layer_2_ip_uspr)			mac_packet[2:14]
# 	dst_ip_usrp					+ str(self.layer_2_next_hop_ip_uspr)mac_packet[14:26]
#
#
#	4: 4th layer ack
#						 ___________________________________________________________________________________________________________________________________________
#	STRUCTURE			|_______message_code____________|_______pktno_l4________________|_______src_ip_l4_______________|_______dst_ip_l4_______|_____timestamp_____|
#	BYTES				|				2				|			8					|			13					|			13			|			8
#
#	FIELD						WRITE								READ
#	message_kind_code			struct.pack('h', 4)			 		(pktno_mac,) = struct.unpack('h', down_packet[0:2])
#	pktno_l4					struct.pack('l', pktno_l4)			(l4_ack_pktno,) = struct.unpack('l', ack_l4[:8])
#	source_ip_l4				+ self.ip_usrp 						l4_packet_sender = ack_l4[8:20]
# 	dst_ip_l4					+ dest_usrp 						l4_packet_receiver = ack_l4[20:32]
#	timestamp 					+  struct.pack('d', timestamp)		(timestamp,) = struct.unpack('d', ack_l4[32:40])
#
#
#	-3: general messagging
#	 					 _______________________________________________________________________________________________________________________________________________________
#	STRUCTURE			|_______message_code____________|_______src_ip_usrp_____________|_______dst_ip_usrp_____|_______message_code____________|_______message_value____________|
#	BYTES				|				2				|			13					|			13							2				|				4				|
#
#	FIELD						WRITE								READ
#	message_kind_code			struct.pack('h', -3)				(pktno_mac,) = struct.unpack('h', down_packet[0:2])
#	source_ip_usrp				+ str(self.layer_2_ip_uspr)			mac_packet[2:14]
# 	dst_ip_usrp					+ str(self.layer_2_next_hop_ip_uspr)mac_packet[14:26]
#	para_code					+ struct.pack('h', para_code)		(para_code,) = struct.unpack('h',sgl_msg[24:26])
#	para_val					+ struct.pack('f', para_val)		(para_value,) = struct.unpack('f',sgl_msg[26:30])
#
#

#################################################################################
#                   Import system libraries
#################################################################################
import time
import math
import numpy as np
from random import randint
import socket
import os
import sys
import inspect

#################################################################################
#                   Configure Directory
#################################################################################
# This path is the same as the current path below, therefore not needed anymore
# # realpath() will make your script run, even if you symlink it :)
# cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
# if cmd_folder not in sys.path:
# sys.path.insert(0, cmd_folder)

# Get current and parent directory; partent directory is the overall directory of the whole project
p = os.getcwd()  # Current directory
p = os.path.dirname(p)  # Parent directory

sys.path.append("../")
sys.path.append("../NeXT-OS")
sys.path.append("../NeXT-OS/wos-dir")
sys.path.append("../NeXT-OS/wos-ncp")
sys.path.append("../NeXT-OS/wos-network")

# Insert the overall path to the search path
sys.path.insert(0, p + '/NeXT-OS/wos-protocol')  # Directory of testbed
sys.path.insert(0, p + '/NeXT-OS/wos-network')  # Network parameters
sys.path.insert(0, p + '/NeXT-OS/wos-alglib')  # Algorithm parameters

#################################################################################
#                   Import UB NeXT libraries
#################################################################################
import ptcl_name
import net_name_g2

####################################################################################
#                         Constants and node information
####################################################################################

# very small value to approximate 0 in denominator
SMALL_VALUE = 1e-20

# change this to 0 to mute notes display
disp_note = 0
note1 = 'Next step work: connect correlator blocks; implement CSI collection function; adaptive algorithm.'
note2 = 'In netcfg.py, set disp_note = 0 to run the program.'

# Point to the node object, updated in mynd.py
thisnode = None

# index of this node, updated in mynd.py
idx_thisnode = None

# Node id, which will be updated in mynd.py, and will be used to construct file names in mynd.py
nodeid = None

# Receiver block, initialized to None, will be updated after the receiver block created in start_l1_receiving_block
# This block will be invoked to get received signal power
obj_rcvr_blk = None

####################################################################################
#                          Transmission Parameters
####################################################################################

# select control algorithm
# alg = 'JOCP'                   # JOCP algorithm will not be implemented since our focus is automated algorithm generation.
alg = 'WNOS'

# select physical layer: 'NARROWBAND' or 'OFDM'
phy = 'NARROWBAND'
# phy = 'OFDM'

# narrowband parmeters: transmitter and reciever must be set for the same parameters
narrow_rate = ptcl_name.narrow_rate  # transmit rate in bps
narrow_modulation = 'gmsk'  # 'bpsk', 'gmsk'

# Switch for transmission parameter optimization
# 1 - optimized; 0 - not optimized
b_optrate = 0  # switch for rate optimization
b_optpwr = 0  # switch for power optimization

# Generate the initial transmit gain randomly
# tx_gain = randint(net_name.min_pwr_in_dB, net_name.max_pwr_in_dB)
tx_gain = 15

# Initialize the transport-layer rate, in bps
tspt_rate = 256 * 1.9 * 5.1  # 12/11/2017, Guan, in bps
# ! /usr/bin/python

scheme = 1

# Best Response, use the maximum power and layer-4 transmission rate
if scheme == 1:
    b_br = 'on'  # br -> best response
    b_pwr_ctl = 'off'
    b_Lag_ctl = 'off'
    b_rate_ctl = b_Lag_ctl

    # Use the maximum power and rate
    tx_gain = net_name_g2.max_pwr_in_dB  # transmit gain of usrp
    tspt_rate = net_name_g2.max_rate_in_bps  # Initial tansport layer rate in bps

# power and rate control
if scheme == 2:
    b_br = 'off'
    b_pwr_ctl = 'on'
    b_Lag_ctl = 'on'
    b_rate_ctl = b_Lag_ctl

# only rate control
if scheme == 3:
    b_br = 'off'
    b_pwr_ctl = 'off'
    b_Lag_ctl = 'on'
    b_rate_ctl = b_Lag_ctl

# No Control, fixed power and layer-4 transmission rate
if scheme == 4:
    b_br = 'off'
    b_pwr_ctl = 'off'
    b_Lag_ctl = 'off'
    b_rate_ctl = b_Lag_ctl

# only power control
if scheme == 5:
    b_br = 'off'
    b_pwr_ctl = 'on'
    b_Lag_ctl = 'off'
    b_rate_ctl = b_Lag_ctl

# For power minimization, without rate control, with power control, with Lagrangian updating
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

# The initial point for the two counters are initialized
rate_init_counter = 0
pwr_init_counter = 0
index = 0
opt_val = None

# transmit parameters
sps = 4  # samples per symbol
tx_ampl = 0.8  # transmit amplitude
rx_gain = 10.0  # receiver gain of usrp

l4_control_rate_flag = 1  # 1: limited rate 0: no control, no limit on rate

# dB -> absolute for UHD gain of USRP
tx_gain_abs = 10 ** (tx_gain / 10)  # transmitter side
rx_gain_abs = 10 ** (rx_gain / 10)  # receiver side

# Digital gain of transmitter and receiver, hard coded
tx_digital_gain = 1  # transmitter digital gain, default 1; seems not being used
rx_digital_gain = 1  # receiver digital gain, default 1;  seems not being used

# differential modulation or not
differential = False  # use non_differential modulation to match the preamble correlator at receiver side

sess_rate = {}

####################################################################################
# Channel gain information, measured offline for now
####################################################################################

# Id of nodes: [src1, src2, rly11, rly21, rly12, rly22, dst1, dst2]
# Row: index of node1, starting from 0
# Column: index of node2, starting from 0
# Example: chn_gain[0, 6] represents the channel gain from src1 to dst1

# Initialize the channel gain to all zeros
num_node = 8  # The total number of nodes
chn_gain = np.zeros((num_node, num_node))

# Configure the channel gain matrix based on the measured channel gain values
chn_gain[0, 2] = 0.0083
chn_gain[2, 0] = chn_gain[0, 2]

chn_gain[2, 4] = 0.0028
chn_gain[4, 2] = chn_gain[2, 4]

chn_gain[4, 6] = 0.0005
chn_gain[6, 4] = chn_gain[4, 6]

chn_gain[1, 3] = 0.0001
chn_gain[3, 1] = chn_gain[1, 3]

chn_gain[3, 5] = 0.0003
chn_gain[5, 3] = chn_gain[3, 5]

chn_gain[5, 7] = 0.0037
chn_gain[7, 5] = chn_gain[5, 7]

chn_gain[1, 2] = 0.00001
chn_gain[2, 1] = chn_gain[1, 2]

chn_gain[0, 3] = 0.0012
chn_gain[3, 0] = chn_gain[0, 3]

chn_gain[3, 4] = 0.0001
chn_gain[4, 3] = chn_gain[3, 4]

chn_gain[5, 2] = 0.00002
chn_gain[2, 5] = chn_gain[5, 2]

chn_gain[5, 6] = 0.0006
chn_gain[6, 5] = chn_gain[5, 6]

chn_gain[4, 7] = 0.00004
chn_gain[7, 4] = chn_gain[4, 7]

# Which channel gain should be used for the session with this node as transmitter,
# i.e., the column of chn_gain?
# idx_thisnode (defined above) determines the row of chn_gain matrix to be used
# Channel gain for destination nodes is set to None

# Configuartion for two sessions
#   src1   	src2
#	rly11   rly21
#	rly12   rly22
#	dst1    dst2
chn_idx_thisnode = [2, 3,
                    4, 5,
                    6, 7,
                    None, None]

####################################################################################
# Transmit gain of all transmitters, randomly generated above
# This parameter is used to calculate transmit power and interference
# Updated in running time by signaling exchange
# The transmit gain is set to 0 for destination nodes
####################################################################################


# Configuartion for two sessions, with two hops for each session
#   src1   	src2
#	rly11   rly21
#	rly12   rly22
#	dst1    dst2
tx_gain_allnode = [tx_gain, tx_gain,
                   tx_gain, tx_gain,
                   tx_gain, tx_gain,
                   0, 0]

####################################################################################
#                           Node Role Configuration
####################################################################################

# available node id, the corresponding node type

# Configuration for two sessions
# nd_id   = [	'src1', 	'src2',    'rly11',     'rly21',    'rly12', 	'rly22',    'dst1', 	'dst2']
# nd_type = [	'tx',  		'tx', 	   'relay',  	'relay',  	'relay',    'relay',    'rx',  		'rx']
nd_id = ['src1', 'dst1']
nd_type = ['tx', 'rx']
####################################################################################
#                           IP Configuration
####################################################################################

# IP of PCs
IP_PC1 = '192.168.10.96'
IP_PC2 = '192.168.10.97'

# Session 1 IP address
ip_pc_src1 = IP_PC1
ip_pc_rly11 = IP_PC1
ip_pc_rly12 = IP_PC1
ip_pc_dst1 = IP_PC1

# ip_usrp_src1 	= 	'192.168.10.20'
# ip_usrp_rly11 	= 	'192.168.10.16'
# ip_usrp_rly12 	= 	'192.168.10.21'
# ip_usrp_dst1 	= 	'192.168.10.17'

########################################################
################--------238 setup-------################
########################################################
ip_usrp_src1 = '192.168.10.10'
ip_usrp_rly11 = '192.168.10.11'
ip_usrp_rly12 = '192.168.10.20'
ip_usrp_dst1 = '192.168.10.16'

########################################################

# Session 2
ip_pc_src2 = IP_PC2
ip_pc_rly21 = IP_PC2
ip_pc_rly22 = IP_PC2
ip_pc_dst2 = IP_PC2

# ip_usrp_src2 	= 	'192.168.10.15'
# ip_usrp_rly21  = 	'192.168.10.16'
# ip_usrp_rly22  = 	'192.168.10.14'
# ip_usrp_dst2 	= 	'192.168.10.17'

ip_usrp_src2 = '192.168.10.15'
ip_usrp_rly21 = '192.168.10.14'
ip_usrp_rly22 = '192.168.10.21'
ip_usrp_dst2 = '192.168.10.17'

########################################################
# location of all usrps
# map each usrp to initial location coordinates
########################################################

location = {ip_usrp_src1: {'x': 0, 'y': 0, 'z': 0}, ip_usrp_rly11: {'x': 1, 'y': 0, 'z': 0},
            ip_usrp_rly12: {'x': 2, 'y': 0, 'z': 0}, ip_usrp_dst1: {'x': 3, 'y': 0, 'z': 0},
            ip_usrp_src2: {'x': 0, 'y': 3, 'z': 0}, ip_usrp_rly21: {'x': 1, 'y': 3, 'z': 0},
            ip_usrp_rly22: {'x': 2, 'y': 3, 'z': 0}, ip_usrp_dst2: {'x': 3, 'y': 3, 'z': 0}}

coord_list = ['x', 'y']
########################################################

# map usrp ip to index of the node
usrp_ip_2_ndidx = {ip_usrp_src1: 0, ip_usrp_src2: 1, ip_usrp_rly11: 2, ip_usrp_rly21: 3, ip_usrp_rly12: 4,
                   ip_usrp_rly22: 5, ip_usrp_dst1: 6, ip_usrp_dst2: 7}

# USRP IPs of sender-type nodes of a session, including the source but not destination
usrp_ip_sender_of_session = {ip_usrp_src1: [ip_usrp_src1, ip_usrp_rly11, ip_usrp_rly12],
                             ip_usrp_src2: [ip_usrp_src2, ip_usrp_rly21, ip_usrp_rly22]}

# All usrp IPs
all_usrp_ip = [ip_usrp_src1, ip_usrp_src2,
               ip_usrp_rly11, ip_usrp_rly21,
               ip_usrp_rly12, ip_usrp_rly22,
               ip_usrp_dst1, ip_usrp_dst2]

# usrp address
# Currently exactly 12 character IP address is supported
#   src1   			src2
#	rly11   		rly21
#	rly12   		rly22
#	dst1    		dst2
args = ['addr=' + ip_usrp_src1, 'addr=' + ip_usrp_src2,
        'addr=' + ip_usrp_rly11, 'addr=' + ip_usrp_rly21,
        'addr=' + ip_usrp_rly12, 'addr=' + ip_usrp_rly22,
        'addr=' + ip_usrp_dst1, 'addr=' + ip_usrp_dst2]

# ip_usrp
#   src1   			src2  			src3
#	rly11   		rly21   		rly31
#	rly12   		rly22   		rly32
#	rly13  			rly23   		rly33
#	rly14   		rly24   		rly34
#	rly15   		rly25   		rly35
#	dst1    		dst2    		dst3
ip_usrp = [ip_usrp_src1, ip_usrp_src2,
           ip_usrp_rly11, ip_usrp_rly21,
           ip_usrp_rly12, ip_usrp_rly22,
           ip_usrp_dst1, ip_usrp_dst2]

# ip_pc
#   src1   			src2
#	rly11   		rly21
#	rly12   		rly22
#	dst1    		dst2
ip_pc = [ip_pc_src1, ip_pc_src2,
         ip_pc_rly11, ip_pc_rly21,
         ip_pc_rly12, ip_pc_rly22,
         ip_pc_dst1, ip_pc_dst2]

# prev_hop_usrp
#   src1   			src2
#	rly11   		rly21
#	rly12   		rly22
#	dst1    		dst2
prev_hop_usrp = [None, None,
                 ip_usrp_src1, ip_usrp_src2,
                 ip_usrp_rly11, ip_usrp_rly21,
                 ip_usrp_rly12, ip_usrp_rly22]

# prev_hop_pc
#   src1   			src2
#	rly11   		rly21
#	rly12   		rly22
#	dst1    		dst2
prev_hop_pc = [None, None,
               ip_pc_src1, ip_pc_src2,
               ip_pc_rly11, ip_pc_rly21,
               ip_pc_rly12, ip_pc_rly22]

# next_hop_usrp
#   src1   			src2  			src3
#	rly11   		rly21   		rly31
#	rly12   		rly22   		rly32
#	dst1    		dst2    		dst3
next_hop_usrp = [ip_usrp_rly11, ip_usrp_rly21,
                 ip_usrp_rly12, ip_usrp_rly22,
                 ip_usrp_dst1, ip_usrp_dst2,
                 None, None]

# next_hop_pc
#   src1   			src2
#	rly11   		rly21
#	rly12   		rly22
#	dst1    		dst2
next_hop_pc = [ip_pc_rly11, ip_pc_rly21,
               ip_pc_rly12, ip_pc_rly22,
               ip_pc_dst1, ip_pc_dst2,
               None, None]

# source_usrp
#   src1   			src2
#	rly11   		rly21
#	rly12   		rly22
#	dst1    		dst2
source_usrp = [None, None,
               None, None,
               None, None,
               ip_usrp_src1, ip_usrp_src2]

# source_pc
#   src1   			src2
#	rly11   		rly21
#	rly12   		rly22
#	dst1    		dst2
source_pc = [None, None,
             None, None,
             None, None,
             ip_pc_src1, ip_pc_src2]

# dest_usrp
#   src1   			src2
#	rly11   		rly21
#	rly12   		rly22
#	dst1    		dst2
dest_usrp = [ip_usrp_dst1, ip_usrp_dst2,
             None, None,
             None, None,
             None, None]

# dest_pc
#   src1   			src2  			src3
#	rly11   		rly21   		rly31
#	rly12   		rly22   		rly32
#	dst1    		dst2    		dst3
dest_pc = [ip_pc_dst1, ip_pc_dst2,
           None, None,
           None, None,
           None, None]

# source usrp ip of sessions
#   src1   			src2
#	rly11   		rly21
#	rly12   		rly22
#	dst1    		dst2
source_usrp_session = [ip_usrp_src1, ip_usrp_src2,
                       ip_usrp_src1, ip_usrp_src2,
                       ip_usrp_src1, ip_usrp_src2,
                       ip_usrp_src1, ip_usrp_src2]

# ip computer controlling usrp
pc_usrp_dic = {ip_usrp_src1: ip_pc_src1, ip_usrp_dst1: ip_pc_dst1, ip_usrp_rly11: ip_pc_rly11,
               ip_usrp_rly12: ip_pc_rly12, ip_usrp_src2: ip_pc_src2, ip_usrp_dst2: ip_pc_dst2,
               ip_usrp_rly21: ip_pc_rly21, ip_usrp_rly22: ip_pc_rly22}

# UDP port number
# src 1 --> dst 1
# src 2 --> dst 2
# src 2 --> dst 3

udp_port_listen = [9000, 9001,
                   9003, 9004,
                   9005, 9007,
                   9019, 9020]

udp_port_send = [8000, 8001,
                 8003, 8004,
                 8005, 8007,
                 8019, 8020]

# UDP listening ports associated to usrp
#		'src1', 	'src2', \
# 		'rly11',	'rly21',\
#	 	'rly12', 	'rly22',\
#		'dst1', 	'dst2'

port_usrp_dic = {ip_usrp_src1: udp_port_listen[0], ip_usrp_rly11: udp_port_listen[2], ip_usrp_rly12: udp_port_listen[4],
                 ip_usrp_dst1: udp_port_listen[6], ip_usrp_src2: udp_port_listen[1], ip_usrp_rly21: udp_port_listen[3],
                 ip_usrp_rly22: udp_port_listen[5], ip_usrp_dst2: udp_port_listen[7]}

# dictionary of neighboring nodes. used in the periodic signalling function
# node swill send broadcast periodic updates to all the nodes in their neugboring set
# the function is to be implemented yet

neighbors_dic = {ip_usrp_src1: [ip_usrp_rly11], ip_usrp_dst1: [ip_usrp_rly12],
                 ip_usrp_rly11: [ip_usrp_src1, ip_usrp_rly12], ip_usrp_rly12: [ip_usrp_rly11, ip_usrp_dst1],
                 ip_usrp_src2: [ip_usrp_rly21], ip_usrp_dst2: [ip_usrp_rly22],
                 ip_usrp_rly21: [ip_usrp_src2, ip_usrp_rly22], ip_usrp_rly22: [ip_usrp_rly21, ip_usrp_dst2]}

# session 1 : src has rly as neigbor, rly has src and dst, dst has rly as neigbor. the definition of neigbor can be changed

# session 2

######################################################################################
#   Transmit/Receive Frequency Configuration
#   !!!!!! When freq is changed, itf_relation configuration below needs to be udpated accordingly
######################################################################################
f1 = 2.0e9
f2 = 2.2e9
f3 = 2.4e9
f4 = 2.6e9
f5 = 2.8e9
f6 = 3.0e9

'''
# Configuration for three sessions
#   src1   			src2  			src3
#	rly11   		rly21   		rly31
#	rly12   		rly22   		rly32
#	rly13  			rly23   		rly33
#	rly14   		rly24   		rly34 9001
#	rly15   		rly25   		rly35
#	dst1    		dst2    		dst3
tx_freq   =   [	f1,  		f1, 		f1,\
  		        f2,  		f2,  		f2,\
  		        f3,  		f3,  		f3,\
		        None,   	None,   	None]

rx_freq   =   [	None,   	None,   	None,\
		        f1,  		f1, 		f1,\
  		        f2,  		f2,  		f2,\
  		        f3,  		f3,  		f3]
'''

# Configuration for two sessions
#   src1   			src2
#	rly11   		rly21
#	rly12   		rly22
#	dst1    		dst2
tx_freq = [f1, f1,
           f2, f2,
           f3, f3,
           None, None]

rx_freq = [None, None,
           f1, f1,
           f2, f2,
           f3, f3]

####################################################################################
# Interference Configuration
#
# Interference relationship, this needs to be configured according to frequency used by the nodes
# Only relay and destination suffer from interference, source nodes do not
#
# Vector name indicate the nodes that receive interference
# Elecments of each vector represent the interferer
#
# 0: no mutual interference; 1: there is mutual interference
#####################################################################################

# Configuartion for two sessions
#       	src1   	src2  	rly11   rly21   rly12   rly22   dst1    dst2
itf_src1 = [0, 0, 0, 0, 0, 0, 0, 0]
itf_src2 = [0, 0, 0, 0, 0, 0, 0, 0]

itf_rly11 = [0, 1, 0, 0, 0, 0, 0, 0]
itf_rly21 = [1, 0, 0, 0, 0, 0, 0, 0]

itf_rly12 = [0, 0, 0, 1, 0, 0, 0, 0]
itf_rly22 = [0, 0, 1, 0, 0, 0, 0, 0]

itf_dst1 = [0, 0, 0, 0, 0, 1, 0, 0]
itf_dst2 = [0, 0, 0, 0, 1, 0, 0, 0]

'''
# Configuration for three sessions
# itf_relation = np.matrix([	itf_src1, 	itf_src2, 	itf_src3,
                          	# itf_rly11, 	itf_rly21, 	itf_rly31,
				            # itf_rly12, 	itf_rly22, 	itf_rly32,
				            # itf_rly13, 	itf_rly23, 	itf_rly33,
				            # itf_rly14, 	itf_rly24, 	itf_rly34,
				            # itf_rly15, 	itf_rly25, 	itf_rly35,
                          	# itf_dst1, 	itf_dst2, 	itf_dst3])

itf_relation = np.matrix([	itf_src1, 	itf_src2, 	itf_src3,
                          	itf_rly11, 	itf_rly21, 	itf_rly31,
				            itf_rly12, 	itf_rly22, 	itf_rly32,
                          	itf_dst1, 	itf_dst2, 	itf_dst3])
'''
# Configuration for two sessions
itf_relation = np.matrix([itf_src1, itf_src2,
                          itf_rly11, itf_rly21,
                          itf_rly12, itf_rly22,
                          itf_dst1, itf_dst2])

####################################################################################
#                       Protocol Configuration
####################################################################################
# number of frames at mac layer building one layer-4 packet
number_of_blocks = 1  # number of 255Byte blocks composing a l2 packet
number_of_frames = 2  # number of layer 2 frames in one layer 4 packet
l4_packets_to_send = 10000  # Total number of layer-4 packets to sent

# Channel coding rate configuration (the list of candidate channel coding rates)
ch_coding_rate = [0.14, 0.16, 0.18, 0.20, 0.22, 0.24, 0.20, 0.22, 0.24, 0.26, 0.28, 0.30]

l2_size_block = 128  # fixed, in Byte, maximum 4096/2 = 2048
l1_size = int(l2_size_block * (1 + ch_coding_rate[2]) - 1)  # variable, default half l2 packet
l2_size = l2_size_block * number_of_blocks
l4_size = l2_size * number_of_frames

l4_header_length = 42
l2_header_length = 28
chunk_size = l2_size - l2_header_length

timeout_l2 = 0.3 * number_of_blocks  # time in second to wait for layer 2 ack
timeout_l4 = timeout_l2 * number_of_frames * number_of_blocks * 2 * 7  # time in second to wait for layer 4 ack

# retransmission limit
l2_retransmission_threshold = 10  # 500
l4_retransmission_threshold = 10  # 20

# point to point PER thresholds
l2_th_PER_low = 0.05
l2_th_PER_high = 0.1

total_bytes = l4_packets_to_send * number_of_frames * l2_size

# P2P throughput parameters
l2_th_coeff = 0.75

l4_maximum_rate = tspt_rate / 8  # bps -> [Bps]
l4_maximum_packets_per_second = max(1, int(math.ceil(l4_maximum_rate / l4_size)))

'''
# Configuartion for three sessions
# window size for layer 2
#    src1  			src2  			src3
#	rly11   		rly21   		rly31
#	rly12   		rly22   		rly32
#	rly13  			rly23   		rly33
#	rly14   		rly24   		rly34
#	rly15   		rly25   		rly35
#	dst1    		dst2    		dst3
l2_window   =  [1,   					1, 						   1,\
				1,  					1,						   1,\
				1,  					1,						   1,\
				1,   					1,						   1]
'''

# Configuration for two sessions
# window size for layer 2
#   src1  			src2
#	rly11   		rly21
#	rly12   		rly22
#	dst1    		dst2
l2_window = [1, 1,
             1, 1,
             1, 1,
             1, 1]

# Configuration for two sessions
# window size for layer 4
#   src1   			src2
#	rly11   		rly21
#	rly12   		rly22
#	dst1    		dst2

# window size implements sliding window transport layer protocol at sources
l4_window = [6, 6,
             1, 1,
             1, 1,
             1, 1]

####################################################################################
#                           Network Runtime Information
####################################################################################

# Total number of received packets
n_tot = 0

# Time when node starts to run
time_start = time.time()
prev_time = time_start

# Record Throughput
thpt_history = []
time_idx = []

# Record power
pwr_history = [tx_gain]
pwr_time_history = []

# Indication of whether Lagrangian has reached zero. 0: No; 1: Yes
# Updated in signaling.py
b_zero_lag = 0

# Link layer running average throughput, updated in lyr2 class, used in signaling module
# in lyr2 packet, multiply packet size to convert to bps
lnk_thpt = 0.001  # Initialized to small value rather than zero to avoid "divided by zero" error
n_pkt_cnt = 0  # Link layer packet counter, used in ly2 to count the received packets for throughput estimation

# Configure initial Lagrangane coefficent for different control problems
# Large value for power minimization, small value for rate maximization
if scheme != 6:
    ptcl_name.link_sngl_lbd = 0.01
    ptcl_name.Lag_step = 0.0005
else:
    pass  # Use default values in ptcl_name

# para_pnl	needs to be reset to zero if having not been updated for a while
pre_para_pnl_updt_time = -1  # Initialized to -1

sir_thisnode = None  # SIR information measured online, initialized to None
sgl_pwr_thisnode = None  # average received signal power of this node, updated in csi.py
alpha = 0.5  # coefficient of running average

values_net_para = {}
values_net_para2 = {}

lag_dict = {}

node_list = ['src1', 'src2', 'rly11', 'rly12', 'rly21', 'rly22']

payload_size = None
l2_capacity = 0

itx_pnl = 0
expr_lag = None
#################################################

throughput_list = []
rate_list = []

load_idx_pwr = 0
load_idx_rate = 0

pwr_file = []
rate_file = None

pnl_history = []
lag_history = []

delay_history = []

tx_pkt = 0
tx_time_stamp_dict = {}  # This dictionary will be used to store the timestamp of the txd pkt
ack_time_stamp_dict = {}  # This dictionary wll be used to store the timestamp in the ACK

phy_cnt = 1
tspt_flag = False

lag_2_dict = False
lag_2_dict2 = False

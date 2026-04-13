
# signalling exchange module (Modified for B210 USRP)

# Configure directory
import os
import sys
import socket
import struct
import time
import numpy as np
from sympy import *
import math

sys.path.append("/home/edgeai/Dropbox/Research/OS Wireless/OSWireless_demo")
from addpath import *

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
target_folder = os.path.join(project_root, "NeXT_OS")
sys.path.append(target_folder)

target_folder = os.path.join(target_folder, "wos_protocol")
sys.path.append(target_folder)
# Protocol files (Lagrangian for now)
import ptcl_func
import ptcl_name

# Symbolic computing
from mpmath import *
import netcfg

# directory file
import pps_dir
import importlib.util

"""
#################################################################
# signaling format (Modified for B210 serial addressing)
# -------------------------------------------------------------
# |  signalling code |  node serial  |   value    |
# |     (1 byte)     |  (1 bytes)   |  (float)   |
# -------------------------------------------------------------
#################################################################
"""

# signalling code, one byte
TX_GAIN = 0
SIR = 1

# print("\n ######## -------- Signalling.py -- RUN UP TO HERE -------- ######## \n")

def start_listening_socket(self):
    # Modified for B210: Using PC address for socket communication
    # self.UDP_IP_SEND = self.pc_addr  # PC address for outgoing communications
    """###### ------ This could be the potential error for UDP_IP_send for socket communication ------######"""

    self.UDP_IP_LISTEN = self.ip_pc
    self.UDP_PORT_LISTEN = self.udp_port_listen

    print('PC ADDRESS:', self.UDP_IP_LISTEN, '\n')
    print('PORT NUMBER:', self.UDP_PORT_LISTEN, '\n')
    print("@@@ trying to open a UDP socket at PC address:", self.UDP_IP_LISTEN, 'and PORT:', self.UDP_PORT_LISTEN, '\n')

    self.sock_listen = socket.socket(socket.AF_INET,  # Internet
                                     socket.SOCK_DGRAM)  # UDP

    self.sock_listen.bind((self.UDP_IP_LISTEN, self.UDP_PORT_LISTEN))

    self.l4.initialize_received_l4_feedback()

    print('LISTENING SOCKET started at ', self.UDP_IP_LISTEN, ' ', self.UDP_PORT_LISTEN, '\n')

    while True:
        (packet, addr) = self.sock_listen.recvfrom(1024)  # buffer size is 1024 bytes
        (cc_code,) = struct.unpack('h', packet[0:2])

        packet = packet[2:]  # removing signalling code from the received packet
        # print('ACK MESSAGE: ', cc_code, packet, '\n')  # the cc_code always be -3 -> keep generating signal messages
        if cc_code == 2:  # layer 2 ack
            self.l2.received_l2_feedback(packet)
            # print("[SIGNALLING DEBUGGING 2] The cc_code is 2 and message received is: ", packet)
        elif cc_code == 4:  # layer 4 ack
            self.l4.received_l4_feedback(packet)
            # print("[SIGNALLING DEBUGGING 4] The cc_code is 4 and message received is: ", packet)
        elif cc_code == -1:  # layer 2 coding rate singalling message ack
            self.l2.received_cc_ack()
            # print("[SIGNALLING DEBUGGING -1] The cc_code is -1 and message received is: ", packet)
        elif cc_code == -2:  # layer 2 coding rate signalling message
            self.l2.handle_update_rate_exception(packet)
            # print("[SIGNALLING DEBUGGING -2] The cc_code is -2 and message received is: ", packet)
        elif cc_code == -3:  # general signaling message
            parse_sgl(self, packet)
            # print("[SIGNALLING DEBUGGING -3] The cc_code is -3 and message received is: ", packet)


def periodic_update_neighbors(self):
    value1 = 1000
    value2 = 2000

    n_updt = 0
    n_prd = 1  # Update transport layer once, physical layer N times

    while True:
        n_updt += 1

        time.sleep(3)

        # Penalization needs to be reset if having not been updated for a while (10 second here)
        cur_time = time.time()
        if netcfg.pre_para_pnl_updt_time == -1:  # Have not received any penalization, no need to reset
            pass
        else:
            if cur_time - netcfg.pre_para_pnl_updt_time >= 15:
                ptcl_name.para_pnl = [0]

        # Update Lagrangian coefficients; not needed for destinations
        if netcfg.nd_type[netcfg.idx_thisnode] != 'rx' and n_updt % n_prd == 0:
            if netcfg.b_Lag_ctl == 'on':  # XY: defined in netcfg scheme parameters
                updt_Lag()  # XY: Update lagrangian coefficient
            else:
                pass

        # Update transmit gain
        if netcfg.nd_type[netcfg.idx_thisnode] != 'rx':
            updt_pwr()  # XY: Update transmit power
            pass

        # Update transport layer transmission rate, only for source
        if netcfg.nd_type[netcfg.idx_thisnode] == 'tx':
            updt_tsptrate()  # XY: Update transport layer transmission rate
            pass

        # # Update locally measured interference
        # b_updt, value = ptcl_func.updt_lnkitf()

        # Handle both single return value and tuple returns
        result = ptcl_func.updt_lnkitf()
        if isinstance(result, tuple):
            b_updt, value = result
        else:
            # If it returns a single boolean, assume no value update
            b_updt = result
            value = None

        # Send measured link interference to previous hop node, i.e., the
        # corresponding transmitter
        #
        # True means information has been udpated, False not updated and no need to send
        if b_updt is True:
            # Modified for B210: Using serial numbers instead of IPs
            dst_serials = [netcfg.prev_hop_serial[netcfg.idx_thisnode]]  # The outer [] to make a list
            msg_code = ptcl_name.code_lkitf_rcvr
            msg_val = ptcl_name.lkitf_rcvr_side
            broadcast_sgl(self, self.serial_usrp, dst_serials, msg_code, msg_val)
            netcfg.itx_pnl = msg_val

        # Send transmit power to all other nodes
        # Destination nodes don't need to broadcast power message
        if netcfg.nd_type[netcfg.idx_thisnode] != 'rx':
            # Modified for B210: Using serial numbers instead of IPs
            dst_serials = list(netcfg.all_usrp_serial)  # Copy list

            # No need to send message to itself
            if self.serial_usrp in dst_serials:
                dst_serials.remove(self.serial_usrp)

            msg_code = ptcl_name.code_tsmt_gain
            msg_val = netcfg.tx_gain_allnode[netcfg.idx_thisnode]  # XY: Transmit power list

            broadcast_sgl(self, self.serial_usrp, dst_serials, msg_code, msg_val)

        # Send Lagrangian coefficients to the source node of the session
        # Destination doesn't send this message, since the message is updated at each transmitter (source, relay)
        if netcfg.nd_type[netcfg.idx_thisnode] != 'rx':
            # Modified for B210: Using serial numbers instead of IPs
            dst_serials = [netcfg.source_usrp_session_serial[netcfg.idx_thisnode]]
            msg_code = ptcl_name.code_Lagrangian

            for lags in netcfg.expr_lag.keys():
                file_lag = 'lag_update_' + lags

                if netcfg.scheme == 8:
                    lag_updt_file = netcfg.values_net_para_lag[file_lag]   # Not defined in netcfg file
                if netcfg.scheme != 8:
                    lag_updt_file = netcfg.values_net_para['lag_update_']

                msg_val = lag_updt_file.call_back()

                setattr(netcfg.values_net_para['lag_in_'], lags, msg_val)
                if netcfg.tspt_flag is True:
                    setattr(netcfg.values_net_para_tspt['lag_in_'], lags, msg_val)  # XY: Not defined
                netcfg.lag_name = lags  # XY: Not defined
                broadcast_sgl(self, self.serial_usrp, dst_serials, msg_code, msg_val)
                val = getattr(netcfg.values_net_para['lag_in_'], netcfg.lag_name)  # Not defined

        # Send parameters for updating Lagrangian coefficients, from each source node to all the senders
        # along the path of the session.

        # Only source node needs to send
        if netcfg.nd_type[netcfg.idx_thisnode] == 'tx':  # This part is reaching.
            # Modified for B210: Using serial numbers instead of IPs
            dst_serials = netcfg.usrp_serial_sender_of_session[self.serial_usrp]

            msg_code = ptcl_name.code_ssrate

            msg_val = getattr(netcfg.values_net_para['__net_para_'], netcfg.ses_name)  # Not defined

            broadcast_sgl(self, self.serial_usrp, dst_serials, msg_code, msg_val)

        # Penalization parameters

        # Only transmitters (source and relay) need to send
        if netcfg.nd_type[netcfg.idx_thisnode] != 'rx':
            msg_code = ptcl_name.code_pnl

            # Determine index of the receiver of this node
            idx_rcvr = netcfg.chn_idx_thisnode[netcfg.idx_thisnode]

            # Loop over all interfereing nodes, prepare a message for each of them
            # and send the message

            # First, take the interfereing relationship vector for the receiver of this node
            itf_rla_vec = netcfg.itf_relation[idx_rcvr, :]

            ch_gain_rel = netcfg.chn_gain[idx_rcvr, :]

            ch_gain = np.sum(np.multiply(itf_rla_vec, ch_gain_rel))

            # Number of possible nodes, including interfering and non-interfering
            NUM = itf_rla_vec.size

            # Loop over all nodes
            for n in range(NUM):

                # if the node is not interfering, skip, otherwise prepare message and send
                if itf_rla_vec.item((0, n)) == 0:
                    continue
                else:
                    # Destination address - Modified for B210
                    dst_serials = [netcfg.all_usrp_serial[n]]

                    # Prepare message value, initialize
                    msg_val = 0  # Dummy value

                    pnl_file = netcfg.values_net_para['pnl__phy_']

                    if netcfg.scheme != 9:
                        msg_val = pnl_file.calc_pnl() * ch_gain
                    else:
                        vallist = []
                        msg_val = pnl_file.calc_pnl()
                        for val in msg_val:
                            vallist.append(val[0])
                            msg_val = vallist

                    broadcast_sgl(self, self.serial_usrp, dst_serials, msg_code, msg_val)

        # delay minimization
        if netcfg.scheme == 8:
            if netcfg.nd_type[netcfg.idx_thisnode] != 'rx':
                updt_aux_var()


def updt_aux_var():
    # for delay minimization the auxiliary variable is theta
    if netcfg.aux_var == 'theta':

        # Get the lkcap and theta names
        lkcapvar = 'lkcap_' + netcfg.lnk_name  # Not defined
        theta_name = 'theta_' + netcfg.lnk_name

        # Obtain the value of the lkcap from the net para file
        lk_cap = getattr(netcfg.values_net_para['__net_para_'], lkcapvar)

        # Initialize aggregate rate to 0. Based on the sessions in netcfg.sess_rate dictionary, the aggregate rate will be calculated by adding multiple session rates
        aggr_rate = 0
        for rate in netcfg.sess_rate.keys():
            rate_val = netcfg.sess_rate[rate]
            aggr_rate += rate_val

        # Calculate the value of theta
        theta = lk_cap - aggr_rate

        # Currently, we append 0 if the lkcap and aggr rate are equal
        # if they are unequal, we can calculate the delay by taking the reciprocal of the theta value calculated in the previous step
        # This reciprocal value is stored in netcfg.delay_history list for later use (plot figures)
        if theta == 0:
            netcfg.delay_history.append(0)
        else:
            netcfg.delay_history.append(1 / theta)

        setattr(netcfg.values_net_para['__net_para_'], theta_name, theta)
        if netcfg.tspt_flag is True:
            setattr(netcfg.values_net_para_tspt['__net_para_'], theta_name, theta)


def start_sending_socket(self):
    # Modified for B210: Using PC address for socket communication
    # self.UDP_IP_SEND = self.pc_addr  # PC address for outgoing communications
    """###### ------ This could be the potential error for UDP_IP_send for socket communication ------######"""
    self.UDP_IP_SEND = self.ip_pc
    self.UDP_PORT_SEND = self.udp_port_send

    self.sock_send = socket.socket(socket.AF_INET,  # Internet
                                   socket.SOCK_DGRAM)  # UDP


def initialize_matrix(self):
    # Modified for B210: Using serial numbers as dictionary keys
    self.signalling_dic = {}
    for serial in netcfg.usrp_serial:
        self.signalling_dic[serial] = {}


def broadcast_sgl(self, src_serial, rcvr_serial_list, para_code, para_val):

    """func: broad signalling to all related nodes

    src_serial: serial of transmitter node
    rcvr_serial_list: serial list of receivers to whom the message should be sent
    para_code: ID of parameters to be sent
    para_val: value of parameter to be sent"""

    for target_serial in rcvr_serial_list:  # XY: Automatically send message to itself?
        # print("[DEBUGGING] Reach the broadcast_sgl function! ", rcvr_serial_list)
        # prepare payload message
        # Modified for B210: Using serialized format with fixed-length fields
        # For all schemes except scheme 9 (mobility) we use just the following method
        if netcfg.scheme != 9:
            # Format: -3 (message code) + source serial (13 bytes) + destination serial (13 bytes) + parameter code + parameter value
            src_encoded = src_serial.encode().ljust(13, b'\x00')
            dst_encoded = target_serial.encode().ljust(13, b'\x00')
            message = struct.pack('h', -3) + src_encoded + dst_encoded + struct.pack('h', para_code) + struct.pack('f', para_val)

        # For scheme 9 except for penalization we use just the following method -> XY: Any difference?
        elif netcfg.scheme == 9 and para_code != ptcl_name.code_pnl:
            src_encoded = src_serial.encode().ljust(13, b'\x00')
            dst_encoded = target_serial.encode().ljust(13, b'\x00')
            message = struct.pack('h', -3) + src_encoded + dst_encoded + struct.pack('h', para_code) + struct.pack('f', para_val)

        # For scheme 9 only penalization follow this method
        # For mobility schemes, since the penalization value is a vector,
        # we follow the following method to prepare the message
        # The parsing of the message is adapted accordingly
        elif netcfg.scheme == 9 and para_code == ptcl_name.code_pnl:
            src_encoded = src_serial.encode().ljust(13, b'\x00')
            dst_encoded = target_serial.encode().ljust(13, b'\x00')
            message = (struct.pack('h', -3) + src_encoded + dst_encoded
                       + struct.pack('h', para_code) + struct.pack('%sf' % len(para_val), *para_val)
                       + struct.pack('h', len(para_val)))

        # NEW CODE:
        if para_code == ptcl_name.code_Lagrangian:
            message = message + str(netcfg.lag_name).encode('utf-8')

        if para_code == ptcl_name.code_ssrate:
            message = message + str(netcfg.ses_name).encode('utf-8')

        # if para_code == ptcl_name.code_Lagrangian:
        #     message = message + str(netcfg.lag_name)
        #
        # if para_code == ptcl_name.code_ssrate:
        #     message = message + str(netcfg.ses_name)

        parse_sgl(self, message[2:])

        # send the message to all receivers one by one

        # Modified for B210: Using serial to address mapping
        target_addr = netcfg.serial_to_addr.get(target_serial)
        target_port = netcfg.serial_to_port.get(target_serial)
        
        "Debugging codes"
        # print('Broadcasting message!!!!!!!!!', target_addr, target_port)
        # print(message)

        if target_addr and target_port:
            self.sock_send.sendto(message, (target_addr, target_port))
        else:
            print(f"Warning: Could not find address/port for serial {target_serial}")


def parse_sgl(self, sgl_msg):

    """
    func: parse a received signalling message and set related parameters
    sgl_msg: the received signalling message (see above for signalling format)
    """

    # get signaling code and value
    # print('Len:', len(sgl_msg))

    # Modified for B210: Adjusted byte offsets for fixed-length serial fields
    # Extract source and destination serials (13 bytes each)
    source_serial_raw = sgl_msg[0:13]
    source_serial = source_serial_raw.strip(b'\x00').decode()

    dst_serial_raw = sgl_msg[13:26]
    dst_serial = dst_serial_raw.strip(b'\x00').decode()

    (para_code,) = struct.unpack('h', sgl_msg[26:28])  # XY: what is the para_code and para_value? Did not find in the layer 2 packet structure
    # print('Inside the signal function: ', para_code, netcfg.scheme)

    if netcfg.scheme != 9:  # Scheme always be 1 in our case for now.
        (para_value,) = struct.unpack('f', sgl_msg[28:32])
    elif netcfg.scheme == 9 and para_code != ptcl_name.code_pnl:
        (para_value,) = struct.unpack('f', sgl_msg[28:32])
    elif netcfg.scheme == 9 and para_code == ptcl_name.code_pnl:
        (val_decode,) = struct.unpack('h', sgl_msg[36:38])
        para_value = struct.unpack('%sf' % val_decode, sgl_msg[28:36])

    # Message contains interference information from next-hop receiver
    if para_code == ptcl_name.code_lkitf_rcvr:
        ptcl_name.lkitf00 = para_value  # Record the receiver-measured interference as link interference

        # val_var_inter = 'lkitf_' + netcfg.lnk_name

        # Check if lnk_name exists (it may not be set for rx nodes)
        if hasattr(netcfg, 'lnk_name'):
            val_var_inter = 'lkitf_' + netcfg.lnk_name
        else:
            # Use a default value for rx nodes
            val_var_inter = 'lkitf_default'

        # print("\n ######## -------- Signalling.py -- RUN UP TO HERE -------- ######## \n")

        # Add safety checks for dictionary access
        if '__net_para_' not in netcfg.values_net_para:
            netcfg.values_net_para['__net_para_'] = type('NetParaObject', (), {})()

        net_para_obj = netcfg.values_net_para['__net_para_']

        # Initialize the attribute if it doesn't exist
        if not hasattr(net_para_obj, val_var_inter):
            setattr(net_para_obj, val_var_inter, 0.0)

        old_var = getattr(netcfg.values_net_para['__net_para_'], val_var_inter)
        setattr(netcfg.values_net_para['__net_para_'], val_var_inter, ptcl_name.lkitf00)
        new_val_inter = getattr(netcfg.values_net_para['__net_para_'], val_var_inter)

    # Message of transmit power of other nodes
    if para_code == ptcl_name.code_tsmt_gain:
        # Modified for B210: Using serial to node index mapping
        idx_sender = netcfg.usrp_serial_2_ndidx.get(source_serial)

        if idx_sender is not None:
            # Record transmit power for sender node
            netcfg.tx_gain_allnode[idx_sender] = para_value
        else:
            print(f"Warning: Could not find node index for serial {source_serial}")

    # The Lagrangian coefficients received from links belong to the path of the session
    if para_code == ptcl_name.code_Lagrangian:
        ptcl_name.sess_links_lbd_dict[source_serial] = para_value

        # Update sess_links_lbd based on the updated sess_links_lbd_dict
        ptcl_name.sess_links_lbd = [value for key, value in ptcl_name.sess_links_lbd_dict.items()]

        # Modified for B210: Using serial-based list lookup
        sender_serials = netcfg.usrp_serial_sender_of_session.get(dst_serial, [])
        if source_serial in sender_serials:
            idxx = sender_serials.index(source_serial) + 1
        else:
            idxx = 0  # Default if not found

        # lag_name = sgl_msg[32:42]
        lag_name = sgl_msg[32:42].decode('utf-8').strip('\x00')

        netcfg.lag_history.append(para_value)
        setattr(netcfg.values_net_para['lag_in_'], lag_name, para_value)

    # Parameters for udpating Lagrangian coefficients
    if para_code == ptcl_name.code_ssrate:
        # sess_name = sgl_msg[32:43]
        sess_name = sgl_msg[32:43].decode('utf-8').strip('\x00')
        setattr(netcfg.values_net_para['__net_para_'], sess_name, para_value)
        netcfg.sess_rate[sess_name] = para_value
        if netcfg.tspt_flag is True:
            setattr(netcfg.values_net_para_tspt['__net_para_'], sess_name, para_value)

    # Parameters for penalization
    if para_code == ptcl_name.code_pnl:
        pnl_coeff = 'pnl_coefficient'
        old_var = getattr(netcfg.values_net_para['__net_para_'], pnl_coeff)
        netcfg.pnl_history.append(para_value)
        setattr(netcfg.values_net_para['__net_para_'], pnl_coeff, para_value)
        if netcfg.tspt_flag is True:
            setattr(netcfg.values_net_para_tspt['__net_para_'], pnl_coeff, para_value)

        ptcl_name.para_pnl_dict[source_serial] = para_value
        ptcl_name.para_pnl = [value for key, value in ptcl_name.para_pnl_dict.items()]


def updt_Lag():
    """
    Update Lagrangian coefficient, see the following paper for theory.
    "A Tutorial on Decomposition Methods for Network Utility Maximization"
    IEEE JSAC, vol. 24, no. 8, August 2006

    Called By: signalling.periodic_update_neighbors()
    """

    # Step size
    step_size = ptcl_name.Lag_step

    # Parameters received from all sources using this link
    Lag_from_src = ptcl_name.para_updt_Lag

    # Calculate link capacity
    #
    # First, calculate SINR
    sgl_pwr = netcfg.tx_gain_allnode[netcfg.idx_thisnode] * ptcl_name.lkgain00  # Useful signaling
    itf = ptcl_name.lkitf00  # Interference
    noise = ptcl_name.lknoise00  # Noise
    SINR = sgl_pwr / (itf + noise)  # SINR

    # Use Transmit rate to approximate the bandwidth
    bandwidth = netcfg.narrow_rate

    # Calculate capacity
    link_cap = bandwidth * math.log(1 + SINR, 2)

    if netcfg.scheme == 6:  # power minimization
        link_cap = netcfg.lnk_thpt * netcfg.l2_size_block * 8  # throught in lyr2 packet * packet size * 8 bits per Byte

    new_Lag = ptcl_name.link_sngl_lbd - step_size / link_cap * (link_cap + sum(Lag_from_src) * 1000)

    ptcl_name.link_sngl_lbd = max(new_Lag, 0)

    # Indicate zero Lagrangian coefficients have been reached
    if ptcl_name.link_sngl_lbd == 0:
        netcfg.b_zero_lag = 1

    # After Lagrangian coefficients get zero, it means there is no need to update transmit rate anymore,
    # but the physical layer power control still needs to continue. To enable this, the Lagrangian coefficients are set to 1e-5
    # for all nodes, but these coefficients are used only for power control at the physical layer.
    #
    # This is controlled using a variable b_zero_lag defined in netcfg
    if netcfg.b_zero_lag == 1:
        ptcl_name.link_sngl_lbd = 1e-7
        new_Lag = ptcl_name.link_sngl_lbd


def load_alg_file(alg_name):
    """
    Load the algorithm file based on the algorithm name
    """
    alg_load = alg_name + '.py'
    alg_load_path = pps_dir.alg_dir + alg_load
    # loaded_alg_file = imp.load_source(pps_dir.alg_dir, alg_load_path)
    spec = importlib.util.spec_from_file_location(pps_dir.alg_dir, alg_load_path)
    loaded_alg_file = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded_alg_file)

    return loaded_alg_file


def nd_id_map(node_role):
    """
    Determine the node id based on the node role
    """

    load_path = pps_dir.driver_dir + 'node_map.py'

    # loaded_file = imp.load_source(pps_dir.driver_dir, load_path)
    spec = importlib.util.spec_from_file_location(pps_dir.driver_dir, load_path)
    loaded_file = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded_file)

    map_result = getattr(loaded_file, node_role)

    return map_result


def get_keyword(opt_var):
    """
    Determine the name of the keyword based on the optimization variable
    """
    var_keyword_map_path = pps_dir.driver_dir + 'var_keyword_map.py'

    # loaded_var_kw_file = imp.load_source(pps_dir.driver_dir, var_keyword_map_path)
    spec = importlib.util.spec_from_file_location(pps_dir.driver_dir, var_keyword_map_path)
    loaded_var_kw_file = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded_var_kw_file)

    keyword = getattr(loaded_var_kw_file, opt_var)

    return keyword


def get_opt_alg(dic_info):
    """
    Determine the name of the algorithm to be called
    """

    algorithm = '__' + dic_info['keyword'] + '_' + dic_info['node']

    return algorithm


def val_updt(node_id, node_link_file, new_value, updt_param):
    map_path = pps_dir.driver_dir + node_link_file + '.py'

    val_var = netcfg.ses_name

    old_val = getattr(netcfg.values_net_para['__net_para_'], netcfg.ses_name)

    setattr(netcfg.values_net_para['__net_para_'], netcfg.ses_name, new_value)
    if netcfg.lag_2_dict:
        setattr(netcfg.values_net_para_lag['__net_para_'], netcfg.ses_name, new_value)
    if netcfg.lag_2_dict2:
        setattr(netcfg.values_net_para_lag['__net_para_2'], netcfg.ses_name, new_value)

    new_val = getattr(netcfg.values_net_para['__net_para_'], netcfg.ses_name)


def val_updt_pwr(node_id, node_link_file, new_value_pwr, new_value_gain, new_value_inter, new_value_capa, updt_param):
    map_path = pps_dir.driver_dir + node_link_file + '.py'

    val_var_pwr = 'lkpwr_' + netcfg.lnk_name
    val_var_gain = 'lkgain_' + netcfg.lnk_name

    val_var_capa = 'lkcap_' + netcfg.lnk_name

    setattr(netcfg.values_net_para['__net_para_'], val_var_pwr, new_value_pwr)
    new_val_pwr = getattr(netcfg.values_net_para['__net_para_'], val_var_pwr)

    setattr(netcfg.values_net_para['__net_para_'], val_var_gain, new_value_gain)
    new_val_gain = getattr(netcfg.values_net_para['__net_para_'], val_var_gain)

    setattr(netcfg.values_net_para['__net_para_'], val_var_capa, new_value_capa)
    new_val_capa = getattr(netcfg.values_net_para['__net_para_'], val_var_capa)

    if netcfg.lag_2_dict:
        setattr(netcfg.values_net_para_lag['__net_para_'], val_var_pwr, new_value_pwr)
        setattr(netcfg.values_net_para_lag['__net_para_'], val_var_gain, new_value_gain)
        setattr(netcfg.values_net_para_lag['__net_para_'], val_var_capa, new_value_capa)


def updt_pwr():
    """
    Update transmit power (which is transmit gain for USRP) by solving the optimization problem
    automated generated in alglib_physol.py.

    Called By: signalling.periodic_update_neighbors()
    """
    # get the node id based on the role: src1 --> node1
    node_role = netcfg.nodeid  # determine the node role information dynamically

    # map role to id based on node_map.py, print the corresponding node index
    node_id_map = nd_id_map(node_role)
    netcfg.node_map_id = node_id_map

    opt_var = 'pwr'

    # variable-dependent keyword
    # keyword = 'phy' # This should be determined based the optimization variable
    keyword = get_keyword(opt_var)

    dic_info = {'node': node_id_map, 'keyword': keyword}

    # Get the name of the algorithm based on the dictionary info (Node id and keyword)
    name_alg = get_opt_alg(dic_info)

    # Load the algorithm file based on the algorithm name
    loaded_alg_file = netcfg.values_net_para['__phy_']

    optval = loaded_alg_file.wnos_optimize()

    this_node_idx = netcfg.idx_thisnode

    # look up the neighbor's index
    neighbor_idx = netcfg.chn_idx_thisnode[this_node_idx]

    ch_gain = netcfg.chn_gain[this_node_idx, neighbor_idx]

    inter_var = 'itf_' + netcfg.nodeid

    inter_matrix = getattr(netcfg, inter_var)

    if 1 in inter_matrix:
        index_inter = inter_matrix.index(1)
        interference_this_node = netcfg.chn_gain[this_node_idx][index_inter]
    else:
        interference_this_node = 0

    # Update transmit gain by applying step size
    old_gain_dB = netcfg.tx_gain_allnode[netcfg.idx_thisnode]

    old_gain = 10 ** (old_gain_dB / 10)  # dB -> absolute

    # Setting new to power to the optimal solution directly
    if optval.success is True:
        if netcfg.scheme == 6:  # Only for power minimization
            new_gain = optval.x[0]
        else:
            new_gain = old_gain + ptcl_name.gamma * (optval.x[0] - old_gain)  # For other control schemes
    else:
        new_gain = old_gain  # Do not update power

    new_gain_dB = 10 * math.log10(new_gain)  # absolute -> dB

    capacity_val = netcfg.l2_capacity

    val_updt_pwr(node_id_map, 'node_link_session', new_gain_dB, ch_gain, interference_this_node, capacity_val, 'link')

    # Record power history
    cur_time = time.time()

    run_time = cur_time - netcfg.time_start  # Elapsed time in second

    netcfg.pwr_time_history.append(run_time)

    # Update transmit gain of USRP
    if netcfg.scheme == 7:
        if netcfg.pwr_init_counter < netcfg.pwr_count - 1:
            new_gain_dB = netcfg.tx_gain
            netcfg.pwr_init_counter += 1
            netcfg.pwr_history.append(new_gain_dB)
        else:
            netcfg.pwr_history.append(new_gain_dB)
    else:
        netcfg.pwr_history.append(new_gain_dB)

    if new_gain_dB != netcfg.tx_gain_allnode[netcfg.idx_thisnode]:
        if netcfg.b_pwr_ctl == 'ON' or netcfg.b_pwr_ctl == 'on':
            new_gain_dB = netcfg.thisnode.set_gain(new_gain_dB)  # Set usrp gain
            netcfg.tx_gain_allnode[netcfg.idx_thisnode] = new_gain_dB  # Update configuration
            ptcl_name.lkpwr00 = new_gain
        else:
            pass

    # Update step size
    ptcl_name.phy_idx = ptcl_name.phy_idx + 1

    if netcfg.scheme != 8:  # 8 does not exist, so applies to all schemes; updating step should be adapted automatically; For power minimization, no need to update this parameter
        ptcl_name.gamma = ptcl_name.gamma * (1 - ptcl_name.epsilon * ptcl_name.gamma)

def updt_tsptrate():
    """
    Update transport layer transmission rate

    Called By: signaling.periodic_update_neighbors()
    """

    # Update iteration parameters
    # get the node id based on the role: src1 --> node1
    node_role = netcfg.nodeid

    # map role to node id based on node_map.py
    node_id_map = nd_id_map(node_role)

    # get the variable dependent keyword
    opt_var = 'rate'
    keyword = get_keyword(opt_var)

    dic_info = {'node': node_id_map, 'keyword': keyword}

    # Get the name of the algorithm based on the dictionary info
    name_alg = get_opt_alg(dic_info)

    # load the algorithm file based on the algorithm name
    if netcfg.scheme == 8:
        loaded_alg_file = netcfg.values_net_para_tspt['__tspt_']
    else:
        loaded_alg_file = netcfg.values_net_para['__tspt_']

    ptcl_name.gamma_tspt = ptcl_name.gamma_tspt * (1 - ptcl_name.epsilon_tspt * ptcl_name.gamma_tspt)

    optval = loaded_alg_file.wnos_optimize()

    # Step size calculated based on the optimization result for rate maximimzation and power minimization NCPs.
    if netcfg.scheme != 8:
        new_rate = ptcl_name.tspt_rate + ptcl_name.gamma_tspt * (optval.x[0] - ptcl_name.tspt_rate)

    if netcfg.scheme == 7:
        if netcfg.rate_init_counter < netcfg.rate_count - 1:
            new_rate = 5
            ptcl_name.tspt_rate = new_rate
            netcfg.rate_init_counter += 1
            netcfg.rate_list.append(new_rate)
        else:
            netcfg.rate_list.append(ptcl_name.tspt_rate)
    else:
        netcfg.rate_list.append(ptcl_name.tspt_rate)

    if netcfg.scheme == 8:
        if netcfg.step_par == 'constant':
            if optval.x[0] < ptcl_name.tspt_rate:
                print('aaa')
                new_rate = ptcl_name.tspt_rate - 0.1
            else:
                print('bbb')
                new_rate = ptcl_name.tspt_rate + 0.1
        else:
            ##VARIABLE STEP SIZE##
            new_rate = ptcl_name.tspt_rate + (
                        ptcl_name.gamma_tspt / (net_name.ssrate_upr_default - net_name.ssrate_lwr_default)) * (
                                   optval.x[0] - ptcl_name.tspt_rate)

    val_updt(node_id_map, 'node_link_session', new_rate, 'session')

    # If rate control is off, ptcl_name should stay at the rate specified in netcfg
    if netcfg.b_rate_ctl == 'on':
        # Record new transmission rate
        ptcl_name.tspt_rate = new_rate
        ptcl_name.keyword['ssrate00'] = new_rate
    else:
        # Stay at the rate specified in netcfg
        ptcl_name.tspt_rate = netcfg.tspt_rate / 1000
        ptcl_name.keyword['ssrate00'] = netcfg.tspt_rate / 1000

    # Update transport layer transmission rate
    if netcfg.b_rate_ctl == 'on':
        netcfg.l4_maximum_rate = new_rate * 1000 / 8  # Kbps -> Bps #7625
        netcfg.l4_maximum_packets_per_second = max(1, math.ceil(netcfg.l4_maximum_rate / netcfg.l4_size))

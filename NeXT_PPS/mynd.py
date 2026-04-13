########################################################
# mynode: single file that can run with different roles
########################################################
# !/usr/bin/python
#
# Copyright 2005,2006,2011,2013 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.

# data -> layer 4 -> layer 2 -> layer 1 -> USRP transmit/receiver

# Import the embedded libraries
import os
import sys
import inspect
import random
import struct
import socket
import signal
import string
import threading
from threading import Thread
import numpy as np
import time
import copy
import queue as Queue
from addpath import *
import pmt

# "from current dir"
import signalling
from network_config import *
from lyr2 import layer_2
from lyr4 import layer_4
import netcfg
import netlib
import ctl

import loading_file
import loading_file_old
import meas_delay_calc
import loading_tspt
import loading_phy
import updt_coord

# From another folder (NeXT_OS)
import ptcl_func  # Module defining functions for protocol parameter updating

# Global stop event for graceful shutdown
stop_event = threading.Event()

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

# Custom thread class with stop capability
class StoppableThread(Thread):
    """Thread class with a stop() method."""

    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class node(object):

    def __init__(self):
        self.threads = []  # Keep track of all threads
        self.running = True  # Flag for main loop

    def main(self, ptcl_func=ptcl_func):

        clear_terminal()

        options = get_args()

        node_name = options.role

        ndinfo = netlib.get_ndinfo(node_name)
        netcfg.nodeid = node_name

        print("Node information:", ndinfo, '\n')

        self.ip_usrp = netcfg.ip_usrp[ndinfo['index']]
        self.ip_pc = netcfg.ip_pc[ndinfo['index']]

        # B210 has no IP—ip_usrp is really the serial number
        self.serial_usrp = self.ip_usrp
        # print(self.ip_usrp, self.serial_usrp)

        self.udp_port_listen = netcfg.udp_port_listen[ndinfo['index']]

        self.udp_port_send = netcfg.udp_port_send[ndinfo['index']]

        # L2 INFO
        prev_hop_usrp = netcfg.prev_hop_usrp[ndinfo['index']]
        prev_hop_pc = netcfg.prev_hop_pc[ndinfo['index']]

        next_hop_usrp = netcfg.next_hop_usrp[ndinfo['index']]
        next_hop_pc = netcfg.next_hop_pc[ndinfo['index']]

        # L4 INFO
        source_usrp = netcfg.source_usrp[ndinfo['index']]
        source_pc = netcfg.source_pc[ndinfo['index']]

        dest_usrp = netcfg.dest_usrp[ndinfo['index']]
        dest_pc = netcfg.dest_pc[ndinfo['index']]

        prev_hop_usrp = netcfg.prev_hop_usrp[ndinfo['index']]
        next_hop_usrp = netcfg.next_hop_usrp[ndinfo['index']]
        # print("Next hop USRP serial:", next_hop_usrp)

        number_of_frames = netcfg.number_of_frames
        # print("Number of frames:", number_of_frames)

        l4_window = netcfg.l4_window[ndinfo['index']]  # XY: Not use
        l2_window = netcfg.l2_window[ndinfo['index']]

        """----------------Loading the algorithm files---------------"""

        # print('nodeid:', netcfg.nodeid)
        print("Network configuration scheme:", netcfg.scheme)

        node_rolee = netcfg.nd_type[netcfg.nd_id.index(netcfg.nodeid)]
        netcfg.node_role_id = node_rolee
        print("Node role:", node_rolee, node_name)

        # Load all the algorithms to a dictionary. This will be used later in signalling.py
        # XY: nd_id_map will be called only for transmitter and relay node
        if netcfg.scheme != 8:
            if node_rolee != 'rx':
                node_map = signalling.nd_id_map(netcfg.nodeid)
                netcfg.node_name_m = node_map
                # print("[TESTING]", node_map)
                # loading_file.load(node_map, node_rolee)
                loading_file_old.load(node_map, node_rolee)

        if netcfg.scheme == 8:
            if node_rolee != 'rx':
                node_map = signalling.nd_id_map(netcfg.nodeid)
                netcfg.node_name_m = node_map
                loading_file.load(node_map, node_rolee)
                loading_file.lag_update(node_map)
                node2 = node_map
                loading_phy.phy_alg_load(node2)
                if node_rolee == 'tx':
                    node3 = node_map
                    loading_tspt.tspt_alg_load(node3)

        """# On B210 (USB only) we don’t have IPs—use serials directly:
        # alias the node’s own USRP serial (ip_usrp holds it for USB devices)"""
        self.serial_usrp = self.ip_usrp

        # For a 2-node network, pick “source” vs. “dest” based on role:
        if node_rolee == 'tx':
            source_usrp = self.serial_usrp  # we’re the sender
            dest_usrp = next_hop_usrp  # peer is the receiver
        else:  # rx
            source_usrp = prev_hop_usrp  # peer sent to us
            dest_usrp = self.serial_usrp  # we’ll reply back

        """------------------------Update Coordinates--------------------------"""

        # This part of code is currently used only for scheme 9 which is mobility control
        if netcfg.scheme == 9:
            if node_rolee != 'rx':
                netcfg.idx_thisnode = ndinfo['index']
                updt_coord.coord()

        """Initialize signalling"""
        """Signalling defines the start_sending_socket, initialize_matrix and start_listen_socket functions, need to modify"""
        signalling.initialize_matrix(self)  # signalling matrix -> create dict include all serials
        signalling.start_sending_socket(self)  # UDP sockets -> create the socket
        print('--------------------- UDP SEND START -----------------------')

        "Initialize layer 4 and layer 2"
        self.l4 = layer_4(
            self.ip_pc,
            self.serial_usrp,
            number_of_frames,
            source_pc,
            source_usrp,
            dest_pc,
            dest_usrp,
            l4_window,
            self.sock_send,  # XY: defined in signalling.start_sending_socket()
            self.UDP_PORT_SEND  # XY: defined in self.udp_port_send
        )

        self.l2 = layer_2(
            number_of_frames,
            self.serial_usrp,  # serial_addr - B210 serial address
            ndinfo['type'],  # role
            prev_hop_usrp,  # layer_2_prev_hop_serial
            next_hop_usrp,  # layer_2_next_hop_serial
            options,  # tx_options
            options,  # rx_options
            l2_window,  # window
            self.sock_send,  # sock_send
            self.UDP_PORT_SEND  # udp_port
        )

        "Socket: start to listen the message"

        self.start_listening_socket_thread = Thread(target=signalling.start_listening_socket, args=(self,))
        self.start_listening_socket_thread.start()  # Start to listening to the acknowledgement messages
        print('\n------------------------UDP LISTEN START-----------------------', '\n')

        print('USRP:  ', self.ip_usrp, ' | ID index: ', ndinfo['index'], ' | Listening on:  ', self.udp_port_listen,
              "\n")

        ##############################################################
        # common to all roles
        ##############################################################
        self.l2.init_upper_queue(self.l4)
        self.l4.init_lower_queue(self.l2)
        print('# linked the two layers\n')

        self.l4.get_l2_info(self.l2)
        print('# l4 got information of l2\n')

        self.l2.init_thread()  # XY: initial function called the push down function as a thread
        print('# l2 threads initialized\n')

        self.l4.init_thread()
        print('# l4 threads initialized\n')

        self.role = ndinfo['type']
        netcfg.idx_thisnode = ndinfo['index']

        ptcl_func.updt_lnkgain()  # Get the gains for uplink and downlink ?

        "--------------------------Start signal transmitting---------------------------"
        # XY: Why we need this? What neighbors should we update?
        self.signalling_thread = Thread(target=signalling.periodic_update_neighbors, args=(self,))
        self.signalling_thread.start()
        print('---------------------------- SIGNALLING START ---------------------------')

        if ndinfo['type'] == 'tx' or ndinfo['type'] == 'relay':
            ctl.start_ctl_thread()

        if ndinfo['type'] == 'relay' or ndinfo['type'] == 'rx':
            pass

        # print("\n ######## -------- mynd.py -- RUN UP TO HERE -------- ######## \n")

        """------------------------------Transmitter only--------------------------------"""
        if ndinfo['type'] == 'tx':
            pktno_l4 = 0  # package to Layer 4 index

            # build payload as bytes, not str
            raw_payload = (netcfg.l4_size - netcfg.l4_header_length) * random.choice(string.digits)  # 256 - 42 = 214
            # print('raw payload: ', len(raw_payload), type(raw_payload), '\n')
            payload = raw_payload.encode('utf-8')

            if netcfg.l4_control_rate_flag == 1:  # XY: rate control flag 0 -> no control 1 - > limited rate
                print('MAX TRANSPORT RATE	l4 packet size ', netcfg.l4_size, '\n')
                print('MAX TRANSPORT RATE 	', netcfg.l4_maximum_rate, '\n')
                print('MAX TRANSPORT RATE 	packets per second to be input ', netcfg.l4_maximum_packets_per_second, '\n')

            while True:  # Threads are alive during this process
                if netcfg.l4_control_rate_flag == 1 and pktno_l4 % netcfg.l4_maximum_packets_per_second == 0:
                    time.sleep(1)

                timestamp = time.time()

                ip_bytes = self.ip_usrp.encode('utf-8').ljust(13, b'\x00')  # Encode USRP IP
                dst_bytes = dest_usrp.encode('utf-8').ljust(13, b'\x00')  # Encode Destination USRP IP
                packet = (struct.pack('l', pktno_l4) + ip_bytes + dst_bytes
                          + struct.pack('d', timestamp) + payload)  # 8 + 13 + 13 + 8 + payload

                # print(pktno_l4, "[MAIN FILE MYND DEBUGGING] L4 packet length: ", len(packet), packet, '\n')

                self.l4.down_queue.put(packet)

                if netcfg.node_role_id == 'tx':  # XY: Record the time for each packet
                    netcfg.tx_time_stamp_dict.update({pktno_l4: time.time()})

                if pktno_l4 == netcfg.l4_packets_to_send:  # XY: Total number of packets
                    break
                pktno_l4 += 1

        if ndinfo['type'] == 'relay' or ndinfo['type'] == 'rx':
            self.l2.start_l1_receiving_block()
            print('# started l2 rx chain\n')

    def cleanup(self):
        """Clean up resources and save data"""
        print('\n\nClosing all threads and sockets...')

        # Signal all threads to stop
        stop_event.set()
        self.running = False

        # Stop all threads gracefully
        for thread in self.threads:  # XY: does the created threads automatically add to the threads list?
            if hasattr(thread, 'stop'):
                thread.stop()

        # Wait for threads to finish (with timeout)
        for thread in self.threads:
            thread.join(timeout=2.0)

        # Stop GNU Radio blocks  XY: need to change
        if hasattr(self, 'l2') and hasattr(self.l2, 'l1_transmission_block'):
            try:
                self.l2.l1_transmission_block.stop()
                self.l2.l1_transmission_block.wait()
            except BrokenPipeError:
                pass

        # Close sockets
        if hasattr(self, 'sock_send'):
            try:
                self.sock_send.close()
            except BrokenPipeError:
                pass

        if hasattr(self, 'start_listening_socket_thread') and \
                hasattr(self.start_listening_socket_thread, 'sock_listen'):
            try:
                self.start_listening_socket_thread.sock_listen.close()
            except BrokenPipeError:
                pass

        # Save data
        self.save_data()

    def save_data(self):
        """Save performance data to files"""
        try:
            curr_dir = os.getcwd()
            scheme_folder = 'Scheme' + str(netcfg.scheme)
            pathh = os.path.join(curr_dir, 'plotting_data', scheme_folder)

            if not os.path.isdir(pathh):
                os.makedirs(pathh, exist_ok=True)

            # Define file names
            thpt_file_name = os.path.join(pathh, f'thrpt_{netcfg.nodeid}.npy')
            power_file_name = os.path.join(pathh, f'power_{netcfg.nodeid}.npy')
            meas_delay_file_name = os.path.join(pathh, f'measdelay_{netcfg.nodeid}.npy')
            rx_file_name = os.path.join(pathh, f'rxpkt{netcfg.nodeid}.npy')
            rate_file_name = os.path.join(pathh, f'rate_{netcfg.nodeid}.npy')
            theta_file_name = os.path.join(pathh, f'delay{netcfg.nodeid}.npy')

            # Save delay measurements if transmitter
            if netcfg.node_role_id == 'tx':
                meas_delay_calc.delay_cal_plot(meas_delay_file_name)

            # Save numpy arrays
            with open(thpt_file_name, 'wb') as f1:
                np.save(f1, netcfg.throughput_list)

            with open(power_file_name, 'wb') as f2:
                np.save(f2, netcfg.pwr_history)

            with open(theta_file_name, 'wb') as f3:
                np.save(f3, netcfg.delay_history)

            with open(rate_file_name, 'wb') as f4:
                np.save(f4, netcfg.rate_list)

            print("Data saved successfully")

        except Exception as e:
            print(f"Error saving data: {e}")

    def run_node(self):
        if __name__ == '__main__':
            try:

                # display next-step work
                if netcfg.disp_note == 1:
                    print('#############################################################################')
                    print(netcfg.note1)
                    print(netcfg.note2)
                    print('#############################################################################')
                    exit(0)

                self.main()
                while True:
                    time.sleep(100)
            # Replace the KeyboardInterrupt exception handler (around line 460) with:

            except KeyboardInterrupt:
                print('\n\n closing all threads, this closes all the open sockets')

                # Stop GNU Radio flowgraphs properly
                try:
                    if hasattr(self, 'l2') and hasattr(self.l2, 'l1_transmission_block'):
                        self.l2.l1_transmission_block.stop()
                        self.l2.l1_transmission_block.wait()
                except BrokenPipeError:
                    pass

                # Instead of using _Thread__stop(), set stop conditions
                try:
                    # For threads that have stop_condition attribute
                    for i in range(self.l2.window):
                        if self.l2.thread_pool[i] is not None:
                            self.l2.thread_pool[i].stop_condition = True

                    for i in range(self.l4.window):
                        if self.l4.thread_pool[i] is not None:
                            self.l4.thread_pool[i].stop_condition = True
                except BrokenPipeError:
                    pass

                # Record throughput history
                curr_dir = os.getcwd()

                scheme_folder = 'Scheme' + str(netcfg.scheme)

                pathh = curr_dir + '/plotting_data/' + scheme_folder
                if not os.path.isdir(pathh):
                    os.mkdir(pathh)

                thpt_file_name = curr_dir + '/' + 'plotting_data' + '/' + scheme_folder + '/' + 'thrpt_' + str(
                    netcfg.nodeid) + '.npy'
                power_file_name = curr_dir + '/' + 'plotting_data' + '/' + scheme_folder + '/' + 'power_' + str(
                    netcfg.nodeid) + '.npy'
                meas_delay_file_name = curr_dir + '/' + 'plotting_data' + '/' + scheme_folder + '/' + 'measdelay_' + str(
                    netcfg.nodeid) + '.npy'
                rx_file_name = curr_dir + '/' + 'plotting_data' + '/' + scheme_folder + '/' + 'rxpkt' + str(
                    netcfg.nodeid) + '.npy'
                rate_file_name = curr_dir + '/' + 'plotting_data' + '/' + scheme_folder + '/' + 'rate_' + str(
                    netcfg.nodeid) + '.npy'
                theta_file_name = curr_dir + '/' + 'plotting_data' + '/' + scheme_folder + '/' + 'delay' + str(
                    netcfg.nodeid) + '.npy'

                if netcfg.node_role_id == 'tx':
                    meas_delay_calc.delay_cal_plot(meas_delay_file_name)

                with open(thpt_file_name, 'wb') as f1:
                    np.save(f1, netcfg.throughput_list)

                with open(power_file_name, 'wb') as f2:
                    np.save(f2, netcfg.pwr_history)

                with open(theta_file_name, 'wb') as f3:
                    np.save(f3, netcfg.delay_history)

                with open(rate_file_name, 'wb') as f4:
                    np.save(f4, netcfg.rate_list)

                # Exit cleanly
                import sys
                sys.exit(0)

    def set_gain(self, new_gain):
        """
        Update transmit gain of the USRP

        Called By: signaling.periodic_update_neighbors()
        """

        new_gain = self.l2.l1_transmission_block.sink.set_gain(new_gain)
        return new_gain


# execute program
if __name__ == '__main__':
    mynode = node()

# Create a reference to the node in netcfg so the node can be accessible from other files
netcfg.thisnode = mynode

mynode.run_node()

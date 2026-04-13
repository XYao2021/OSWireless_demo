"""
                        LAYER 2 (Modified for B210 USRP)
"""
import sys
import os
sys.path.insert(0, './physical_layer/transmitter')     # Relative path
sys.path.insert(0, './physical_layer/receiver')

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from USRP_Transmitter import *
from USRP_Receiver import *
from ntwklyr import network_layer
from netlib import MyThread
import threading
from threading import Thread
import socket
import time
import struct
import sys
import numpy as np
# Import files in same folder
import netcfg
import chncod
import csi
import signalling

# from pkt_xmt import pkt_xmt

# Define threads for signaling
ack_l2_received = threading.Event()
ack_l2_received_control = threading.Event()

class layer_2(network_layer):
    """
    Layer 2 implementation for B210 USRP devices.

    This class implements the network layer 2 functionality for B210 USRP devices
    which use serial numbers for addressing instead of IP addresses. It maintains
    the same general functionality as the N-series implementation but adapts the
    addressing scheme for B210 devices.
    """

    def __init__(self,
                 number_of_frames,
                 serial_addr,  # B210 serial address
                 role,  # tx / rx / relay
                 layer_2_prev_hop_serial='',
                 layer_2_next_hop_serial='',
                 tx_options='',
                 rx_options='',
                 window=1,
                 sock_send='',
                 udp_port=''
                 ):

        network_layer.__init__(self, "layer_2")

        # Basic parameters
        self.number_of_frames = number_of_frames  # Number of l2 packets that compose an upper layer packet
        self.tx_options = tx_options
        self.rx_options = rx_options

        # B210 addressing
        self.serial_addr = serial_addr  # B210 serial address
        self.role = role

        # Neighbor node information
        self.layer_2_prev_hop_serial = layer_2_prev_hop_serial
        self.layer_2_next_hop_serial = layer_2_next_hop_serial

        # Packet parameters
        self.buffer_size = 1024  # Normally 1024, but we want fast response
        self.packet_size = netcfg.l2_size
        self.block_size = netcfg.l2_size_block

        # Socket for sending acknowledgments (if the node is a receiver)
        # XY: if role is relay, need to initial transmit and receive function at the same time
        if self.role == 'rx' or self.role == 'relay':
            self.send_previous_hop_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Initialize transmission block (if the node is a transmitter)
        if self.role == 'tx' or self.role == 'relay':
            print(f"txopron size, {self.packet_size}")
            if self.role == "tx":
                tx_args = "serial=" + netcfg.serial_usrp_src1
                tx_subdev = "A:A"
                repeat_times = 2
            else:
                tx_args = "serial=" + netcfg.serial_usrp_rly1
                tx_subdev = "A:B"
                repeat_times = 2
            # XY :define the self.TX here using new physical layer -> create the transmitter
            self.l1_transmission_block = USRPTransmitter(
                                                        # USRP settings (matching your C++ defaults)
                                                        tx_freq=920e6,          # 2.412 GHz
                                                        tx_rate=1e6,              # 1 MSPS
                                                        tx_gain=30.0,             # 20 dB
                                                        tx_bw=500e3,              # 500 kHz
                                                        tx_args=tx_args,               # Auto-detect
                                                        tx_antenna="TX/RX",
                                                        tx_subdev=tx_subdev,
                                                        ref="internal",

                                                        # Message settings
                                                        num_bits=1024,
                                                        interval=2000,            # 1 second between packets
                                                        continuous=False,         # Not continuous
                                                        repeat_times=repeat_times,

                                                        # Modulation settings
                                                        scheme="DBPSK",
                                                        add_preamble=True,
                                                        preamble_length=5,        # m=5 for m-sequence
                                                        preamble_type="m-sequence",

                                                        # Filter settings
                                                        filter_type="rrc",
                                                        symbol_rate=0.8e6,
                                                        num_taps=151,
                                                        U=5,
                                                        D=4,
                                                        roll_off=0.25,
                                                        num_threads=1)
            self.l1_transmission_block.start("bits")

        # Window and socket parameters
        self.window = window  # XY: not used in the following codes
        self.sock_send = sock_send
        self.UDP_PORT = udp_port  # XY: not used in the following codes

        # Channel coding rate dictionary (per frequency)
        self.ch_coding_rate = {}

        if self.role == 'tx':
            self.ch_coding_rate[self.tx_options.tx_freq] = netcfg.ch_coding_rate[2]
        elif self.role == 'relay':
            self.ch_coding_rate[self.tx_options.tx_freq] = netcfg.ch_coding_rate[2]
            self.ch_coding_rate[self.rx_options.rx_freq] = netcfg.ch_coding_rate[2]
        elif self.role == 'rx':
            self.ch_coding_rate[self.rx_options.rx_freq] = netcfg.ch_coding_rate[2]

        # Initialize coders (per frequency)
        self.coder = {}

        if self.role == 'tx':
            self.coder[self.tx_options.tx_freq] = chncod.initialize_RSCoder(
                self.ch_coding_rate[self.tx_options.tx_freq])
        elif self.role == 'relay':
            self.coder[self.tx_options.tx_freq] = chncod.initialize_RSCoder(
                self.ch_coding_rate[self.tx_options.tx_freq])
            self.coder[self.rx_options.rx_freq] = chncod.initialize_RSCoder(
                self.ch_coding_rate[self.rx_options.rx_freq])
        elif self.role == 'rx':
            self.coder[self.rx_options.rx_freq] = chncod.initialize_RSCoder(
                self.ch_coding_rate[self.rx_options.rx_freq])

        # Performance counters
        self.transmitted_packets = 1
        self.successfully_transmitted_packets = 1

        # Throughput measurement
        self.last = time.time()
        self.A = 0

    def send_l2_feedback(self, packet, number, target_addr, port):
        """Send Layer 2 acknowledgment packet"""
        # Pack message type (2 for L2 feedback)
        packet = struct.pack('h', 2) + packet
        try:
            self.sock_send.sendto(packet, (target_addr, port))
            # print("[DEBUGGING] REACH HERE!!!!!!!!!!!", packet, (target_addr, port))  # XY: Reached here, message content is correct
        except socket.error as exc:
            print(f"Error sending L2 feedback: {exc}")
            pass

    def send_cc_message(self, packet, number, target_addr, port):
        """Send channel coding control message"""
        # Pack message type (-2 for channel coding message)
        packet = struct.pack('h', -2) + packet
        try:
            self.sock_send.sendto(packet, (target_addr, port))
        except socket.error as exc:
            print(f"Error sending CC message: {exc}")
            pass

    def send_cc_feedback(self, packet, number, target_addr, port):
        """Send channel coding feedback"""
        # Pack message type (-1 for channel coding feedback)
        packet = struct.pack('h', -1) + packet
        try:
            self.sock_send.sendto(packet, (target_addr, port))
        except socket.error as exc:
            print(f"Error sending CC feedback: {exc}")
            pass

    def received_cc_ack(self):
        """Signal that a channel coding acknowledgment was received"""
        globals()["ack_l2_received_control"].set()

    def received_l2_feedback(self, mac_ack):
        """Process received Layer 2 acknowledgment"""
        # Extract packet number from the first 2 bytes
        (mac_ack_pktno,) = struct.unpack('h', mac_ack[0:2])

        # Extract source serial (using a fixed size field for serial)
        # B210 serials are typically 8-10 characters, but we use 16 bytes for safety
        mac_source_serial = mac_ack[2:15].strip(b'\x00')
        # print("[ACK DEBUGGING] Reached received_l2_feedback ", mac_ack_pktno, mac_source_serial)

        # Check if this ack is for our waiting packet
        if mac_ack_pktno == self.waiting_ack_mac_pktno and mac_source_serial.decode() == self.serial_addr:
            globals()["ack_l2_received"].set()
        elif mac_ack_pktno == -1:
            # Control message acknowledgment
            globals()["ack_l2_received_control"].set()

    def l2_capacity_calc(self):
        """Calculate Layer 2 capacity in kbps"""
        print("[CAPACITY COMPUTATION DEBUGGING] payload size and time taken are ", netcfg.payload_size, netcfg.time_taken)
        capacity = (self.successfully_transmitted_packets * netcfg.payload_size) / (1000 * netcfg.time_taken)
        print("[CAPACITY COMPUTATION DEBUGGING] capacity ", capacity, '\n')
        return capacity

    def check_PER(self):
        """Calculate Packet Error Rate"""
        netcfg.l2_capacity = self.l2_capacity_calc()
        print("[CAPACITY COMPUTATION DEBUGGING] successfully and total packets are ", self.successfully_transmitted_packets, '/', self.transmitted_packets)
        return 1 - float(self.successfully_transmitted_packets) / self.transmitted_packets

    def check_change_rate_needed(self):
        """Check if channel coding rate needs to be changed based on PER"""
        # Default: no increase needed
        outcome = False
        new_rate = netcfg.ch_coding_rate[0]
        current_index = netcfg.ch_coding_rate.index(self.ch_coding_rate[self.tx_options.tx_freq])

        # Check PER value
        PER = self.check_PER()
        print("[CHECK CHANGE RATE NEEDED DEBUGGING] Packet Error Rate (PER) is ", PER, "Required Range (", netcfg.l2_th_PER_low, ',', netcfg.l2_th_PER_high, ')')

        # Check positioning between threshold
        if PER > netcfg.l2_th_PER_high:
            # Increase the rate by one step (more protection)
            new_index = min(current_index + 1, len(netcfg.ch_coding_rate) - 1)
            if new_index != current_index:
                new_rate = netcfg.ch_coding_rate[new_index]
                outcome = True
        elif PER < netcfg.l2_th_PER_low:
            # Decrease the rate by 1 step (less protection)
            new_index = max(current_index - 1, 0)
            if new_index != current_index:
                new_rate = netcfg.ch_coding_rate[new_index]
                outcome = True
        else:
            outcome = False

        return outcome, new_rate

    def check_decrease_rate_needed(self, act_rt):
        """Legacy method for backward compatibility"""
        # Default: no decrease needed
        outcome = False
        new_rate = self.ch_coding_rate[self.tx_options.tx_freq]
        return outcome, new_rate

    def start_l1_receiving_block(self):
        """Start the physical layer receive processing"""  # Only for receiver
        # ----------------------- This section need to be rewritten ------------------#
        if self.role == "rx":
            rx_args = "serial=" + netcfg.serial_usrp_dst1
            rx_subdev = "A:0"
            threshold = 16.0
            energy_threshold = 5.0e-7
            rx_gain = 20.0
        else:
            rx_args = "serial=" + netcfg.serial_usrp_rly1
            rx_subdev = "A:A"
            threshold = 5.0
            energy_threshold = 1.0e-6
            rx_gain = 30.0

        self.l1_receiving_block = USRPReceiver(
                                            rx_channel=0,
                                            samps_per_buff=10000,
                                            num_recv_request=0,
                                            rx_freq=920e6,
                                            rx_rate=1e6,
                                            rx_gain=rx_gain,
                                            rx_bw=500e3,
                                            settling_time=0.2,
                                            uhd_timeout=1000.0,
                                            rx_args=rx_args,
                                            rx_ant="RX2",
                                            rx_subdev=rx_subdev,
                                            ref="internal",
                                            otw="sc16",
                                            data_type="float",

                                            # Energy Detection and AGC parameters
                                            energy_packet_size=1380,
                                            IIR_window_size=1,
                                            alpha=0.96,
                                            energy_threshold=energy_threshold,  # Fixed threshold
                                            IIR_threshold_multiplier=8.0,
                                            IIR_threshold_adaptive=False,  # Disable adaptive
                                            AGC_type="Feed",

                                            # Filter Parameters
                                            num_taps=151,
                                            U=4,
                                            D=1,
                                            num_threads=1,
                                            symbol_rate=0.8e6,
                                            roll_off=0.25,
                                            filter_type="rrc",

                                            # Synchronization Parameters
                                            recv_msg_len=1025,
                                            sps_sync=5,
                                            sync_threshold=threshold,

                                            # Demodulation Parameters
                                            preamble_length=5,
                                            add_preamble=True,
                                            preamble_type="m-sequence",
                                            demod_scheme="DBPSK")

        # Update reference to this receiver block in netcfg
        netcfg.obj_rcvr_blk = self.l1_receiving_block

        success = self.l1_receiving_block.start()
        if not success:
            print("Failed to start receiver!")
            sys.exit(1)

        packet_count = 0
        running = True
        try:
            while running:
                msg = self.l1_receiving_block.receive_bits()
                if msg is not None:
                    packet_count += 1
                    if packet_count < 2:
                        pass
                    else:
                        message = bytes(msg)
                        print(self.serial_addr, len(message), "has: ", message)
                        # try:
                        #     packet_mac = struct.unpack('H', message[0:2])[0]
                        #     source_serial = message[2:15].rstrip(b'\x00').decode('utf-8')
                        #     dest_serial = message[15:28].rstrip(b'\x00').decode('utf-8')
                        #
                        #     if dest_serial == self.serial_addr:
                        #         # print("[DEST] I am the real destination")
                        #         # print("[DEST] The packet_mac is: ", packet_mac, '\n')
                        #         # print("[DEST] The source_serial is: ", source_serial, '\n')
                        #         print("[DEST] The dest_serial is: ", dest_serial, '\n')
                        #         # print("[RELAY PRINTING] The payload is: ", payload, '\n')
                        #         # success = 0
                        #         # # Apply channel coding (error correction)
                        #         # (corrected_packet, success) = chncod.deduct_chncod(
                        #         #     self.coder[self.rx_options.rx_freq],
                        #         #     message,
                        #         #     self.ch_coding_rate[self.rx_options.rx_freq]
                        #         # )
                        #         #
                        #         # print('corrected_packet:', corrected_packet)
                        #         # print('success:', success)
                        #
                        #         self.up_queue.put(message, True)
                        #     else:
                        #         # print("[TRANSFER] Pushing the packets to real destination \n")
                        #         # print("[TRANSFER] The packet_mac is: ", packet_mac, '\n')
                        #         # print("[TRANSFER] The source_serial is: ", source_serial, '\n')
                        #         print("[TRANSFER] The dest_serial is: ", dest_serial, '\n')
                        #         # print("[RELAY PRINTING] The payload is: ", payload, '\n')
                        #         byte_array = np.frombuffer(message, dtype=np.uint8)
                        #         bits = np.unpackbits(byte_array)  # numpy array of bits
                        #         self.l1_transmission_block.send_bits(bits)
                        #
                        # except UnicodeDecodeError:
                        #     time.sleep(0.01)
                        #     continue

                        packet_mac = struct.unpack('H', message[0:2])[0]
                        source_serial = message[2:15].rstrip(b'\x00').decode('utf-8')
                        dest_serial = message[15:28].rstrip(b'\x00').decode('utf-8')

                        # payload = msg[28:len(msg) - 1].decode('utf-8')

                        if dest_serial == self.serial_addr:
                            # print("[DEST] I am the real destination")
                            # print("[DEST] The packet_mac is: ", packet_mac, '\n')
                            # print("[DEST] The source_serial is: ", source_serial, '\n')
                            print("[DEST] The dest_serial is: ", dest_serial, '\n')
                            # print("[RELAY PRINTING] The payload is: ", payload, '\n')
                            # success = 0
                            # # Apply channel coding (error correction)
                            # (corrected_packet, success) = chncod.deduct_chncod(
                            #     self.coder[self.rx_options.rx_freq],
                            #     message,
                            #     self.ch_coding_rate[self.rx_options.rx_freq]
                            # )
                            #
                            # print('corrected_packet:', corrected_packet)
                            # print('success:', success)

                            self.up_queue.put(message, True)
                        else:
                            # print("[TRANSFER] Pushing the packets to real destination \n")
                            # print("[TRANSFER] The packet_mac is: ", packet_mac, '\n')
                            # print("[TRANSFER] The source_serial is: ", source_serial, '\n')
                            print("[TRANSFER] The dest_serial is: ", dest_serial, '\n')
                            # print("[RELAY PRINTING] The payload is: ", payload, '\n')
                            byte_array = np.frombuffer(message, dtype=np.uint8)
                            bits = np.unpackbits(byte_array)  # numpy array of bits
                            self.l1_transmission_block.send_bits(bits)
                else:
                    # No message available, sleep briefly to avoid busy-waiting
                    time.sleep(0.01)

        except KeyboardInterrupt:
            receiver.stop()
            print("\n[PYTHON] KeyboardInterrupt caught")

    def send_pkt(self, payload, eof=True):  # Called  eof: end of the queue, originally False
        """Send a packet at the physical layer with channel coding"""
        # Add channel coding -> XY: Can we use this directly? Need to modified
        # payload_chncod = chncod.add_chncod(
        #     self.coder[self.tx_options.tx_freq],
        #     payload,
        #     self.ch_coding_rate[self.tx_options.tx_freq])  # add the protection -> encoder

        payload_chncod = payload  # XY: The RS encoding will change the message length, this needs to be rewritten!!!

        netcfg.payload_size = len(payload_chncod)

        # Send the packet
        # Convert python bytes to bits -> easy to modify on C++ side
        byte_array = np.frombuffer(payload_chncod, dtype=np.uint8)
        bits = np.unpackbits(byte_array)  # numpy array of bits

        # source = netcfg.serial_usrp_src1.encode().ljust(13, b'\x00')
        # dest = netcfg.serial_usrp_dst1.encode().ljust(13, b'\x00')
        # payload = "This is the test message of Xin Yao from University of Florida, Electrical and Computer Engineering Department! [TESTING] !!"
        # payload = payload.encode()
        # message = source + dest + payload
        # byte_array = np.frombuffer(message, dtype=np.uint8)
        # bits = np.unpackbits(byte_array)  # numpy array of bits

        # print("[TRANSMITTING]: ", len(payload), payload, '\n')
        # print("[TRANSMITTING]: ", len(bits), type(bits[0]), '\n')
        # print("[TRANSMITTER SEND CHNCOD DEBUGGING] payload_chncod: ", payload_chncod, type(payload_chncod),
        #       len(payload_chncod), len(bits))

        # ----------------------- This section need to be rewritten ------------------#
        self.l1_transmission_block.send_bits(bits)
        # for i in range(2):
        #     self.l1_transmission_block.send_bits(bits)
        #     time.sleep(10)
        # self.l1_transmission_block.stop()
        # print('Transmission is finished after waiting ..................')
        return True

    def pass_up(self):
        """
        Process received packets and pass them up to higher layers

        This method gets packets from the up_queue, reassembles them,
        and passes the complete packet to the upper layer.
        """
        up_packet = b''
        pktno_mac_old = 0
        packet_beginning_flag = 0

        # Process packets until a complete message is received
        while True:
            mac_packet = self.up_queue.get(True)
            if len(mac_packet) != 128:
                print('L2', len(mac_packet), 'must be 128')
                continue

            # Extract packet number
            (pktno_mac,) = struct.unpack('h', mac_packet[0:2])

            # print("[RECEIVER LAYER 2 DEBUGGING] The received message: ", pktno_mac, len(mac_packet), mac_packet)  # XY: Reached here, message contents are correct

            """
            # Modified packet structure for B210:
            # - 2 bytes: packet number
            # - 13 bytes: source serial
            # - 13 bytes: destination serial
            # - remaining: data
            """
            l4_header = struct.pack('l', pktno_mac).ljust(8, b'\x00') + mac_packet[2:28] + struct.pack('d', time.time())

            mac_source_serial = mac_packet[2:15].strip(b'\x00').decode()
            mac_dest_serial = mac_packet[15:28].strip(b'\x00').decode()

            # print("[RECEIVED MAC SYSTEM] pktno_mac: ", pktno_mac)
            # print("[RECEIVED MAC SYSTEM] mac_source_serial: ", mac_source_serial)
            # print("[RECEIVED MAC SYSTEM] mac_dest_serial: ", mac_dest_serial)
            # print("[RECEIVED MAC SYSTEM] current serial_addr: ", self.serial_addr)

            # Check if the packet is for this device
            if mac_dest_serial == self.serial_addr:
                # FRAME 0 OF A NEW PACKET (start of message)
                # print("[DEBUGGING] Reached HERE!!!!! ", self.role)
                if pktno_mac == 1 and packet_beginning_flag == 0:
                    packet_beginning_flag = 1
                    feedback_mac = mac_packet[0:28]  # Header portion for feedback

                    pktno_mac_old = pktno_mac
                    up_packet += mac_packet[28:]  # Data portion
                    mac_packet = ''

                    # Send feedback if we're a receiver
                    if (self.role == 'rx' or self.role == 'relay'):
                        # Find the address to send acknowledgment to
                        target_addr = netcfg.serial_to_addr.get(mac_source_serial)  # XY: read the key word
                        port = netcfg.serial_to_port.get(mac_source_serial)  # XY: check the source is current or not?

                        # print("[DEBUGGING] Reached HERE!!!!! ", target_addr, port)

                        if target_addr and port:
                            self.send_l2_feedback(feedback_mac, pktno_mac, target_addr, port)
                    # print("[INSIDE THE LOOP 11111! RECEIVER LAYER 2 DEBUGGING] The feedback_mac is: ", pktno_mac, feedback_mac)
                    # print("[INSIDE THE LOOP 11111! RECEIVER LAYER 2 DEBUGGING] The up_packet is: ", pktno_mac, up_packet)

                # FRAME CONTIGUOUS TO THE PREVIOUS (continuation of message)
                elif packet_beginning_flag == 1 and pktno_mac == (pktno_mac_old + 1) % (self.number_of_frames + 1):
                    feedback_mac = mac_packet[0:28]  # Header portion for feedback

                    pktno_mac_old = pktno_mac
                    up_packet += mac_packet[28:]  # Data portion
                    mac_packet = ''

                    # Send feedback if we're a receiver
                    if (self.role == 'rx' or self.role == 'relay'):
                        # Find the address to send acknowledgment to
                        target_addr = netcfg.serial_to_addr.get(mac_source_serial)
                        port = netcfg.serial_to_port.get(mac_source_serial)

                        if target_addr and port:
                            self.send_l2_feedback(feedback_mac, pktno_mac, target_addr, port)

                    # print("[INSIDE THE LOOP 22222! RECEIVER LAYER 2 DEBUGGING] The up_packet is: ", pktno_mac, up_packet)

                    # If this is the last frame of the message, break
                    if pktno_mac == self.number_of_frames:
                        break

                # CONTROL MESSAGE
                elif pktno_mac == -1:
                    print('HANDLING code rate EXCEPTION')
                    self.handle_update_rate_exception(mac_packet)

                    if (self.role == 'rx' or self.role == 'relay'):
                        # Find the address to send acknowledgment to
                        target_addr = netcfg.serial_to_addr.get(mac_source_serial)
                        port = netcfg.serial_to_port.get(mac_source_serial)

                        if target_addr and port:
                            self.send_cc_feedback(mac_packet, pktno_mac, target_addr, port)

                    continue

                # OUT OF ORDER FRAME
                else:
                    # If this is the last frame and we're in a packet, end
                    if pktno_mac == self.number_of_frames and packet_beginning_flag != 0:
                        break
                    continue

        return l4_header + up_packet, 1

    def pass_down(self, down_packet, index):  # Check pass_down: push data to usrp (called)
        """
        Send a packet to the lower layer and handle retransmissions

        This method sends a packet and waits for acknowledgment, retransmitting
        if necessary up to a specified threshold.
        """
        act_rt = 0  # Retransmission counter

        # Extract packet number
        (pktno_mac,) = struct.unpack('h', down_packet[0:2])
        start_time = time.time()

        if self.role == 'tx' or self.role == 'relay':

            self.send_pkt(payload=down_packet)  # Called l1 path transmission, return True

            self.transmitted_packets = self.transmitted_packets + 1
            self.waiting_ack_mac_pktno = pktno_mac

            while 1:
                # Reset counters periodically to avoid overflow
                if self.transmitted_packets % 100 == 0:
                    self.transmitted_packets = 1
                    self.successfully_transmitted_packets = 1

                # Check channel coding rate periodically
                if self.transmitted_packets % 5 == 0:
                    elapsed_time = time.time() - start_time
                    netcfg.time_taken = elapsed_time

                    # Check if coding rate needs adjustment
                    outcome, new_rate = self.check_change_rate_needed()
                    if outcome:
                        self.coding_update(new_rate, 1)  # 1 -> Update transmitter's coding rate

                # Wait for acknowledgment
                globals()["ack_l2_received"].wait(netcfg.timeout_l2)  # False now, error is here
                """
                Global keys: ['__name__', '__doc__', '__package__', '__loader__', '__spec__', '__file__', '__cached__', '__builtins__',
                              'network_layer', 'my_top_block_tx', 'my_top_block_rx', 'MyThread', 'threading', 'Thread', 'socket', 'time', 
                              'struct', 'sys', 'digital', 'netcfg', 'chncod', 'csi', 'signalling', 'benchmark_tx_narrow', 'benchmark_rx_narrow',
                               'ack_l2_received', 'ack_l2_received_control', 'layer_2']
                """

                print("[LAYER 2 DEBUGGING] This is the index: ", index, globals()["ack_l2_received"].isSet(), '\n')  # XY: Successfully received the pktno_mac = 1

                if globals()["ack_l2_received"].isSet():
                    # Acknowledgment received
                    globals()["ack_l2_received"].clear()

                    # Update packet counter for throughput calculation  XY: Reach here
                    if netcfg.n_pkt_cnt < 10:
                        netcfg.n_pkt_cnt = netcfg.n_pkt_cnt + 1
                    else:
                        # Calculate throughput
                        self.t1 = time.time()
                        delta_t = self.t1 - self.last
                        if delta_t == 0:
                            a = 0
                        else:
                            a = netcfg.n_pkt_cnt / delta_t

                        # Update running average of throughput
                        self.A = self.A * netcfg.l2_th_coeff + (1 - netcfg.l2_th_coeff) * a
                        netcfg.lnk_thpt = self.A
                        self.last = self.t1
                        netcfg.n_pkt_cnt = 0

                    # Increment successful transmission counter
                    self.successfully_transmitted_packets = self.successfully_transmitted_packets + 1
                    # print("[ACK RECEIVING DEBUGGING] HERE", self.successfully_transmitted_packets)  # XY: Successfully reached here
                    break

                elif act_rt < netcfg.l2_retransmission_threshold:
                    # No acknowledgment - retransmit
                    act_rt += 1
                    print('L2 try for', act_rt, ' packet ', pktno_mac)
                    # print("[TRANSMITTING DEBUGGING] HERE: ", pktno_mac, down_packet)
                    self.send_pkt(payload=down_packet)
                    self.transmitted_packets = self.transmitted_packets + 1

                else:
                    # Retransmission threshold reached
                    print("FATAL ERROR: L2 retransmission limit reached for l2 paktno ", pktno_mac)
                    break

            # print("[DEBUG 1] Just broke from while loop")  # XY: The loop is broken, and called again

    def get_number_of_frames(self):
        """Return the number of frames per message"""
        return self.number_of_frames

    def get_l2_pkt_size(self):
        """Return the layer 2 packet size"""
        return self.packet_size

    def get_layer_2_next_hop_serial(self):
        """Return the next hop serial address"""
        return self.layer_2_next_hop_serial

    def get_layer_2_prev_hop_serial(self):
        """Return the previous hop serial address"""
        return self.layer_2_prev_hop_serial

    def get_layer_2_serial(self):
        """Return this device's serial address"""
        return self.serial_addr

    def coding_update(self, ch_coding_rate, send_update):
        """
        Update the channel coding rate

        If send_update is 1, send the update to the neighbor.
        If send_update is 0, apply a received update.
        """
        if send_update == 1:  # The update is to be sent
            print('\n #### TRANSMITTER RATE UPDATE', ch_coding_rate, '########\n')

            # Create coding rate update message
            # Format: packet number (-1) + source serial + destination serial + coding rate
            source_serial = self.serial_addr.encode().ljust(13, b'\x00')
            dest_serial = self.layer_2_next_hop_serial.encode().ljust(13, b'\x00')

            chn_code_rate_update = struct.pack('h', -1) + source_serial + dest_serial + struct.pack('f', ch_coding_rate)

            # Find the address to send to
            target_addr = netcfg.serial_to_addr.get(self.layer_2_next_hop_serial)
            port = netcfg.serial_to_port.get(self.layer_2_next_hop_serial)

            if target_addr and port:
                # Send the message
                self.send_cc_message(chn_code_rate_update, -2, target_addr, port)

                # Wait for acknowledgment, with retransmissions if needed
                act_rt = 0
                while 1:
                    globals()["ack_l2_received_control"].wait(netcfg.timeout_l2 * 2)

                    if globals()["ack_l2_received_control"].isSet():
                        # Acknowledgment received
                        globals()["ack_l2_received_control"].clear()
                        break
                    elif act_rt < netcfg.l2_retransmission_threshold * 2:
                        # Retransmit
                        act_rt += 1
                        self.send_cc_message(chn_code_rate_update, -2, target_addr, port)
                    else:
                        # Retransmission threshold reached
                        print("L2 Control retransmission limit reached")
                        break

            # Update local coding rate
            self.ch_coding_rate[self.tx_options.tx_freq] = ch_coding_rate
            self.coder[self.tx_options.tx_freq] = chncod.initialize_RSCoder(
                self.ch_coding_rate[self.tx_options.tx_freq])

            # print("[CODING UPDATE DEBUGGING] local coding rate update: ", ch_coding_rate)

        elif send_update == 0:  # Update has been received
            # Apply the received update
            self.ch_coding_rate[self.rx_options.rx_freq] = ch_coding_rate
            self.coder[self.rx_options.rx_freq] = chncod.initialize_RSCoder(
                self.ch_coding_rate[self.rx_options.rx_freq])
            print('\n ######## RECEIVED RATE UPDATE', ch_coding_rate, '########\n')

    def handle_update_rate_exception(self, payload):
        """Process a received coding rate update message"""
        # Extract the new coding rate from the message
        # Format: packet number (2) + source serial (13) + destination serial (13) + coding rate (4)
        (new_rate,) = struct.unpack('f', payload[28:32])

        # Apply the update
        self.coding_update(new_rate, 0)  # XY: Update receiver's coding rate

        # Send acknowledgment
        mac_source_serial = payload[2:15].strip(b'\x00').decode()
        target_addr = netcfg.serial_to_addr.get(mac_source_serial)
        port = netcfg.serial_to_port.get(mac_source_serial)

        if target_addr and port:
            self.send_cc_feedback(payload, -1, target_addr, port)

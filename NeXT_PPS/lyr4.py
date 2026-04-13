"""
                        LAYER 2 (Modified for B210 USRP)
"""
import numpy as np
import netlib
import socket
import time
import struct
import sys
import netcfg
from ntwklyr import network_layer
import threading
from threading import Thread

l4_lower_queue_access = threading.Lock()
l4_dict_pktno_thread_access = threading.Lock()


class layer_4(network_layer):
	"""
	Layer 4 implementation for B210 USRP devices.

	This class implements network layer 4 functionality for B210 USRP devices
	which use serial numbers for addressing instead of IP addresses. It maintains
	the same general functionality as the N-series implementation but adapts the
	addressing scheme for B210 devices.
	"""

	def __init__(self,
				 serial_pc,
				 serial_usrp,
				 number_of_frames='',
				 layer_4_source_serial_pc='',
				 layer_4_source_serial_usrp='',
				 layer_4_dest_serial_pc='',
				 layer_4_dest_serial_usrp='',
				 window=1,
				 sock_send='',
				 udp_port=''):

		network_layer.__init__(self, "layer_4")

		self.number_of_frames = number_of_frames  # number of l4 packet that compose an upper layer packet

		self.serial_pc = serial_pc
		self.serial_usrp = serial_usrp

		self.layer_4_source_serial_usrp = layer_4_source_serial_usrp
		self.layer_4_source_serial_pc = layer_4_source_serial_pc
		self.layer_4_dest_serial_usrp = layer_4_dest_serial_usrp
		self.layer_4_dest_serial_pc = layer_4_dest_serial_pc

		self.buffer_size = 1024  # Normally 1024, but we want fast response

		# ack sending thread
		self.ack_send_to_source_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		self.window = window  # XY: use in receive L4 feedback function
		self.t1 = time.time()

		self.sock_send = sock_send
		self.UDP_PORT = udp_port

	def send_l4_feedback(self, packet, number, target_addr, port):
		"""Send Layer 4 acknowledgment packet"""
		packet = struct.pack('h', 4) + packet
		try:
			self.sock_send.sendto(packet, (target_addr, port))
			netcfg.n_tot += 1  # Guan added: total number of correct packets

			print('SENT L4 ACK ', number, 'at ', target_addr, ' PORT', port)

			# Measure throughput every 5 packets
			if netcfg.n_tot >= 5:
				cur_time = time.time()
				run_time = cur_time - netcfg.time_start  # Elapsed time in second
				time_interval = cur_time - netcfg.prev_time

				print('Throughput [packet/s]:', netcfg.n_tot / time_interval)
				netcfg.throughput_list.append(netcfg.n_tot / time_interval)

				# Send the message to the plotting laptop via UDP socket XY: What does this message for ?
				message = struct.pack('f', float(netcfg.n_tot) / time_interval)

				netcfg.n_tot = 0
				netcfg.prev_time = cur_time

		except socket.error as exc:
			print(f"Error sending L4 feedback: {exc}")
			pass

	def initialize_received_l4_feedback(self):
		"""Initialize feedback tracking"""
		self.waiting_l4_ack_pktno = 0
		print('l4 feedback initialized')

	def received_l4_feedback(self, ack_l4):
		"""Process received Layer 4 acknowledgment"""
		(l4_ack_pktno,) = struct.unpack('l', ack_l4[:8])
		print('## L4 RECEIVED ACK ', l4_ack_pktno)

		if (self.waiting_l4_ack_pktno + self.window) > l4_ack_pktno >= self.waiting_l4_ack_pktno:  # check acks for the whole window
			timestamp_2 = time.time()
			self.waiting_l4_ack_pktno += 1

			# Modified for B210: Using 13-byte fields for serial numbers
			# Byte positions: 8-21 for source serial, 21-34 for destination serial

			l4_packet_sender = ack_l4[8:21].strip(b'\x00').decode()  # Source serial
			l4_packet_receiver = ack_l4[21:34].strip(b'\x00').decode()  # Destination serial
			(timestamp,) = struct.unpack('d', ack_l4[34:42])  # Timestamp after serials

			# print("[RECEIVER ACK L4 DEBUGGING SOURCE] packet_source: ", l4_packet_sender)
			# print("[RECEIVER ACK L4 DEBUGGING DESTINATION] packet_destination: ", l4_packet_receiver)
			# print("[RECEIVER ACK L4 DEBUGGING SOURCE] timestamp: ", timestamp)

			# Store the timestamp for the ack message rxd
			netcfg.ack_time_stamp_dict.update({l4_ack_pktno: timestamp})

			if l4_packet_sender == self.serial_usrp:
				# Check if l4_ack_pktno is still active, if not, no need to set the thread
				if l4_ack_pktno in self.dict_pktno_thread:
					self.dict_thread_signal[self.dict_pktno_thread[l4_ack_pktno]].set()

				l4_dict_pktno_thread_access.acquire()  # ACQUIRE the dict
				if l4_ack_pktno in self.dict_pktno_thread:
					del self.dict_pktno_thread[l4_ack_pktno]
				l4_dict_pktno_thread_access.release()  # RELEASE the dict_pktno_thread

				if l4_ack_pktno == netcfg.l4_packets_to_send:
					self.t2 = time.time()
					print(self.t2 - self.t1, ' for ', netcfg.total_bytes, '.',
						  netcfg.total_bytes / (self.t2 - self.t1) / 1000, 'KB/s')

	def get_l2_info(self, l2):
		"""Get information from layer 2"""
		self.number_of_mac_frames = l2.get_number_of_frames()
		self.l2_pkt_size = l2.get_l2_pkt_size()
		# Modified for B210: Using serial addresses instead of IP addresses
		self.layer_2_next_hop_serial_usrp = l2.get_layer_2_next_hop_serial()
		self.layer_2_prev_hop_serial_usrp = l2.get_layer_2_prev_hop_serial()
		self.layer_2_serial_usrp = l2.get_layer_2_serial()

	def pass_up(self):
		"""
		Process received packets and pass them up to higher layers

		This method gets packets from the up_queue, processes them,
		and passes complete packets to the upper layer.
		"""

		up_packet = ''
		l4_packet = ''

		l4_packet = self.up_queue.get(True)
		# print("[RECEIVER L4 DEBUGGING] The received l4 packet: ", len(l4_packet), l4_packet)  # XY: Reached HERE!

		# Modified for B210: Using 16-byte fields for serial numbers
		# Header consists of: 8 bytes pktno + 16 bytes src serial + 16 bytes dst serial + 8 bytes timestamp = 48 bytes
		ack_l4 = l4_packet[0:42]

		try:
			(pktno_l4,) = struct.unpack('l', l4_packet[:8])
		except ValueError:
			print('!?! L2 pktno_mac ERROR - continue')

		# Extract source and destination serial  XY: Not sure why the message format is different as received in Layer 2
		packet_source = l4_packet[8:21].strip(b'\x00').decode()  # Source serial (16 bytes)
		packet_destination = l4_packet[21:34].strip(b'\x00').decode()  # Destination serial (16 bytes)
		(timestamp,) = struct.unpack('d', l4_packet[34:42])  # Timestamp after serials

		# print("[RECEIVER L4 DEBUGGING SOURCE] packet_source: ", packet_source)
		# print("[RECEIVER L4 DEBUGGING DESTINATION] packet_destination: ", packet_destination)
		# print("[RECEIVER L4 DEBUGGING TIME] timestamp: ", timestamp)

		if packet_destination == self.serial_usrp:
			# This packet is for us
			up_packet = l4_packet[42:]  # XY: Data starts after the header -> should be pure data?
			# print("[RECEIVER L4 DEBUGGING UP PACKET] up_packet: ", len(up_packet), up_packet, '\n')

			# Find the PC address to send acknowledgment to
			target_addr = netcfg.serial_to_addr.get(packet_source)
			port = netcfg.serial_to_port.get(packet_source)

			if target_addr and port:
				self.send_l4_feedback(ack_l4, pktno_l4, target_addr, port)

			return up_packet, 2  # XY: Can add more functions here, program ends HERE
		else:
			# This packet is not for us, pass it on
			return l4_packet, 0

	def pass_down(self, down_packet, index):  # has been called
		"""
		Send a packet to the lower layer and handle retransmissions

		This method sends a packet down to layer 2 and waits for acknowledgment,
		retransmitting if necessary up to a specified threshold.
		"""
		act_rt = 0  # XY: number of retransmission if no ACK received
		rt_threshold = 15

		(pktno_l4,) = struct.unpack('L', down_packet[:8])
		# print("[TRANSMITTER DEBUGGING LAYER 4] The LAYER 4 packet number is ", pktno_l4, down_packet)

		# Extract source serial (13 bytes, adjusted for B210)
		packet_source = down_packet[8:21].strip(b'\x00').decode()

		# If we sent the packet, update the timestamp -> XY: This part is confused
		if packet_source == self.serial_usrp:
			# Update timestamp in the packet
			# Format: 8 bytes pktno + 16 bytes src + 16 bytes dst + 8 bytes timestamp
			down_packet = down_packet[:34] + struct.pack('d', time.time()) + down_packet[42:]  # XY: not consist with structure
			down_packet = down_packet[42:]

		pktno_mac = 1
		l4_lower_queue_access.acquire()  # ACQUIRE the lower_queue (to not mix sequential mac packets)

		# print("[LAYER 4 packet pushed to LAYER 2] message: ", len(down_packet), down_packet)

		# Split packet into chunks for layer 2
		while pktno_mac <= self.number_of_mac_frames:
			# XY: Why we need to split the message? -> 128 Bytes under the default setting? chunk_size = 100
			chunk = down_packet[(pktno_mac - 1) * netcfg.chunk_size: min(pktno_mac * netcfg.chunk_size, len(down_packet))]

			# Create layer 2 packet with the proper header for B210
			# Format: 2 bytes pktno + 16 bytes src serial + 16 bytes dst serial + data
			src_serial = self.layer_2_serial_usrp.encode().ljust(13, b'\x00')
			dst_serial = self.layer_2_next_hop_serial_usrp.encode().ljust(13, b'\x00')

			l2_packet = struct.pack('h', pktno_mac & 0xffff).ljust(2, b'\x00') + src_serial + dst_serial + chunk
			# print("[DEBUGGING] The while loop", pktno_mac, chunk, len(chunk), len(down_packet), l2_packet, len(l2_packet), '\n')
			# XY: The 2 packets here, 01 / 02 -> The content has been adjusted according to the framework both for L2 and L4

			# print('--------------------------------------------Packet pushed to Layer 2-----------------------------------')
			self.lower_queue.put(l2_packet)
			pktno_mac += 1
			l2_packet = ''
		# print("[DEBUGGING] The while loop in layer 4 ended! ", pktno_mac, self.number_of_mac_frames)

		l4_lower_queue_access.release()  # RELEASE the lower_queue

		waiting_ack_pktno_l4 = pktno_l4  # the ack received must be for this pktno_mac

		# If we sent the packet, wait for a Layer 4 ACK
		if packet_source == self.serial_usrp:
			# Update dictionary pktno - thread id
			self.dict_thread_signal[self.thread_pool[index].ident] = threading.Event()  # DICT thread_id | Event

			l4_dict_pktno_thread_access.acquire()  # ACQUIRE the dict_pktno_thread

			# If there is no entry for this packet (in case of re-transmission it might be)
			if not waiting_ack_pktno_l4 in self.dict_pktno_thread:
				self.dict_pktno_thread[waiting_ack_pktno_l4] = self.thread_pool[index].ident  # DICT pkton | thread_id

			l4_dict_pktno_thread_access.release()  # RELEASE the dict_pktno_thread

			while 1:
				self.dict_thread_signal[self.thread_pool[index].ident].wait(netcfg.timeout_l4)
				if self.dict_thread_signal[self.thread_pool[index].ident].isSet():
					print("[LAYER 4 RECEIVED ACK DEBUGGING] The LAYER 4 ACK is received!!!!!!")
					self.dict_thread_signal[self.thread_pool[index].ident].clear()
					break
				elif act_rt < netcfg.l4_retransmission_threshold:
					# Retransmit the L4 packet
					pktno_mac = 1

					l4_lower_queue_access.acquire()  # ACQUIRE the lower_queue
					while pktno_mac <= self.number_of_mac_frames:
						chunk = down_packet[(pktno_mac - 1) * netcfg.chunk_size: min(pktno_mac * netcfg.chunk_size,
																					 len(down_packet))]

						# Create layer 2 packet with the proper header for B210
						src_serial = self.layer_2_serial_usrp.encode().ljust(13, b'\x00')
						dst_serial = self.layer_2_next_hop_serial_usrp.encode().ljust(13, b'\x00')

						l2_packet = struct.pack('h', pktno_mac & 0xffff) + src_serial + dst_serial + chunk
						self.lower_queue.put(l2_packet)

						pktno_mac += 1
						l2_packet = ''
					l4_lower_queue_access.release()  # RELEASE the lower_queue

					act_rt += 1
				else:
					print("L4 - retransmission limit reached " + str(pktno_l4))
					break

		return

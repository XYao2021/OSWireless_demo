"""
								Network layer
	this class defines the basic structure of a network layer
	it has 2 queues objects (up_queue,down_queue) and two threads (up_thread,down_thread)
	the threads execute two functions (up_fuction,down_function)
	up_fuction continuously run. receives up_packet from pass_up and decides based on the
	return of pass_up whether to put the packet in upper_queue(upper layer) or down_queue (current layer)
	down_function continuously run. gets the down_packet from down_queue and passes it to pass_down
"""

import random
import sys
import struct
import socket
from threading import Thread
import threading
from netlib import MyThread
import copy

import queue as Queue

class network_layer(object):
	
	def __init__(self, layer_name):
			self.layer_name = layer_name
			self.up_queue = Queue.Queue(1024*5000)
			self.down_queue = Queue.Queue(1024*5000)

	def init_upper_queue(self, upper_layer):
			self.upper_queue = upper_layer.get_up_queue()

	def init_lower_queue(self, lower_layer):
			self.lower_queue = lower_layer.get_down_queue()						
			
	def init_thread(self):	
			self.up_thread = Thread(target=self.up_fuction, args=())
			self.up_thread.start()

			self.down_thread = Thread(target=self.down_function_pool, args=())
			self.down_thread.start()

	def up_fuction(self):
		while True:
			#function that assemble the packet to be sent up/to down_queue. this function will pull packets from the queue
			up_packet, passing_decision = self.pass_up()  #previous_hop_socket check
			if passing_decision == 1:
				self.upper_queue.put(up_packet, True)
			elif passing_decision == 0:
				self.down_queue.put(up_packet, True)
			else:
				pass  # this is for mac layers not having an upper queue

	def down_function_pool(self):
		self.thread_pool = []
		self.dict_thread_signal = {}
		self.dict_pktno_thread = {}		
		for i in range(self.window):			
			self.thread_pool.append(MyThread(target=self.running_down_function, args=(i, )))  # call a thread running
			self.dict_thread_signal[self.thread_pool[i].ident] = threading.Event()  #put a signal			
			self.thread_pool[-1].start()

	def running_down_function(self, index):
		while True:
			if self.thread_pool[index].stop_condition is True:
				print('thread ', index, 'id ', self.thread_pool[index].ident, 'is exiting ')
				break
			self.down_function(index)

	def down_function(self, index):
		# functions that fragments the packet and put each of them down. the function is in charge of putting all the fragments in the queue
		down_packet = self.down_queue.get(True)
		# down_packet = self.upper_queue.get(True)
		self.pass_down(down_packet, index)

	def get_up_queue(self):
		return self.up_queue

	def get_down_queue(self):
		return self.down_queue

	#test whether self.pass_down calls one of these functions.
	def pass_down(self, down_packet, index):
		print('dummy pass_down')

	def pass_up(self):
		print('dummy pass_up')

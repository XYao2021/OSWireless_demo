"""Those common functions in other modules"""

from optparse import OptionParser
import time
import struct
import sys
from threading import Thread

import netcfg

class MyThread(Thread):
	def __init__(self, target, args):
		Thread.__init__(self, target=target, args=args)
		self.stop_condition = False

def get_ndinfo(node_name):

	"""identify node type and index with give node name"""

	# get node name
	node_index = netcfg.nd_id.index(node_name)
	# print '$$$ NODE INDEX IS' ,node_index
	# print ('$$$ NODE INDEX IS', node_index)
	
	# get the corresponding node type
	node_type = netcfg.nd_type[node_index] 
	
	ndinfo = {'index': node_index, 'type': node_type}
	return ndinfo
	
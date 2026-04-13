
#####################################################################
# channel coding module
# 
# The input payload may be in binary, may need to
# be converted to ASC-II first, and then converted 
# back to binary for transmission befor return
#
# RS code can be used: https://pypi.python.org/pypi/unireedsolomon
#####################################################################

import netcfg
import math
import struct
import time
from unireedsolomon.rs import *
from unireedsolomon.ff import *


def dtm_code_rate():
	"""
	func: determine channel coding rate. The channel coding rate should be determined
	to maintain the residual packet error rate at a predefined level, say 1/10. The channel coding
	rate will increased or decreased based on the observed packet error rate. Currently
	return 0.5 as default

	Define a set of possible channel coding rate in netcfg, ranging from 9/10 to 1/4
	"""
	# default channel coding rate

	return_rate = netcfg.ch_coding_rate[2]
	
	# get information somewhere else about observed packet error rate, (let's put it into l2 acks)
	# somewhere else there should be function to do the statistics
	
	# adjust channel coding rate
	return return_rate


def initialize_RSCoder(ch_coding_rate):
	"""
	initializes decoder
	"""
	k = netcfg.l2_size_block  #this must be fixed
	n = int(k * (1 + ch_coding_rate) - 1)  # variable, default half l2 packet
	# print '$$$ CODER N,K ',n,k
	print('$$$ CODER N,K ', n, k)

	generator = 3
	fcr = 1
	c_exp = math.ceil(math.log(netcfg.l1_size, 2))
	prim = find_prime_polynomials(generator, c_exp, fast_primes=False, single=True)

	t1 = time.time()
	coder = RSCoder(n, k, generator, prim, fcr, c_exp)

	return coder


def add_chncod(coder, payload, ch_coding_rate):
	"""
	func: add error protection to payload
	return: the payload with channel coding added
	parameters:
	payload_crc: payload to be protected
	chn_cod_rae: channel coding rate

	Notes: the payload is a string

	n = netcfg.l1_size #output bits of the encoder
	k = netcfg.l2_size #input bits of the encoder

	generator=3
	prim=0x11b
	fcr=1
	c_exp=math.ceil(math.log(netcfg.l1_size,2))

	#print 'L0 pre coding', struct.unpack('h', payload[0:2])

	coder = RSCoder(n, k, generator, prim, fcr, c_exp)
	"""

	c = b''
	c_block = b''
	d_block = b''

	# only for control messages (short)
	bloc_size = netcfg.l2_size_block
	if len(payload) < bloc_size:

		# c_block = coder.encode(payload, poly=False, k=None, return_string=True)
		c_block = coder.encode(payload, return_string=False)  # XY: This returns the list
		c_block = bytes(c_block)
		
		return c_block

	else:
		for i in range(0, netcfg.number_of_blocks):

			block_to_encode = payload[i*bloc_size:(i+1)*bloc_size]

			# c_block = coder.encode(block_to_encode, poly=False, k=None, return_string=True)
			c_block = coder.encode(payload, return_string=False)
			c_block = bytes(c_block)
			# print(i, c_block, type(c_block))

			c += c_block
			del c_block 

			del block_to_encode

	return c

def deduct_chncod(coder, payload, ch_coding_rate):
	"""
	func: add error protection to payload
	return: the payload with channel coding added
	parameters:
	payload_crc: payload to be protected
	chn_cod_rae: channel coding rate

	Notes: the payload is a string
	"""
	#print 'L0 pre decoding',' ', struct.unpack('h', payload[0:2])

	d = b''
	k = netcfg.l2_size_block  #this must be fixed
	bloc_size = int(k * (1 + ch_coding_rate) - 1)
	d_block = b''

	if len(payload) <= bloc_size:

		try:
			(d_block, d_block1) = coder.decode(payload)

			return d_block, 1  #success
		except RSCodecError:
	
			return d_block, 0  #failure

	else:
		num_blocks = (len(payload) + bloc_size - 1) // bloc_size

		for i in range(0, num_blocks):

			block_to_decode = payload[i*bloc_size:(i+1)*bloc_size]

			'''	
			try:
				(m,m1) = coder.decode(payload)
				#print 'success decode'
				#print 'L0 post decoding', ' ', struct.unpack('h', m[0:2])	
				return m,1 #success
			except RSCodecError:
				#print 'failure decode'
				return payload,0 #failure
			'''

			try:
				(d_block, d_block1) = coder.decode(block_to_decode)

			except RSCodecError:	
				return d, 0  #failure

			d += d_block
			del d_block
			del d_block1 

	return d, 1  #success

	
def check_phy(payload_chncod):
	"""
	func: check if length of the resulting packet exceeds phy-layer requirement
	return: 1 - OK, 0 - not OK
	"""
	
	# Currently, do nothing, return OK directly
	if len(payload_chncod) <= 4096:
		return 1
	else:
		return 0

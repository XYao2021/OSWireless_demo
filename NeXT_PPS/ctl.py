
# control module

# import netcfg, jocp, wnosalg, signalling
import wnosalg
import netcfg
import signalling

import threading
import time
from threading import Thread

# control thread
global ctl_thread, dict_tick

ctl_thread = None

# current transmit rate and power; check these parameters to see if there are any changes
cur_rate = 0
cur_tx_gain = netcfg.tx_gain

# update period of power and rate
period_tick = 1			# period of a tick in second
pwr_tick = 1			# period of power udpate in tick
rate_tick = 5			# period of rate update in tick
tick_cnt = 0			# current tick count, updated in ctl_main
dict_tick = {'period_tick': period_tick, 'pwr_tick': pwr_tick, 'rate_tick': rate_tick, 'tick_cnt': tick_cnt}

def start_ctl_thread():
	"""
	start control thread
    
    Called By: mynd.node()
	"""
	global ctl_thread
	
	ctl_thread = Thread(target=ctl_main, args=())
	ctl_thread.start()	
	# print 'Control thread started.'
	print("Control thread started.")
	
	
def ctl_main():
	"""
	main program of control thread
    
    Called By: start_ctl_thread() in this file
	"""
	
	tick = 0
	
	while True:
		########################################################
		# tick is used to control the update period of rate and power
		# if tick % cnt_updt_pwr == 0, power is updated
		# if tick % cnt_updt_rate == 0, rate is updated
		########################################################
		tick += 1
		dict_tick['tick_cnt'] = tick
		
		# Determine which transmission parameter should be optimized, according
		# to tick count and the optimization switch defined in netcfg
		b_optrate = 0					# Initialize to not being optimized (0)
		b_optpwr = 0
		
		# Whether to optimize power?
		if dict_tick['tick_cnt'] % (period_tick * pwr_tick) == 0 and netcfg.b_optpwr == 1:
			b_optpwr = 1
			
		# Whether to optimize transport layer rate?
		if dict_tick['tick_cnt'] % (period_tick * rate_tick) == 0 and netcfg.b_optrate == 1:
			b_optrate = 1	

		dict_opt_switch = {'b_optpwr': b_optpwr, 'b_optrate': b_optrate}
		
		########################################################
		# network control algorithm here
		# JOCP: Jointly Optimized Congestion and Power Control (Control the transport layer (TCP rates) and physical layer (transmit power) at the same time)
		# WNOS: Wireless Network Operating System (Automatically generate the distributed control algorithm according to the written high-level network objectives)
		# Both algorithm are not implemented yet, will replace this part with new optimization algorithm
		########################################################
		if netcfg.alg == 'JOCP':                        # As configured in netcfg, JOCP is not implemented
			# dict_para = jocp.jocp()
			print("Error: Currently JOCP is not supported!\n")
			exit(0)
		else:
			print("Support WNOS network control algorithm")
			dict_para = wnosalg.wnosalg(dict_opt_switch)  # wnosalg is located in the same directory
			# print("Error: Currently WNOS is not supported!\n")
			exit(0)
		
		########################################################
		# update transmit parameters
		########################################################
		new_tx_gain = dict_para['tx_gain']  # XY: Control the tx_gain to control transmit power
		new_rate = dict_para['rate']		
		updt_para(new_tx_gain, new_rate)
		
		########################################################
		# broad new parameters to neighbors
		########################################################
		idx_thisnode = netcfg.idx_thisnode											# index of transmitter
		rcvr_ip_list = None															# ip list of receivers
		
		para_code = None															# type of parameter to be sent
		para_val = None																# value of parameter to be sent
		#signalling.broadcast_sgl(idx_thisnode, rcvr_ip_list, para_code, para_val)	# broad the parameter
		
		########################################################
		# if tick reaches its maximum, reset it and count from 0
		########################################################
		if tick >= 100000:
			tick = 0
		
		# wait for a tick period
		time.sleep(period_tick)
		#print '*'


def updt_para(new_tx_gain, new_rate):
	"""
	func: update transmit parameters
	
	new_tx_gain: new transmit gain
	new_rate: new layer-4 transmit rate 
    
    Called By: ctl_main() in this file
	"""
	pass

def get_rcvr_ip_list(idx_thisnode):
	"""
	determine the ip of list for control message broadcasting
	"""
	pass

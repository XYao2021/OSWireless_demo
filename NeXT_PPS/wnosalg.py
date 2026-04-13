
# Our Own Algorithm to determine the transmit rate of each source and transmit power of each transmitter
# Using the automatically generated solution algorithms

def wnosalg(dict_opt_switch):
	"""
	Joint rate and power control algorithm designed based on NLPD framework
	
	dict_opt_switch: optimization switch dictionary, 1-the corresponding parameter is optimized, 0-not optimized
	
	Called By: ctl.ctl_main()
	"""
	dict_para = {'tx_gain': None, 'rate': None}
	
	# my code here
	if dict_opt_switch['b_optpwr'] == 1:			# Optimize transmission power
		dict_para['tx_gain'] = opt_pwr()									
		
	if dict_opt_switch['b_optrate'] == 1:			# Optimize transmission rate
		dict_para['rate'] = opt_rate()
	
	return dict_para
	
def opt_pwr():
	"""
	Optimize transmission power based on automatically generated solution algorithm (see WNOS project for details)
	
	Called By: wnosalg() in the same file
	"""
	return None

def opt_rate():
	"""
	Optimize transmission rate based on automatically generated solution algorithm (see WNOS project for details)
	
	Called By: wnosalg() in the same file
	"""
	return None

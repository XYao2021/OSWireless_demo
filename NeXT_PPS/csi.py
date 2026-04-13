######################################################################
# Module function: get channel state information
# Modified for B210 USRP devices (using serial numbers instead of IP)
######################################################################

# Reference correlation magnitude measured at transmitter side:
# '+1, -1' preamble modulated using bpsk with samples per symbol of 4 and excess BW 0.35
# then correlated with '+1 -1' preamble using matched filter
# no transt gain and digital gain has been considered

import math
import netcfg

######################################################################
# Parameters for channel gain measurement, used in
# my_csi_est_tx.py, my_csi_est_rx.py, my_tx_withcorr.py
######################################################################

# Sample rate
sps = 4
samp_rate = 250000

# PN code -> XY: preamble sequence used
pn0 = [1, -1, 1, -1, 1, 1, -1, -1, 1, 1, -1, 1, 1, 1, -1, 1, 1, -1, 1, -1, -1, 1, -1, -1, 1, 1, 1, -1, -1, -1, 1, -1, 1,
	   1, 1, 1, -1, -1, 1, -1, 1, -1, -1, -1, 1, 1, -1, -1, -1, -1, 1, -1, -1, -1, -1, -1, 1, 1, 1, 1, 1, 1, -1, -1]
pn1 = [-1, 1, 1, 1, 1, -1, -1, 1, 1, -1, -1, 1, -1, -1, 1, 1, 1, 1, 1, -1, -1, 1, 1, 1, 1, 1, 1, 1, 1, -1, -1, 1, -1,
	   -1, 1, -1, -1, 1, -1, 1, -1, -1, -1, 1, -1, 1, -1, -1, -1, -1, 1, 1, 1, 1, -1, 1, -1, 1, -1, 1, 1, -1, 1, 1]
pn2 = [-1, -1, 1, 1, 1, -1, -1, -1, -1, 1, -1, 1, 1, 1, 1, -1, -1, -1, -1, -1, -1, -1, -1, 1, 1, -1, 1, 1, 1, 1, -1, 1,
	   -1, 1, 1, -1, -1, -1, -1, -1, 1, -1, 1, -1, 1, -1, 1, -1, -1, -1, 1, 1, 1, 1, 1, -1, -1, 1, 1, 1, -1, 1, -1, 1]
pn3 = [-1, -1, 1, -1, 1, 1, -1, -1, 1, -1, 1, -1, -1, 1, -1, -1, 1, -1, 1, -1, 1, 1, 1, 1, 1, -1, 1, 1, -1, -1, -1, 1,
	   -1, -1, 1, 1, -1, 1, 1, -1, 1, 1, -1, -1, 1, 1, 1, 1, 1, 1, -1, -1, -1, 1, -1, 1, 1, -1, 1, 1, 1, -1, -1, -1]
pn_used = pn0

# Gain
tx_gain = 13.0
rx_gain = 18.0

# dB -> absolute
tx_gain_abs = 10 ** (tx_gain / 10)
rx_gain_abs = 10 ** (rx_gain / 10)

# This parameter must be 1 for channel estimation
# because the received correlation magnitude does not change with this parameter
digi_gain_tx = 1.0

# This parameter can be larger than 1
digi_gain_rx = 20.0

# B210 USRP serial numbers (using the values from netcfg.py) -> Not used in other files
tx_usrp_serial = "serial=" + netcfg.serial_usrp_src1
rx_usrp_serial = "serial=" + netcfg.serial_usrp_dst1

# Frequency
freq = 2e9

# Number of channel measurements
num_msmt = 100

# Reference squared correlation magnitude -> XY: for time synchronization
ref_corr_mag_sqrd = 64650.0


def calc_chn_gain(corr_mag_sqrd):
	"""
    ############### function ##################
    calculate channel gain

    ################ parameters ###############
    measured squared correlation magnitude

    ################ return ###################
    channel gain
    """

	path_gain = corr_mag_sqrd / ref_corr_mag_sqrd  # end-to-end path gain
	print('tx_gain_abs:', tx_gain_abs)
	chn_gain = path_gain / tx_gain_abs / rx_gain_abs / (digi_gain_rx ** 2) / (digi_gain_tx ** 2)

	return chn_gain


def updt_sir():
	"""
    ############### function ##################
    update SIR online

    ################ parameters ###############
    read parameters from netcfg

    ################ return ###################
    update sir parameter in netcfg
    """

	###################################################
	# Read received total signal power
	###################################################

	# check if the receiver block has been created, return directly if not
	# otherwise, read the received signal power from the block
	if netcfg.obj_rcvr_blk is None:
		# print('None receiver block!')
		return
	else:
		# print('Receiver block detected.')
		sgl_pwr_complex = netcfg.obj_rcvr_blk.get_sgl_pwr()
		sgl_pwr = sgl_pwr_complex.imag

	###################################################
	# Calculate SIR
	###################################################

	# calculate the received useful signal power
	idx = netcfg.idx_thisnode
	chn_gain = netcfg.chn_gain[idx, netcfg.chn_idx_thisnode[idx]]
	# print(chn_gain)
	useful_sgl_pwr = (netcfg.tx_ampl ** 2) * (netcfg.tx_gain_abs) * \
					 chn_gain * (netcfg.rx_gain_abs)

	# calculate interference power
	itf_pwr = max(netcfg.SMALL_VALUE, sgl_pwr - useful_sgl_pwr)

	# calculate SIR -> XY: Signal to Interference Ratio
	sir = useful_sgl_pwr / itf_pwr

	###################################################
	# Update SIR of this node in netcfg
	###################################################
	if netcfg.sir_thisnode is None:
		netcfg.sir_thisnode = sir
	else:
		netcfg.sir_thisnode = netcfg.sir_thisnode * netcfg.alpha + sir * (1 - netcfg.alpha)

	# print('---------------------------------------------------')
	# print('Estimated SIR:', sir)
	print(sir, ' ', sgl_pwr, ' ', useful_sgl_pwr)

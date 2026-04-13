# Add search paths
import sys, os, inspect

sys.path.append("./wos-dir/")
sys.path.append("./wos-ncp/")
sys.path.append("./wos-network/")
sys.path.append("../")
sys.path.append("../NeXT-PPS")
sys.path.append("../../")

sys.path.insert(0, './wos-network')
sys.path.insert(0, './wos-ncp')
sys.path.insert(0, './wos-dir')
sys.path.insert(0, '../NeXT-PPS')

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))

sys.path.insert(0, parent_dir + '\OSW_G2_elmtlib\element_library')

import numpy as np

def data_format(data_array, input_data, reward):
	#print('input data', input_data)
	#print('reward', reward)
	init_array = np.array([1])
	input_array = np.array(input_data)
	reward_array = np.array(reward)
	data = np.hstack((init_array, input_array))
	data = np.hstack((data, reward_array))
	#print('data to be stored', data)
	#print('Array_Size', np.size(data_array))
	if np.size(data_array) == 0:
		data_array = data
	else:
		data_array = np.vstack((data_array, data))
	return data_array

N = 10
num_ip = 4

data_array = np.array([])
for n in range(N):
    input_data = []
    for n_ip in range(num_ip):
        input_data.append(n+n_ip)
    reward = np.sum(input_data)
    data = data_format(data_array, input_data, reward)
    #print(data)
    data_array = data
print(data_array)

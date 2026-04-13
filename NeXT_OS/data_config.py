def data_config(nt):
	'''
	Configure the data plane
	nt - network object passed from the main program
	'''
	print('Configuring driver plane')
	nt.configure('node_0', 
	{'dataset':'data_node_0.npy',
	'usrp':'usrp_0'})
	nt.configure('node_1', 
	{'dataset':'data_node_1.npy',
	'usrp':'usrp_1'})
	nt.configure('node_2', 
	{'dataset':'data_node_2.npy',
	'usrp':'usrp_2'})
	nt.configure('node_3', 
	{'dataset':None,
	'usrp':'usrp_3'})
	nt.configure('node_4', 
	{'dataset':'data_node_4.npy',
	'usrp':'usrp_4'})
	nt.configure('node_5', 
	{'dataset':'data_node_5.npy',
	'usrp':'usrp_5'})
	nt.configure('node_6', 
	{'dataset':'data_node_6.npy',
	'usrp':'usrp_6'})
	nt.configure('node_7', 
	{'dataset':None,
	'usrp':'usrp_7'})


# import imp
import importlib.util

import sys
import os

sys.path.append("/home/edgeai/Dropbox/Research/OS Wireless/OSWireless_demo")
from addpath import *

import netcfg
# import netcfg, net_name
import pps_dir
import pickle
import copy

def load(node, node_rolee):
    netcfg.values_net_para = {}
    
    #List of algorithms to be loaded
    list_files_to_be_loaded = ['__net_para_', 'pnl__phy_', 'lag_in_']
    
    # Get the name of the algorithm directory
    # Prepare the name of the directory storing the path of the algorithm repo
    alg_dir = pps_dir.driver_dir+'alg_dir_name.py'
    
    # # open the algorithm directory read mode and get the path of the alg repo
    # file = open(alg_dir,'r')      # open in read mode
    #
    # # The stored alg path has 'alg_path' - Remove the quotation marks
    # alg_dir = file.read()[1:-1]
    # #print alg_dir[1:-1]

    with open(alg_dir, 'r') as file:
        alg_dir = file.read().replace("dir_name = '../NeXT_OS/NCP_g2_rate_power/'",
                                      "../NeXT_OS/NCP_g2_rate_power/").strip()

    # Store the path in network config file for later use
    netcfg.alg_dir = alg_dir
    
    # Load all the files as specified in the list above
    # First, get the path of the specific algorithm
    # Then, load the algorithm file
    # finally, store the object of the loaded file to a dictionary for later use in sugnalling.py ( we do this so that the values can be updated during runtime

    for file_name in list_files_to_be_loaded:
        # prepare the name of the file to be loaded
        file_to_be_loaded = alg_dir+file_name+node+'.py'
        file_to_be_loaded = alg_dir + file_name + node + '.py'

        # Load the source file using imp.load_source
        # loaded_source = imp.load_source(node, file_to_be_loaded)
        spec_lag = importlib.util.spec_from_file_location(node, file_to_be_loaded)
        loaded_source = importlib.util.module_from_spec(spec_lag)
        spec_lag.loader.exec_module(loaded_source)
        
        # STore the loaded source in netcfg.values_net_para dictionary for later use in signalling.py
        netcfg.values_net_para.update({file_name: loaded_source})
    
    # This part is to get the name of the dependent session for the specific link
    # This again will be used in signalling.py
    # The logic of obtaining the object of the loaded algo is same as above
    
    # Get the path of the node_link_session.py which stores the name of the link and session for this node
    node_link_file = 'node_link_session'
    map_path = pps_dir.driver_dir+node_link_file+'.py'

    # loaded_file = imp.load_source(pps_dir.driver_dir, map_path)
    spec_lag = importlib.util.spec_from_file_location(pps_dir.driver_dir, map_path)
    loaded_file = importlib.util.module_from_spec(spec_lag)
    spec_lag.loader.exec_module(loaded_file)

    details = getattr(loaded_file, node)

    session_name = details['session'][0]
    netcfg.tsptsesname = session_name
    # print(net_name.sess_rate_list[netcfg.tsptsesname])

    link_name = details['link']

    # Store the link name and session name for later use in signalling.py
    netcfg.lnk_name = link_name
    netcfg.ses_name = 'ssrate_'+session_name

def lag_update(node):
    # Lag update function is used to load the source of various lag update files

    # Get the file that stores the name of the lagrangian variables used in the algorithm
    node_expr_map_file = netcfg.alg_dir+'lag_out_'+node+'.py'

    # Load the source and get the list stored in 'value' attribute of the file obtained above
    # loaded_source3 = imp.load_source(node, node_expr_map_file)
    spec_lag = importlib.util.spec_from_file_location(node, node_expr_map_file)
    loaded_source3 = importlib.util.module_from_spec(spec_lag)
    spec_lag.loader.exec_module(loaded_source3)

    lag_list = getattr(loaded_source3, 'value')

    # The partial portion of the file name is defined below 
    file_name = 'lag_update_'

    i = 0
    netcfg.values_net_para_lag = {}
    netcfg.lag_2_dict = False
    netcfg.lag_2_dict2 = False
    
    # An empty dict to store the name of the lag element.
    netcfg.expr_lag = {}
    ptr = ['node', 'node']
    # Loop over the lagrangians and store the source - follows the same logic as above.
    if len(lag_list) != 1:
        for lag_elmt in lag_list:

            file_name2 = lag_elmt
            file_name_lag = file_name+file_name2

            netcfg.expr_lag[file_name2] = lag_elmt
            file_to_be_loaded = netcfg.alg_dir+file_name_lag+'.py'

            ptr_string = 'node'+str(i+1)

            # loaded_source2 = imp.load_source(ptr_string, file_to_be_loaded)
            spec_lag = importlib.util.spec_from_file_location(ptr_string, file_to_be_loaded)
            loaded_source2 = importlib.util.module_from_spec(spec_lag)
            spec_lag.loader.exec_module(loaded_source2)

            netcfg.values_net_para_lag.update({file_name_lag: loaded_source2})
            
            if i == 1:
                netcfg.lag_2_dict = True
                file_to_be_loaded = netcfg.alg_dir+'__net_para_'+node+'.py'

                # loaded_source3 = imp.load_source(ptr_string, file_to_be_loaded)
                spec_lag = importlib.util.spec_from_file_location(ptr_string, file_to_be_loaded)
                loaded_source3 = importlib.util.module_from_spec(spec_lag)
                spec_lag.loader.exec_module(loaded_source3)

                netcfg.values_net_para_lag.update({'__net_para_': loaded_source3})
                
            if i == 2:
                netcfg.lag_2_dict2 = True
                file_to_be_loaded = netcfg.alg_dir+'__net_para_'+node+'.py'
                loaded_source4 = imp.load_source(ptr_string, file_to_be_loaded)
                netcfg.values_net_para_lag.update({'__net_para_2': loaded_source4})

            i += 1
        
    if len(lag_list) == 1:
        file_name2 = lag_list[0]
        file_name_lag = file_name+file_name2
        netcfg.expr_lag[file_name2] = file_name2
        file_to_be_loaded = netcfg.alg_dir+file_name_lag+'.py'

        # loaded_source4 = imp.load_source(node, file_to_be_loaded)
        spec_lag = importlib.util.spec_from_file_location(node, file_to_be_loaded)
        loaded_source4 = importlib.util.module_from_spec(spec_lag)
        spec_lag.loader.exec_module(loaded_source4)

        netcfg.values_net_para_lag.update({file_name_lag: loaded_source4})
        netcfg.lag_2_dict = True
        file_to_be_loaded = netcfg.alg_dir+'__net_para_'+node+'.py'

        # loaded_source3 = imp.load_source(node, file_to_be_loaded)
        spec_lag = importlib.util.spec_from_file_location(node, file_to_be_loaded)
        loaded_source3 = importlib.util.module_from_spec(spec_lag)
        spec_lag.loader.exec_module(loaded_source3)

        netcfg.values_net_para_lag.update({'__net_para_': loaded_source3})

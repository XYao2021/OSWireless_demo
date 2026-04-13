
import os
import sys
import importlib.util
import netcfg
import pps_dir
import pickle


def tspt_alg_load(node3):
    """
    Load transport layer algorithms for the specified node.

    This function loads the transport layer algorithm modules required for the specified node,
    updating the netcfg.values_net_para_tspt dictionary with the loaded modules.

    Args:
        node3: Node identifier string
    """
    # Only the tx node needs to load the tspt layer algorithm
    file_name = '__tspt_'
    netcfg.values_net_para_tspt = {}

    # Load transport algorithm module
    filet = os.path.join(netcfg.alg_dir, file_name + node3 + '.py')
    spec = importlib.util.spec_from_file_location(file_name + node3, filet)
    loaded_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded_module)
    netcfg.values_net_para_tspt.update({file_name: loaded_module})

    netcfg.tspt_flag = True

    # Load network parameters module
    file_to_be_loaded = os.path.join(netcfg.alg_dir, '__net_para_' + node3 + '.py')
    spec = importlib.util.spec_from_file_location('__net_para_' + node3, file_to_be_loaded)
    loaded_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded_module)
    netcfg.values_net_para_tspt.update({'__net_para_': loaded_module})

    # Load Lagrangian input module
    file_to_be_loaded = os.path.join(netcfg.alg_dir, 'lag_in_' + node3 + '.py')
    spec = importlib.util.spec_from_file_location('lag_in_' + node3, file_to_be_loaded)
    loaded_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded_module)
    netcfg.values_net_para_tspt.update({'lag_in_': loaded_module})

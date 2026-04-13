
import os
import sys
import importlib.util
import netcfg
import pps_dir
import pickle


def phy_alg_load(node):
    """
    Load physical layer algorithms for the specified node.

    This function loads the physical layer algorithm module required for the
    specified node, updating the netcfg.values_net_para dictionary with the loaded module.

    Args:
        node: Node identifier string
    """
    # Only the tx node needs to load the physical layer algorithm
    netcfg.values_net_para_phy = {}
    file_name = '__phy_'
    filep = os.path.join(netcfg.alg_dir, file_name + node + '.py')

    # Use importlib instead of imp (which is deprecated in Python 3)
    spec = importlib.util.spec_from_file_location(file_name + node, filep)
    loaded_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded_module)

    # Update the netcfg.values_net_para dictionary with the loaded module
    netcfg.values_net_para.update({file_name: loaded_module})

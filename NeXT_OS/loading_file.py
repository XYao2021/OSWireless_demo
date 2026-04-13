import imp
import sys,os

path = os.getcwd()
sys.path.insert(0, '../NeXT-PPS')

import netcfg
import pps_dir
import pickle

def load(node_list):
    netcfg.values_net_para = {}
    for node in node_list:
        file_to_be_loaded = pps_dir.alg_dir+'__net_para_'+node+'.py'
        loaded_source  = imp.load_source(node, file_to_be_loaded)
        netcfg.values_net_para.update({node:loaded_source})

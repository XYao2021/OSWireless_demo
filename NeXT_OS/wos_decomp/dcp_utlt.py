#######################################################
# Date: 03/15/2016
# Author: Zhangyu Guan
# Project Manager: Tommaso Melodia, Zhangyu Guan
# parse utility
#######################################################

import sys
sys.path.insert(0, './wos-network')

# from wos-network
import net_name, net_func

# from local folder
import dcp_name, dcp_cstr, dcp_var, dcp_inst, dcp_gn

def ps_utlt(xpd):
    '''
    parse the utility function for a NUM to generate its expanded version
    '''  
    # parse utility function
    #print('Parsing utility function...')
    
    # generate an instance of the expression
    obj_utlt = gen_xpdutlt(xpd)
    
    # add the instance to xpd
    # xpd.add_utlt(obj_utlt)        # no need to add utlity explicitly, its name has been recorded in xpd.lst_inst


def gen_xpdutlt(xpd):
    '''
    generate expanded utility
    return the string name of the utility
    '''    
    # create the generator
    obj_utlt = xpd.get_netelmt(net_name.utility)
    gn = dcp_gn.create_gn(obj_utlt)
    
    # generate instance for utility
    obj_utlt = gn.get_newlst()
    
    # # create the utility object with lst_inst as the variable vector  
    # #---------------------------------------------------------------      
    # elmt_name = xpd.get_newinstname()                                   # element info
    # elmt_num = 1     
    
    # netutlt = xpd.get_netelmt(net_name.utility)                         # parent elemnt of xpdutlt, i.e., the network utility object
    
    # # instlst: the list of specific variable names
    # addi_info = {'ntwk':xpd.ntwk, 'parent':netutlt, 'instlst': lst_inst}  
    # info = net_func.mkinfo(elmt_name, None, elmt_num, addi_info)        

    # elmt = dcp_inst.inst(info)                                          # create element
    # netutlt.addgroup(elmt_name, elmt)                                   # add element as a subgroup 
    
    # print(netutlt.__dict__.keys())
            
    # x = elmt
    # x.ping()
    # #---------------------------------------------------------------    
  
    # return the utility name
    return obj_utlt
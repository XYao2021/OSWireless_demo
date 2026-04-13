#######################################################
# Date: 03/15/2016
# Author: Zhangyu Guan
# Project Manager: Tommaso Melodia, Zhangyu Guan
# Parse constraints
#######################################################

import sys
sys.path.insert(0, './wos-network')

# from wos-network
import net_name, net_func

# from local folder
import dcp_name, dcp_set, dcp_inst, dcp_gn

def ps_allcstrs(xpd):
    '''
    parse all constraints to generate xpd
    xpd: object of the NUM problem
    '''
    
    # retrieve the network
    ntwk = xpd.get_ntwk()
    
    # process all constraints
    cstr_id = 1
    while True:        
        # retrieve constraint object, terminate if None returned
        obj_cstr = ntwk.getcstr(cstr_id)
        if obj_cstr == None:
            break;
        else:
            cstr_id += 1
            
        # process the retrieved constraint object
        ps_cstr(xpd, obj_cstr)
        
def ps_cstr(xpd, obj_cstr):
    '''
    parse a constraint
    '''      
    
    # create the generator
    gn = dcp_gn.create_gn(obj_cstr)
    
    # generate a constraint instance every time, until None instance
    while True:
        # generate new instances until None returned
        obj_inst = gn.get_newlst()
        if obj_inst == None:                             
            break
            
        # 
    
        # # record the generated instance
        # #---------------------------------------------------------------      
        # elmt_name = xpd.get_newinstname()                                   # element info
        # elmt_num = 1     
        
        # # instlst: the list of specific variable names
        # addi_info = {'ntwk':xpd.ntwk, 'parent':obj_cstr, 'every': None, 'nonevery': None}  
        # info = net_func.mkinfo(elmt_name, None, elmt_num, addi_info)        

        # elmt = dcp_inst.inst(info)                                          # create element
        # obj_cstr.addgroup(elmt_name, elmt)                                  # add element as a subgroup 
        
        # print(obj_cstr.__dict__.keys())
                
        # x = elmt
        # x.ping()
        # #---------------------------------------------------------------         
        
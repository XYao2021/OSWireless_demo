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

import net_name_g2

def inst_mdl(nt):
    lkcap_attribute_list = nt.get_list(net_name_g2.lkcap)
    lksinr_attribute_list = nt.get_list(net_name_g2.lksinr)
    lkinrate_attribute_list = nt.get_list(net_name_g2.lkinrate)
    lkdelay_attribute_list = nt.get_list(net_name_g2.lkdelay)
    ssdelay_attribute_list = nt.get_list(net_name_g2.ssdelay)

    '''
    Installing Models for attributes connected to microwave bands
    '''
    print('Installing Models for Microwave Band Attributes')
    for lk in nt.get_list(net_name_g2.microwave_link):
        lkobj = nt.get_netelmt_g2(lk)
        nt.attach_model(lkobj.___lkcap___.stype, '__lkcap__script__micro__')
        nt.attach_model(lkobj.___lksinr___.stype, '__lksinr__script__micro__')
        
    print('Installing Models for SixGhz Band Attributes')
    for lk in nt.get_list(net_name_g2.sixghz_link):
        lkobj = nt.get_netelmt_g2(lk)
        nt.attach_model(lkobj.___lkcap___.stype, '__lkcap__script__sixghz__')
        nt.attach_model(lkobj.___lksinr___.stype, '__lksinr__script__sixghz__')
        
    print('Installing Models for Millimeter wave Band Attributes')
    for lk in nt.get_list(net_name_g2.mmwave_link):
        lkobj = nt.get_netelmt_g2(lk)
        nt.attach_model(lkobj.___lkcap___.stype, '__lkcap__script__mmwave__')
        nt.attach_model(lkobj.___lksinr___.stype, '__lksinr__script__mmwave__')
        
    print('Installing Models for Terahertz Band Attributes')
    for lk in nt.get_list(net_name_g2.thz_link):
        lkobj = nt.get_netelmt_g2(lk)
        nt.attach_model(lkobj.___lkcap___.stype, '__lkcap__script__thz__')
        nt.attach_model(lkobj.___lksinr___.stype, '__lksinr__script__thz__')
        
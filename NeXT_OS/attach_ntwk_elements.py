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

def attach_ntwk_elmt(nt):
    # Adding node network element
    nt.attach(net_name_g2.node, 4, addi_info={'num_ant':2}) 

    # Adding antenna network element
    nt.attach(net_name_g2.antenna, 10)

    # Adding mimo node element
    nt.attach(net_name_g2.mimo_node, 4, addi_info={'num_ant':2})
    
    # Adding directional_antenna element
    nt.attach(net_name_g2.directional_antenna, 1)
    
    # Adding uwave node element
    nt.attach(net_name_g2.microwave_node, 4, addi_info={'num_ant':2})
    
    # Adding uwave mimo node element
    nt.attach(net_name_g2.microwave_mimo_node, 4, addi_info={'num_ant':2})
    
    # Adding 6ghz node element
    nt.attach(net_name_g2.sixghz_node, 4, addi_info={'num_ant':2, 'oper_freq':'six'})

    # Adding 6ghz mimo node element
    nt.attach(net_name_g2.sixghz_mimo_node, 4, addi_info={'num_ant':2})

    # Adding mmwave node element
    nt.attach(net_name_g2.mmwave_node, 4, addi_info={'num_ant':2})

    # Adding mmwave mimo node element
    nt.attach(net_name_g2.mmwave_mimo_node, 4, addi_info={'num_ant':2})

    # Adding thz node element
    nt.attach(net_name_g2.thz_node, 4, addi_info={'num_ant':2})

    # Adding thz mimo node element
    nt.attach(net_name_g2.thz_mimo_node, 4, addi_info={'num_ant':2})

    # Adding link network element
    nt.attach(net_name_g2.link, 4)

    # Adding microwave link network element
    nt.attach(net_name_g2.microwave_link, 3)

    # Adding six ghz link network element
    nt.attach(net_name_g2.sixghz_link, 2)

    # Adding mmwave link network element
    nt.attach(net_name_g2.mmwave_link, 3)

    # Adding thz link network element
    nt.attach(net_name_g2.thz_link, 3)
 
    # Adding session network element
    nt.attach(net_name_g2.session, 4)
    

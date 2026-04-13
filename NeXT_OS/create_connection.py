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
def crt_cnct(nt):
    node_list = nt.get_list(net_name_g2.node)
    mimo_node_list = nt.get_list(net_name_g2.mimo_node)
    microwave_node_list = nt.get_list(net_name_g2.microwave_node)
    microwave_mimo_node_list = nt.get_list(net_name_g2.microwave_mimo_node)
    sixghz_node_list = nt.get_list(net_name_g2.sixghz_node)
    sixghz_mimo_node_list = nt.get_list(net_name_g2.sixghz_mimo_node)
    mmwave_node_list = nt.get_list(net_name_g2.mmwave_node)
    mmwave_mimo_node_list = nt.get_list(net_name_g2.mmwave_mimo_node)
    thz_node_list = nt.get_list(net_name_g2.thz_node)
    thz_mimo_node_list = nt.get_list(net_name_g2.thz_mimo_node)

    link_list = nt.get_list(net_name_g2.link)
    microwave_link_list = nt.get_list(net_name_g2.microwave_link)
    sixghz_link_list = nt.get_list(net_name_g2.sixghz_link)
    mmwave_link_list = nt.get_list(net_name_g2.mmwave_link)
    thz_link_list = nt.get_list(net_name_g2.thz_link)
    session_list = nt.get_list(net_name_g2.session)
    #exit()
    
    '''
    # Connecting nodes and links 
    '''

    # Creating microwave links between microwave nodes
    print('Creating microwave links between microwave nodes')
    nt.connect('microwave_link_0', ['microwave_node_0', 'microwave_node_1'])
    nt.connect('microwave_link_1', ['microwave_node_1', 'microwave_node_2'])
    nt.connect('microwave_link_2', ['microwave_node_2', 'microwave_node_3'])

    # Creating sixghz links between sixghz nodes
    print('Creating sixghz links between sixghz nodes')
    nt.connect('sixghz_link_0', ['sixghz_node_0', 'sixghz_node_1'])
    nt.connect('sixghz_link_1', ['sixghz_node_2', 'sixghz_node_3'])

    # Creating mmwave links between mmwave nodes
    print('Creating mmwave links between mmwave nodes')
    nt.connect('mmwave_link_0', ['mmwave_node_0', 'mmwave_node_1'])
    nt.connect('mmwave_link_1', ['mmwave_node_1', 'mmwave_node_2'])
    nt.connect('mmwave_link_2', ['mmwave_node_2', 'mmwave_node_3'])

    # Creating thz links between thz nodes
    print('Creating thz links between thz nodes')
    nt.connect('thz_link_0', ['thz_node_0', 'thz_node_1'])
    nt.connect('thz_link_1', ['thz_node_1', 'thz_node_2'])
    nt.connect('thz_link_2', ['thz_node_2', 'thz_node_3'])
    print('--------------------------------------------------------------------------------------------------')
    '''
    Connecting links and sessions
    '''
    #print(session_list, '.....', session_list)
    
    # Creating microwave session with microwave links
    print('Creating microwave session with microwave links')
    nt.connect('session_0', ['microwave_link_0', 'microwave_link_1', 'microwave_link_2'])

    # Creating sixghz session with sixghz links
    print('Creating sixghz session with sixghz links')
    nt.connect('session_1', ['sixghz_link_0', 'sixghz_link_1'])

    # Creating mmwave session with mmwave links
    print('Creating mmwave session with mmwave links')
    nt.connect('session_2', ['mmwave_link_0', 'mmwave_link_1', 'mmwave_link_2'])

    # Creating thz session with thz links
    print('Creating thz session with thz links')
    nt.connect('session_3', ['thz_link_0', 'thz_link_1', 'thz_link_2'])
    print('--------------------------------------------------------------------------------------------------')
    

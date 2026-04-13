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

def expr_cnst(nt):
    expr = {'expr_xpd': '', 'expr_ori': ''}

    for link in nt.get_list('microwave_link'):                                                   # Loop over the links in link list
        #print(link)
        lkobj = nt.get_netelmt_g2(link)                                      # Get the link object
        lkcap_expr = nt.get_expr_g2(link, net_name_g2.lkcap)                 # Get the expression for link capacity
        print(link, lkcap_expr)
#######################################################
# Date: 03/15/2016
# Author: Zhangyu Guan
# Project Manager: Tommaso Melodia, Zhangyu Guan
# parse variable
#######################################################

import sys
sys.path.insert(0, './wos-network')

# from wos-network
import net_name, net_func

# from local folder
import dcp_name, dcp_cstr


def ps_var(xpd, var_name):
    '''
    parse a variable
    '''    
    #print('Parsing variable {}...'.format(var_name))
    
    # variable object 
    varobj = xpd.get_netelmt(var_name)                                      
    para_name = varobj.getpara()                    # parameter name for which the variable is defined
    mbrobj = varobj.newfamset()                     # add member list for a variable    
    
    # Changes: will return the list when creating the list above
    # mbr_lst = varobj.getfamset()                  # get the member list for which the variale is defined
    
    # record the expanded varible    
    varinfo = {'var': var_name, 'para':para_name, 'lst':mbrobj.lst}
    dcp_xpd.add_xpdvar(xpd, varinfo)
    
    
    # # retrieve the utlity expression
    # ntwk = xpd.get_ntwk()                                          # network object   
    # utlt = ntwk.get_netelmt(net_name.utility).get_expr()
    # ntwk.disp_expr(utlt)

    # # process each variable in the variable list
    # varlst = utlt[net_name.varlst]
    # for var in varlst:
        # dcp_var.ps_var(xpd, var)        
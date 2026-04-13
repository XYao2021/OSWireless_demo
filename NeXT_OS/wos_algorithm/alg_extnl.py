#######################################################
# Date: 07/16/2016
# Author: Zhangyu Guan
# Project Manager: Tommaso Melodia, Zhangyu Guan
# Function: add penalization item to utility 
#######################################################

import sys
sys.path.insert(0, './wos-network')
sys.path.insert(0, './wos-decomp')

# from wos-network
import net_func

# from wos-decomp
import dcp_vps, dcp_name

# from current directory 
import alg_name, alg_lexpr, alg_sbst

# from sympy
from sympy import *

def expd_expr(obj_lexpr):
    '''
    obj_lexpr: object of the expression
    
    func: expand utility expression by incorporating variables of other users
    return: updated utility function
    '''
    # repeat to process all external sub-expressions
    while True:
        # get the next external sub-expression, and terminate if none        
        dict_extnl = get_extnl(obj_lexpr)
        if dict_extnl == None:
            #print('No more external element!')
            break
        else:
            #print('dict_extnl:', dict_extnl)
            pass
                        
        # construct the long expression for the external sub-expression            
        str_lexpr = cstr_lexpr(obj_lexpr, dict_extnl)
        
        
        # # substitute the external sub-expression with the constructed long expression
        # sbst(obj_lexpr, dict_extnl, str_lexpr)    

def get_xtnl(obj_lexpr):
    '''
    obj_lexpr: object of the expression
    
    func: get next external sub-expression
    return: external sub-expression in dictionary
    '''
    # get the string expression
    str_expr = str(obj_lexpr.expr)
    
    # find out all key elements
    dict_elmt = alg_sbst.find_elmt(str_expr)
    
    # name and index of nonleaf element 
    xtnl_name = None
    xtnl_idx = None     
    xtnl_full = None        # full name
    
    # check every element
    num_elmt = len(dict_elmt['lst_name'])           # total number of elements
    for nm in range(num_elmt):
        if is_xtnl(obj_lexpr, dict_elmt['lst_name'][nm]):
            xtnl_name = dict_elmt['lst_name'][nm]
            xtnl_idx = dict_elmt['lst_idx'][nm]
            xtnl_full = dict_elmt['lst_fullname'][nm]
            break
            
    if xtnl_name == None:                           # no external element was found
        return None
    else:                                           # found, return name and index 
        return {'name':xtnl_name, 'idx':xtnl_idx, 'fullname': xtnl_full}    

def is_xtnl(obj_any, str_elmtname):
    '''
    obj_any: any object via which other elements can be accessed
    str_elmtname: name of element in string
    
    func: determine if the element is external element
    return: True or False
    '''
    obj_elmt = obj_any.get_netelmt(str_elmtname)       # object with name str_elmtname    
    b_isextnl = obj_elmt.is_xtnl()    
    #print('{} is external: {}'.format(str_elmtname, b_isextnl))
    return b_isextnl     

def cstr_lexpr(obj_any, dict_extnl):
    '''
    obj_any: object of any network element, via which other elements can be accessed
    dict_extnl: dictionary of element {'name', 'index'}
    
    func: construct the long expression of the element
    return: constructed long expression in string
    '''    
    
    # extract object for the element
    obj_elmt = obj_any.get_netelmt(dict_extnl['name'])
    
    # extract formular
    dict_fmlr = obj_elmt.get_expr()
    
    # include index into the formula
    str_lexpr = attach_id(dict_fmlr, dict_extnl['idx'])
    
    return str_lexpr
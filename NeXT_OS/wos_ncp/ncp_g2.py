#######################################################
# Class definition of network control problem
#######################################################
import sys, os, inspect

sys.path.append("../")
sys.path.append("../wos-dir/")
sys.path.append("../wos-network/")
sys.path.append("../../")
sys.path.append("../../NeXT-PPS")
sys.path.append("../../../")

sys.path.insert(0, '../wos-network')
sys.path.insert(0, '../wos-dir')
sys.path.insert(0, '../../NeXT-PPS')

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))

sys.path.insert(0, parent_dir + '\OSW_G2_elmtlib\element_library')

import ncp_name_g2

from sympy.parsing.sympy_parser import parse_expr
import sympy as smp

import mobi_config_g2
from collections import OrderedDict 
           
class ncp_func_g2():
    '''
    General functions for vertial and horizontal decomposition
    '''
    def __init__(self, info):
        for elmt in info.keys():
            setattr(self, elmt, info[elmt])
        
    def gen_component_g2(self, expr):
        '''
        Func: Generate component expression based on dual expression
        
        expr: the expression to be analyzed 
        
        reutrn: the list of component expressions 
        '''
        # Convert to symbolic domain 
        sym_expr_dual = parse_expr(expr)
        # print('xxxxxx', sym_expr_dual)

        # Expanded dual expression
        if mobi_config_g2.expansion_flag == True:
            sym_expr_dual = smp.expand(sym_expr_dual)
        else:
            sym_expr_dual = smp.simplify(sym_expr_dual)

        # print("Dual expression to components expression is:", sym_expr_dual)

        # Add the condition to check no. of terms in the sub-problem expression 04/16/2025
        # If the expression has only one term, then the components list will copy the expression
        # without breaking the expression to component expressions.
        # If the expression has multiple terms, then break the expression to component expressions.
        if len(sym_expr_dual.as_ordered_terms()) == 1:                  # count additive terms
            list_comp_expr = list(sym_expr_dual.as_ordered_terms())  # convert tuple to list
        else:
            list_comp_expr = list(sym_expr_dual.args)  # convert tuple to list


        # no_terms = sym_expr_dual.as_ordered_terms()
        # print("No. of terms", len(no_terms))


        return list_comp_expr

    def walk_tree_g2(self, expr):    
        '''
        Walk through the tree of the expression, return all the operands contained in the expression
        
        expr: the expression tree to walk through
        
        return: the list of all the operands
        '''
        
        list_operand = []
        for arg in expr.args:
            list_operand.append(arg)                                # Record the current operand
            operands_in_child_expr = self.walk_tree_g2(arg)            # Record the operands in the current operands
            list_operand = list_operand + operands_in_child_expr

        return list_operand
        
    def is_single_item_expr(self, expr):
        '''
        func: check if expr contains multiple component expressions
        
        expr: symbolic expression
        
        return: True if yes, False if not
        '''        
        if self.walk_tree_g2(expr) == []:
            return True
        else:
            return False
                
    def get_subprob_g2(self, name_prob):
        '''
        Return the object of the subproblem with given name name_prob
        If nonexistent, return None
        '''       

        if hasattr(self, name_prob):    
            prob_obj = getattr(self, name_prob)        
        else:   
            prob_obj = None

        return prob_obj  

    def create_subprob(self, name_prob):
        '''
        create a subproblem with given name, initialized to None
        '''
        
        setattr(self, name_prob, None)
        prob_obj = getattr(self, name_prob)
        
        return prob_obj
        
    def add_expr_to_suprob_g2(self, name_prob, expr):
        '''
        add an expression to an existing subproblem
        '''
        # if the subproblem has not been created, created one
        if self.get_subprob_g2(name_prob) is None:
            self.create_subprob(name_prob)
        
        # get the orignal expression
        prob_ori = self.get_subprob_g2(name_prob)
        
        # add the expresion to the originl expression
        if prob_ori is None:
            prob_new = expr
        else:
            prob_new = prob_ori + expr
        
        # udpate the subprob
        setattr(self, name_prob, prob_new)
        
        return self.get_subprob_g2(name_prob)  

    def get_netelmt(self, elmt_name):
        '''
        Return the object of the parameter with name para_name
        '''
       
        # get ncp
        ncp = self.ncp
         
        # get network element
        # construct network attribute corresponding to elmt_name        
        
        if hasattr(ncp, elmt_name) == False:      
            # the requested network element doesn't exist
            # if the wanted element does not exist, notify the network
            # will be implemented in future
            
            return None
        else:
            return getattr(ncp, elmt_name)          
        
class lag(ncp_func_g2):
    '''
    definition of lagrangian multiplier
    '''
    def __init__(self, info): 
        ncp_func_g2.__init__(self, info)
        

class exprhldr_g2(ncp_func_g2):
    '''
    Save the expression in expression holder
    This will hold name and expression
    '''
    def __init__(self, info): 
        ncp_func_g2.__init__(self, info)
        
        self.lag = None         # Lagrangian coefficient
        self.expr_lag = None    # expression after applying Lagrangian coefficient
      
        self.layer = None       # default protoco layer of this constraints
        self.hid = None         # horizontal id for distributed decomposition        

            
    def ping(self):    
        print('----------------------------')
        print(self.name, ':', self.expr)
        print('expr_lag:', self.expr_lag)
        
        
    def cstr_lag_name(self):
        '''
        3.17.20: ZG: Construct the name of the Lagrangian coefficient
        '''
        
        return self.name + '_lag'
        
        
    def gen_lag_coef_g2(self):
        '''
        3.16.20: ZG: Generate Lagrangian coefficient for the expression
        
        return: dictionary with the name of the lagrangian coefficient
        '''        
        # contruct name for lagrangian coefficient
        #print(self.__dict__)
        self.lag = self.cstr_lag_name()       
        ##################################################
        # register this coefficient in ncp
        info = {'ncp': self.ncp, 'parent': self, 'name': self.lag}
        info['layer'] = self.layer
        info['hid'] = self.hid
        setattr(self.ncp, self.lag, lag(info))        
        ##################################################
        
        return {'lag':self.lag, 'hid': self.hid}
        
    def get_lag(lag_name):
        '''
        return the object with name lag_name
        '''
        getattr(self.ncp, lag_name)
        
    def apply_lag(self):
        '''
        3.17.20: ZG: Apply Lagrangian coefficient to the expression
        '''
        self.expr_lag =  self.expr + '*' + self.lag
        
        return self.expr_lag
        
    def connect_to_dependent(self, dependent_elmt):
        '''
        - func: connect this expression to the associated network element dependent_elmt
        
        - dependent_elmt: the network element for which the  expression is defined, the protocl layer and
          horizontal id (hid) will be used as the default layer and hid of the expression        
          
        - return: default layer and hid of the expression
        '''
        
        # get the object of the dependent network element
        elmt_obj = self.ntwk.get_netelmt(dependent_elmt)

        # set default layer 
        self.layer =  elmt_obj.layer
        
        # set default hid
        self.hid = elmt_obj.hid

        # set dependent network element
        self.dependent = elmt_obj

        return (self.layer, self.hid)
        
    def connect_to_dependent_g2(self, dependent_elmt):
        '''
        - func: connect this expression to the associated network element dependent_elmt
        
        - dependent_elmt: the network element for which the  expression is defined, the protocl layer and
          horizontal id (hid) will be used as the default layer and hid of the expression        
          
        - return: default layer and hid of the expression
        '''
        
        # get the object of the dependent network element
        elmt_obj = self.ntwk.get_netelmt_g2(dependent_elmt)

        # set default layer 
        self.layer =  elmt_obj.layer
        
        # set default hid
        self.hid = elmt_obj.hid

        # set dependent network element
        self.dependent = elmt_obj

        return (self.layer, self.hid)
        

class ncp_g2(ncp_func_g2):
    '''
    Template of network control problem
    '''
    def __init__(self, ntwk_obj):    
        info = {'ncp': self, 'parent': self}
        ncp_func_g2.__init__(self, info)

        self.operands = None                #operands
        self.operation = None               #opertion

        # Which expression is the utility
        self.utility = None

        # The network object to be controlled
        self.ntwk = ntwk_obj
        
        # expression counter, initialized to zero
        # increase 1 after new expression created
        self.expr_cnt = 0
        self.expr_list = []                 #init expression list, used to save all the expressions
        
        
    def mkexpr_new_g2(self, *args):
        '''
        func: This is the wrapper function of mkexpr defined below. In mkexpr, the operand contains only 
        the expaneded expression. In this function, it contains both the expanded and the orignal epxressions
        
        return: expression dictionary containing both expanded and orignal expressions
        '''
        
        # Get the operation
        if len(args) > 1:
            operation = args[-1]   # The last argument is operation
            #print ("operation = ",operation)
        else:
            operation = None        # There is no operation

        # Get the object of the one or two variables
        var_list = args[:-1]
        # The number of operands
        num_oper = len(var_list)
        
        # There is only one operand
        if num_oper == 1:
            # This operand is a dictionary
            if type(var_list[0]) is dict:
                oper1_xpd = var_list[0]['expr_xpd']             # Get the expanded expression
                oper1_ori = var_list[0]['expr_ori']             # Get the original expresion

                
            # This operand is a constant string
            else:   
                oper1_xpd = var_list[0]
                oper1_ori = var_list[0]
            
            expr_ori = self.mkexpr(oper1_ori, operation)
            expr_xpd = self.mkexpr(oper1_xpd, operation)
            
        # There are two operands
        elif num_oper == 2:
            # This operand is a dictionary
            if type(var_list[0]) is dict:
                #print(var_list[0])
                oper1_xpd = var_list[0]['expr_xpd']             # Get the expanded expression of the 1st operand
                oper1_ori = var_list[0]['expr_ori']             # Get the original expresion of the 1st operand      
            
            # This operand is a constant string
            else:
                oper1_xpd = var_list[0]
                oper1_ori = var_list[0]                

            # This operand is a dictionary
            if type(var_list[1]) is dict:
                oper2_xpd = var_list[1]['expr_xpd']             # Get the expanded expression of the 2nd operand
                oper2_ori = var_list[1]['expr_ori']             # Get the original expresion of the 2nd operand    
            
            # This operand is a constant string
            else:
                oper2_xpd = var_list[1]
                oper2_ori = var_list[1]
    
            expr_xpd = self.mkexpr(oper1_xpd, oper2_xpd, operation)    
            expr_ori = self.mkexpr(oper1_ori, oper2_ori, operation) # Construct the original expression

        return {'expr_xpd': expr_xpd, 'expr_ori': expr_ori}
             
    def mkexpr(self, *args):
        '''
        Define expressions, compose expressions, compare expressions
        args passes 1, 2 or 3 arguments, corresponding to operations with no, 1 and 2 arguments
        
        Guan, 3.1.20: change the function name from ncp_crt_fmlr to mkexpr
        '''
        ################################################################

        #supported operations class is in ncp_name.py
        supported_operations = ncp_name_g2.sptd_oprt
        
        # Get the operation
        if len(args) > 1:
            operation = args[-1]   # The last argument is operation
            #print ("operation = ",operation)
        else:
            operation = None        # There is no operation

        ################################################################
        # Get the object of the one or two variables
        var_list = args[:-1]

        ################################################################
        # Get the expression for each variable object
        expr_list = OrderedDict()
        expr_list['expr_list1'] = None
        expr_list['expr_list2'] = None
        key = list(expr_list.keys())
        for item_idx in range(len(var_list)): 
            # if this operand is an object, get the corresponding expression
            if str(type(var_list[item_idx])).find('class') >= 0 and str(type(var_list[item_idx])).find('str') < 0:
                expr_list[key[item_idx]] = var_list[item_idx].name #self.ncp_get_expr(var_list[item_idx])
                print('Object operand detected')
                pass
            
            # otherwise, if the operand is a string, use it directly
            elif isinstance(var_list[item_idx], str):
                expr_list[key[item_idx]] = var_list[item_idx]                 
            
            # otherwise, error
            else:
                print('The operand type is not supported!')
                exit(0)          

        ################################################################
        # Construct the expression list        
        if expr_list['expr_list2'] is not None:

            if expr_list['expr_list1'] == '':
                fmlr = '(' + expr_list['expr_list2']  + ')'
            elif expr_list['expr_list2'] == '':
                fmlr = '(' + expr_list['expr_list1']  + ')'
            else:
                fmlr = '(' + expr_list['expr_list1'] + operation + expr_list['expr_list2']  + ')'
        else:
            fmlr = operation + '(' + expr_list['expr_list1'] + ')'

        return fmlr

    def record_expr_g2(self, expr_dict, dependent_elmt = None):
        '''
        Func:
        Record the expression name and expression
        Expression names are constructed and saved to a dictionary
        Expression object is created using exprhldr class defined above, and recorded in ncp
        
        Argument:
        - dependent_elmt: the network element for which the  expression is defined, the protocl layer and
          horizontal id (hid) will be used as the default layer and hid of the expression
          
        - expr_dict: the expression dictionary, including the expanded and original expressions
        '''
        
        # construct the name of the expression
        expr_name = ncp_name_g2.expr + '_' + str(self.expr_cnt)
        
        # get the original and expanded expressions 
        expr_ori = expr_dict['expr_ori']        # original
        expr_xpd = expr_dict['expr_xpd']        # expanded
        
        # Construct info dictionary
        # To be backward compability, expr_xpd is still stored in 'expr'        
        # expr_ori is newly added
        info = {'expr': expr_xpd, 'name': expr_name, 'ntwk': self.ntwk, 'ncp': self, 'parent': self}
        info['expr_ori'] = expr_ori
        
        # create the expression object
        expr_obj = exprhldr_g2(info)

        # record the object in ncp
        setattr(self, expr_obj.name, expr_obj)
        self.expr_list.append(expr_obj.name)

        # update expression counter
        self.expr_cnt = self.expr_cnt + 1

        # connect this expression to the dependent network element       
        if dependent_elmt is not None:
            info = expr_obj.connect_to_dependent_g2(dependent_elmt)

        return expr_name, info
              
    
    def ping(self):
        '''
        ping function for the ncp expression object
        '''

        print('Total expressions:', self.expr_cnt)
        for expr in self.expr_list:
            x = getattr(self, expr)
            print(x.name, " (expanded): ", x.expr)     # expanded expression
            print(x.name, " (original):", x.expr_ori)  # original expression

        
        
    def set_utlt(self, name_expr):
        '''
        3.12.20:
        user can use this method to set utility from wos-demo.py
        '''
        self.utility = name_expr
            
    def set_para_g2(self, parameter, para_type):
        '''
        Set a specific parameter to the NCP
        '''
        setattr(self, para_type, parameter)

    def get_expr(self, name_expr):  
        '''
        3.12.20
        user can use this method to get expression from wos-demo.py
        '''
        expr_obj = getattr(self, name_expr)
        return expr_obj
    
    def get_cstr_list(self):
        return self.expr_list[1:]
        
        
    def set_var(self, var_name):
        '''
        Record the name of an optimization variable if it has not been recorded
        '''
        if var_name not in self.list_var:
            self.list_var.append(var_name)
            
    def aux_var_expr_gen(self, expr, elmnt_list, type_name, var_name, layer_name):
        #print('Generating aux var expr')
        ##print(elmnt_list)
        if type_name == 'type_1':
            new_var_name = var_name+'_'+str(elmnt_list[0])[-1:]+'_'+str(elmnt_list[1])[-1:]
            exp = elmnt_list[0]-elmnt_list[1]
            act_exp = expr.subs(exp, new_var_name)
            #print(act_exp)
        else:
            print('Not supported for now.')
        
        self.set_layer_aux_var(new_var_name, elmnt_list, layer_name)
        self.add_constraint_expression(new_var_name, layer_name, str(exp), elmnt_list)
        return act_exp
        
    def set_layer_aux_var(self, new_var_name, elmnt_list, layer_name):
        for elmt in elmnt_list:
            #print(elmt)
            elm_obj = self.ntwk.get_netelmt_g2(str(elmt))
            if elm_obj.layer == layer_name:
                new_ntwk_var = str('_'+new_var_name)
                #print(new_ntwk_var)
                setattr(self.ntwk, new_ntwk_var, elm_obj)
                    
    def add_constraint_expression(self, new_var_name, layer_name, exp, elmnt_list):
        expr = {'expr_xpd': '', 'expr_ori': ''}
        expr = self.mkexpr_new_g2(expr, new_var_name, '+')
        expr = self.mkexpr_new_g2(expr, exp, '-')
        for elmt in elmnt_list:
            #print(elmt)
            elm_obj = self.ntwk.get_netelmt_g2(str(elmt))
            if elm_obj.layer == layer_name:
                dep_name = str(elmt)
        expr_name,info = self.record_expr_g2(expr, dep_name) 
            
    
    
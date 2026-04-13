# single-layer network control problem

# symbolic computing library
from sympy.parsing.sympy_parser import parse_expr
import sympy as smp

import ncp_g2
import net_name_g2
from string import ascii_lowercase
from sympy import sympify

class ncp_xlayer_decomp_g2(ncp_g2.ncp_func_g2):
    '''
    Class of the vertically decomposed network control problem
    '''
    
    def __init__(self, ncp_obj):  
        
        # save network object for future user
        self.ncp  = ncp_obj
        self.ntwk = ncp_obj.ntwk
        
        # overall dual expression after absorbing the constraints into the utility
        self.expr_dual = None
        self.expr_dual_sym = None   # symbolic expression of expr_dual
        
        # list of component expressions of the dual expression
        self.list_comp_expr = []
        
        # list of layers of component expressions
        self.list_layer = []
        
        # list of names of subproblems
        self.list_subprob = []

        # list of lagrangian coefficients
        self.list_lag = []
        
        # mapping from lagrangian coefficient to constraints
        self.mapping_lag_to_cstr = {}
        
        # mapping from lagrangian coefficent to node
        self.mapping_lag_to_node = {}
          
        # Check for expression decomposability
        self.decomposability_check()
        print('----------------------------------------------------')
        self.ncp.ping()
        print('----------------------------------------------------')
        # generating dual expression
        self.gen_dual_g2()
        #exit()
        #exit()
        # get the list of all expressions
        all_expr_name = self.ncp.expr_list

        # process each expresion
        for expr_name in all_expr_name:     

            # get the expression object
            expr_obj = self.ncp.get_expr(expr_name)

            # if this expression is utility, process its original expression
            # otherwise process lag expression
            if expr_name == self.ncp.utility:
                expr = expr_obj.expr
            else:
                expr = expr_obj.expr_lag
            #print('a', expr)
            comp_list = self.gen_component_g2(expr)
            #print(comp_list)
            #exit()
            layer_list, soln_list = self.det_layer_g2(comp_list, expr_obj)
            #print(expr,layer_list)
            #exit()
            self.vert_decomp_g2(comp_list, layer_list, soln_list)
            #exit()
            
    def ping(self):
        print('-----------Dual Expression----------------------')
        print(self.expr_dual)
        print('-----------List of subproblems------------------')
        print(self.list_subprob)
        
        for subprob in self.list_subprob:
            expr = self.get_subprob_g2(subprob)
            print(subprob)
            print(expr)
        
    def gen_dual_g2(self):
        '''
        Func: Generate Lagrangian dual expression
        '''
        
        print('Generating dual expression...')
        # Get the list of all constraints in the network control problem
        list_cstr = self.ncp.get_cstr_list()

        # At the beginning, the dual expression contains only the utility
        utlt_name = self.ncp.utility                # name of the utility expression
        utlt_obj = self.ncp.get_expr(utlt_name)     # object of the utility expression
        utlt_expr = utlt_obj.expr                   # string expression of utility        
        self.expr_dual = utlt_expr                  # Initialize the dual expression
        # Loop over all constraints
        # For each constraint, introduce a Lagrangian multiplier
        for cstr in list_cstr:
            cstr_obj = self.ncp.get_expr(cstr) 

            # Generate Lagrangian coefficient for the constraint
            dic_lag = cstr_obj.gen_lag_coef_g2()

            # get the name and hid of the Lagrangian coefficent
            lag_name = dic_lag['lag']
            lag_hid  = dic_lag['hid']
            #print(lag_name, lag_hid)
            # record the Lagrangian coefficent 
            self.list_lag.append(lag_name)
            
            # map the Lagrangian coefficent to the constraint
            self.mapping_lag_to_cstr[lag_name] = cstr     

            # map the Lagrangian coefficent to node
            self.mapping_lag_to_node[lag_name] = lag_hid
                        
            # Apply the Lagrangian coefficient to the constraint
            cstr_lag = cstr_obj.apply_lag()

            # Absorb the constraints into the utility function
            # Not needed any more, the decomposition will operate the utility and constraints directly
            # Will not be used
            self.expr_dual = self.expr_dual + '+' + cstr_lag

    def rgst_lag_in_node(self, obj_ntwk, lag_name, node_name):
        '''
        Func: register the Lagrangian coefficent in the corresponding node
        
        obj_ntwk: network object
        lag_name: name of the Lagrangian coefficent to be registered
        node_name: name of the node
        '''
        
        # get the node object
        obj_node = obj_ntwk.get_netelmt(node_name)

        # register the Lagrangian coefficent in the node
        obj_node.rgst_lag_in_node(lag_name)
      
    def det_layer_g2(self, comp_list, expr_obj):
        '''
        Func:
        Determine which layer each component expression belongs
        
        Input: 
        comp_list -- the list of component expressions
        expr_obj -- the expression object to which comp_list belongs
        
        Return:
        list_layer -- the list of layers for the component expressions
        '''

        # Initialize the list of layers for component expressions
        list_layer_op = []    
        list_soln_op = []
        #print(expr_obj.__dict__)
        #print(comp_list)
        # Loop over all component expressions
        for expr in comp_list:
            # Determine the layer for the current component expression            
            # First, get the list of operands contained in this expression 
            list_operand = self.walk_tree_g2(expr)
            #print('a', expr)
            #print('b', list_operand)
            # if no operations contained in expr, the operand is expr itself
            if list_operand == []:  
                list_operand = [expr]
                         
            # Loop over all operands, determine the layer for each operand
            layer = []
            for op in list_operand:
                layer_op = self.det_layer_op_g2(op)
                soln_op = self.det_soln_mthd_g2(op)
                # Record the layer for the current operand
                if layer_op is not None:
                    list_layer_op.append(layer_op)
                    layer.append(layer_op)
                    list_soln_op.append(soln_op)
                   
        return list_layer_op, list_soln_op
       
    def decomposability_check(self):
        '''
        The func is responsible for detecting the decomposability of the expression
        If the expression is not decomposable, reformulate it to make it decomposable
        '''
        print('Decomposability Detection and Reformulation ....')
        #self.gen_dual_g2()
        all_expr_name = self.ncp.expr_list
        for expr_name in all_expr_name:     
            # get the expression object
            expr_obj = self.ncp.get_expr(expr_name)
            # if this expression is utility, process its original expression
            # otherwise process lag expression
            if expr_name == self.ncp.utility:
                expr = expr_obj.expr
            else:
                expr = expr_obj.expr_lag
            
            if expr is not None:
                expr_symp = sympify(expr)
                comp_list = self.gen_component_g2(expr)
                reform_expr = ''
                for expr2 in comp_list:
                    layer_list = self.det_layer_g2_reform(expr2)
                    if len(layer_list) > 1:
                        uniq_list = self.get_uniq_list(layer_list)
                        if not all(x == layer_list[0] for x in layer_list):
                            print('ERROR: Expression "%s" is not decomposable. The expression contains sub-components from different layers:%s.'%(expr2, uniq_list))
                            #print('Trying to locate user specified decomposition model...')
                            
                            # Get the pattern of the expression and the elements that form the pattern
                            # for example 1/(lkcap-ssrate)
                            # follows a pattern of 1/(a-b)
                            # This will help in determining the decomposition method 
                            # that can be used for decomposing this problem
                            pattern, pattern_elmnts = self.get_pattern(expr2)
                            #print('The expression follows the pattern "%s"'%pattern)
                            #print('The pattern elements are "%s"'%pattern_elmnts)

                            # Find the decomposition model name
                            decomp_model, type_name, var_name, layer_name = self.get_decomp_model(pattern)
                            if decomp_model == None:
                                print('FAILED!!! Decomposition model not defined for pattern %s.'%pattern)
                                print('Please define and provide the name of the decompostion model during network control problem defnition and Try Again.')
                                exit()
                            else:
                                #print('User-defined decomposition model detected')
                                #print('Expression "%s" following pattern "%s" will be decomposed using "%s" method \n' %(expr, pattern, decomp_model))
                                new_expr = self.ncp.aux_var_expr_gen(expr2, pattern_elmnts, type_name, var_name, layer_name)
                            expr_symp = expr_symp.subs(expr2, new_expr)
                            print('The expression "%s" is converted to "%s" to make it decomposable.'%(expr2, new_expr))
                            print('The new expression is associated to "%s" layer.'%layer_name)
                            setattr(expr_obj, 'expr', str(expr_symp))
                            #exit()
                    else:
                        print('All expressions are decomposable')
            

            #self.ncp.ping()
    def get_pattern(self, expr):
        '''
        Determine the pattern of the expression expr
        '''
        
        list_operand = self.walk_tree_g2(expr)
        list_elmnt_to_be_replaced = []
        for op in list_operand:
            layer_op = self.det_layer_op_g2(op)
            if layer_op is not None:
                list_elmnt_to_be_replaced.append(op)
        for elmnt in range(len(list_elmnt_to_be_replaced)):
            expr = expr.subs(list_elmnt_to_be_replaced[elmnt], ascii_lowercase[elmnt])
        #print(expr)
        #exit()
        return expr, list_elmnt_to_be_replaced
       
    def get_decomp_model(self, pattern):
        '''
        Determine decomposition model name based on the pattern
        '''
        if str(pattern) in list(net_name_g2.known_pattern_type.keys()):
            model_name = net_name_g2.known_pattern_type[str(pattern)]['decomp']
            type_name = net_name_g2.known_pattern_type[str(pattern)]['type']
            if type_name == 'type_1':
                var_name = net_name_g2.known_pattern_type[str(pattern)]['aux']
                layer_name = net_name_g2.known_pattern_type[str(pattern)]['layer']
        else:
            model_name = None
            type_name = None
        return model_name, type_name, var_name, layer_name
        
    def get_uniq_list(self, list_elements):
        '''
        Get unique list based on the provided list_elements)
        '''
        uniq_list = []
        for elm in list_elements:
            if elm not in uniq_list:
                uniq_list.append(elm)
                
        return uniq_list
        
    def det_soln_mthd_g2(self, operand):
        '''
        Determine solution method
        '''
        str_operand = str(operand)
        obj_elmt = self.ntwk.get_netelmt_g2(str_operand)
        if obj_elmt is not None:
            if hasattr(obj_elmt, 'soln_frmwk1'):
                soln_mthd = obj_elmt.soln_frmwk1
                
                return soln_mthd
        
        
    def det_layer_op_g2(self, operand):
        '''
        Func:
        Determine the layer for operand (symbolic expression)
        
        Return:
        The layer this operand belongs to 
        '''
                    
        # Conver the symbolic operand to string
        str_operand = str(operand)

        # Check if the network has an element with name str_operand
        # If yes, return the element object; otherwise return None
        obj_elmt = self.ntwk.get_netelmt_g2(str_operand)

        if obj_elmt is not None:
            layer =  obj_elmt.layer
        else:
            layer = None

        return layer
        
                          
    def vert_decomp_g2(self, comp_list, layer_list, soln_list=None):
        '''
        Func: vertical decomposition - decompose the problem into single-layer subproblems
        
        Input: 
        comp_list: list of component expressions 
        layer_list: corresponding layers 
        
        Output: 
        updated list of names of subproblems (self.list_subprob)
        For each subproblem an attribute is created with the same name as the subproblem
        '''
        # get the number of component expressions
        num_expr = len(comp_list)

        # loop over all component expressions   
        for idx in range(num_expr):
            # get the layer this expression belongs to
            layer = layer_list[idx]

            # # add the print to verify the layer assignments
            # print("Number of components:", len(comp_list))
            # print("Component list:", comp_list)
            # print("Layer list:", layer_list)

            if soln_list is not None:
                soln_frm = soln_list[idx]
                if soln_frm is not None:
                    layer = layer+'_'+soln_frm
                
            # Check if a subproblem has been created corresponding to this layer, if not create one
            if self.get_subprob_g2(layer) is None:
                # Create an empty subproblem corresponding to this layer
                setattr(self, layer, '')
                # Record this subproblem in the subproblem list
                self.list_subprob.append(layer)
                
            # get the corresponding subproblem
            cur_subprob = getattr(self, layer)
            
            # if the current subproblem is empty, initialize  it to the  current component expresion  
            if cur_subprob == '':
                cur_subprob = comp_list[idx]
                
            # Otherwise, add it to the end of the existing expression
            else:
                cur_subprob = cur_subprob + comp_list[idx]  # symbolic 

            # update the subproblem
            setattr(self, layer, cur_subprob)
            
    def det_layer_g2_reform(self, expr):
        '''
        
        '''
        # Determine the layer for the current component expression            
        # First, get the list of operands contained in this expression 
        list_operand = self.walk_tree_g2(expr)
        # if no operations contained in expr, the operand is expr itself
        if list_operand == []:  
            list_operand = [expr]   
        # Loop over all operands, determine the layer for each operand
        layer = []
        for op in list_operand:
            layer_op = self.det_layer_op_g2(op)
            # Record the layer for the current operand
            if layer_op is not None:
                layer.append(layer_op)
        return layer
        
        
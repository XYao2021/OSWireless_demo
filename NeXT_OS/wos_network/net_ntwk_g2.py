# add external dir into search list
import sys, os, inspect

sys.path.append("../")
sys.path.append("../wos-dir/")
sys.path.append("../wos-ncp/")
sys.path.append("../../")
sys.path.append("../../NeXT-PPS")

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
current_dir = os.path.dirname(os.path.dirname(current_dir))
parent_dir = os.path.dirname(current_dir)

# print("current directory:" ,current_dir)
# print("parent directory:" ,parent_dir)

sys.path.insert(0, parent_dir+'/OSW_G2_elmtlib/element_library')
# sys.path.insert(0, parent_dir+'\OSW_G2_elmtlib\element_library\\mmwave')
# sys.path.insert(0, parent_dir+'\OSW_G2_elmtlib\element_library\thz')
# sys.path.insert(0, parent_dir+'\OSW_G2_elmtlib\element_library/\\microwave')
# sys.path.insert(0, parent_dir+'\OSW_G2_elmtlib\element_library\\sixghz')

import netcfg_g2
import os_dir

from sympy.parsing.sympy_parser import parse_expr
import sympy as smp
import net_func_g2, net_name_g2, net_para_g2

def new_ntwk_g2(ntwk_type):
    '''
    create a network of the specified network type
    '''
    elmt_name = net_name_g2.ntwk
    elmt_num  = 1    
    elmt_type = ntwk_type
    
    # changes:
    addi_info = {'ntwk':None, 'parent':None}
    info = net_func_g2.mkinfo_g2(elmt_name, elmt_type, elmt_num, addi_info)    # network topology info, 1 network created

    return net_ntwk_g2(info)    

class net_ntwk_g2:
    def __init__(self, name):
        # from base network element

        # # initialize all required lists to prevent AttributeError
        # self.node_list = []
        # self.antenna_list = []
        # self.session_list = []
        # self.link_list = []
        # self.mimo_node_list = []

        net_func_g2.netelmt_g2.__init__(self, name) 
        self.clear_driver_file()
        
    def ping(self):
        net_func_g2.netelmt_g2.ping(self)
          
    def clear_driver_file(self):
        open(net_name_g2.driver_plane_filename, 'w').close()

    def attach(self, element_name, num_elmnt, addi_info=None):
        '''
        func: Add the specified element to the network
        elmt_name: Name of the network element to be attached to the network
        num_elmnt: Total Number of element to be added
        '''

        if addi_info == None:
            info = net_func_g2.mkinfo_g2(element_name, None, 1, {'ntwk':self, 'parent':self})
        else:
            addi_info['ntwk']=self
            addi_info['parent']=self
            info = net_func_g2.mkinfo_g2(element_name, None, 1, addi_info)

        if 'num_ant' not in info['addi_info'].keys():
            info['addi_info']['num_ant'] =1

        if not hasattr(self, '_'+element_name):
            elmt_module = __import__(element_name)

            # ######========== ensures the module is correctly imported within wos-network 02/28/2025 ==========######
            # try:
            #     elmt_module = __import__(f"wos-network.{element_name}", fromlist=[element_name])
            # except ModuleNotFoundError:
            #     print(f"Error: Module '{element_name}' not found. Ensure it exists in wos-network.")

            class_to_call = getattr(elmt_module, element_name)

            elmnt_set = class_to_call(info)
            setattr(self, element_name, elmnt_set)

            print('Attaching', element_name, 'to the network' )

        local_list =[]
        all_list = []
        for idx in range(0,num_elmnt):
            local_elmnt = net_func_g2.netelmt_g2.attach(self, element_name, idx, addi_info)
            local_list.append(local_elmnt)

        return local_list       #, all_list

    ######========== define a new attach() function to deal with the element_module issue 02/28/2025 ==========######
    # def attach(self, element_name, num_elmnt, addi_info=None):
    #     '''
    #     func: Add the specified element to the network
    #     elmt_name: Name of the network element to be attached to the network
    #     num_elmnt: Total Number of element to be added
    #     '''
    #
    #     if addi_info is None:
    #         addi_info = {'ntwk': self, 'parent': self}
    #     else:
    #         addi_info['ntwk'] = self
    #         addi_info['parent'] = self
    #
    #     info = net_func_g2.mkinfo_g2(element_name, None, 1, addi_info)
    #
    #     if 'num_ant' not in info['addi_info'].keys():
    #         info['addi_info']['num_ant'] = 1
    #
    #     if not hasattr(self, '_' + element_name):
    #         try:
    #             elmt_module = __import__(f"wos-network.{element_name}", fromlist=[element_name])
    #         except ModuleNotFoundError:
    #             try:
    #                 elmt_module = __import__(element_name)
    #             except ModuleNotFoundError:
    #                 print(f"Error: Module '{element_name}' not found. Ensure it exists in wos-network or sys.path.")
    #                 return None
    #
    #         if hasattr(elmt_module, element_name):
    #             class_to_call = getattr(elmt_module, element_name)
    #             elmnt_set = class_to_call(info)
    #             setattr(self, element_name, elmnt_set)
    #             print(f'Attaching {element_name} to the network')
    #         else:
    #             print(f"Error: '{element_name}' class not found in module '{elmt_module.__name__}'.")
    #             return None
    #
    #     local_list = []
    #     for idx in range(0, num_elmnt):
    #         local_elmnt = net_func_g2.netelmt_g2.attach(self, element_name, idx, addi_info)
    #         local_list.append(local_elmnt)
    #
    #     return local_list

    ######========== finish the attach() function to deal with the element_module issue 02/28/2025 ==========######

    def install_model(self, attr, model_name, model_parameter=None):
        '''
        func: install the specified model to the attributes
        attr: List/single element attributes for which the model has to be attached
        model_name: Name of the model
        model_parameters: List or single element dependent attribute of main attribute
        '''
        attr = self.get_list(getattr(net_name_g2, attr))
        if type(attr) is list:
            for attrrr in attr:
                attrobj = self.get_netelmt_g2(attrrr)   
                setattr(attrobj, 'para_type', 'itmd_para')
                setattr(attrobj, 'expr_hldr', model_name)
                setattr(attrobj, 'model_parameter', model_parameter)
        else:
            attrobj = self.get_netelmt_g2(attr)   
            setattr(attrobj, 'para_type', 'itmd_para')
            setattr(attrobj, 'expr_hldr', model_name)
            setattr(attrobj, 'model_parameter', model_parameter)

    def set_soln_mthd(self, parameter, soln_mthd, soln_frmwk, addi_info=None):
        '''
        Set a specific solution method to the optimizable variable
        soln_mthd - solution method (func_approx, rl, ...)
        soln_frmwk - solution framework i.e., specific func_approx or rl algorithms (esn, q learning, sarsa ....)
        addi_info - additional information about second solution framework to be solved in addition to soln_frmwk
        '''
        parameter_list = self.get_list(getattr(net_name_g2, parameter))
        if addi_info != None:
            print('Setting', soln_frmwk, 'and', addi_info , 'as solution algorithm(s) for', parameter)
        else:
            print('Setting', soln_frmwk, 'as solution algorithm(s) for', parameter)

        for param in parameter_list:
            para_obj = self.get_netelmt_g2(param)   
            setattr(para_obj, 'soln_hldr', soln_mthd)
            setattr(para_obj, 'soln_frmwk1', soln_frmwk)
            if addi_info != None:
                setattr(para_obj, 'soln_frmwk2', addi_info)

            
    def cnst_local_name(self, element_name, idx):
        '''
        func: Construct the local name for the the specified element name with provided index (idx)
        '''
        return element_name + '_'+ str(idx)
        
    def cnst_global_name(self, element_name):
        '''
        func: Construct the global name for the the specified element naem
        '''
        counter_name = element_name+'_counter'

        # Set and Initialize the counter if it is not present in the ntwk object
        if counter_name not in self.__dict__.keys():
            cntr_val=0
            setattr(self, counter_name, cntr_val)
        # Retrieve the current value of the counter, increment it by 1 to get new global name
        else:
            cntr_val = getattr(self, counter_name)
            cntr_val+=1
            setattr(self, counter_name, cntr_val)
            
        # Construct the global name
        global_name = element_name + '_'+ str(cntr_val)
        
        return global_name
        
        
    def get_list(self, elmnt_name):
        list_name = elmnt_name+'_list'
        
        return getattr(self, list_name)
        
    def get_netelmt_g2(self, elmt_name):
        '''
        return the network object
        '''   
        # get network element
        # construct network attribute corresponding to elmt_name
        _elmt_name = '_'+elmt_name
        if hasattr(self, _elmt_name) == False:      
            return None
        else:
            return getattr(self, _elmt_name)
            
            
    def add_one_link(self, tx_node, rx_node):
        lk_obj = net_func_g2.netelmt_g2.add_one_link(self, tx_node, rx_node)
        
        return lk_obj
        
    def connect(self, parent_elmnt, elmnt_list):
        '''
        func: connect two network elements
        parent_elmnt: name of the parent element (scalar)
        elmnt_list: list of the element to be connected(list/vector)
        '''
        # Check the criteria for connect function
        if len(parent_elmnt.split())>1:
            print('ERROR: The first argument of "CONNECT" function should be scalar...')
            exit(0)
            
        # Prepare the name of the element sets
        p_obj = self.ntwk.get_netelmt_g2(parent_elmnt)
        if p_obj is None:           # check p_obj is None 03/03/2025
            raise ValueError(f"Error: Could not find parent element '{parent_elmnt}'.")
        elm_obj =self.ntwk.get_netelmt_g2(elmnt_list[0])

        set_p_name = p_obj.type + '_set'
        set_elm_name = elm_obj.type + '_set'
        
        setattr(p_obj, 'dependent_set', set_elm_name)
        
        for elmnt in  elmnt_list:
            elm_obj2 =self.ntwk.get_netelmt_g2(elmnt)
            if hasattr(p_obj, 'oper_freq'):
                setattr(elm_obj2, 'oper_freq', p_obj.oper_freq)
            setattr(elm_obj2, 'dependent_set', set_p_name)
        setattr(p_obj, set_elm_name, elmnt_list)

        # If the connected information needs to be further processed at the network element level
        if hasattr(p_obj, 'update_flag'):
            p_obj.update_info()
        
        # For each element connect it to the parent element
        for elm in elmnt_list:
            elm_obj =self.ntwk.get_netelmt_g2(elm)
            
            # If the element has the specific parent element set
            # Get the current parent element data and add the new element
            if hasattr(elm_obj, set_p_name):
                old_set_list = []
                old_data = getattr(elm_obj, set_p_name)
                for od in old_data:
                    old_set_list.append(od)
                old_set_list.append(parent_elmnt)
                setattr(elm_obj, set_p_name, old_set_list)
            # Else, update the parent element to each child element
            else:
                setattr(elm_obj, set_p_name, [parent_elmnt])
                
        if p_obj.type == 'session':
            self.initialize_hop_info(p_obj)
            self.set_hop_info(p_obj)
            self.write_hop_info_to_file(p_obj)
             
    def initialize_hop_info(self, p_obj):
        '''
        Prepare the previous and next hop information for Source and Destination node for each session 
        p_obj - object of session
        '''
        link_set = p_obj.link_set
        
        # Get first and last link of the session
        first_link = link_set[0]
        last_link = link_set[-1]

        # Get the corresponding objects
        first_link_obj = self.get_netelmt_g2(first_link)
        last_link_obj = self.get_netelmt_g2(last_link)
        
        # Get the transmitter node of first link and receiver node of last link
        first_link_tsmd_nd = first_link_obj.tsmt_nd
        last_link_rcvr_nd = last_link_obj.rcvr_nd

        # Get the corresponding objects
        first_link_tsmd_nd_obj = self.get_netelmt_g2(first_link_tsmd_nd)
        last_link_rcvr_nd_obj = self.get_netelmt_g2(last_link_rcvr_nd)
        
        # If the transmitter node of first link and receiver node of last link 
        # does not have the prev hop and next hop information
        # set the corresponding info
        if not hasattr(first_link_tsmd_nd_obj,'prev_hop'):
            setattr(first_link_tsmd_nd_obj,'prev_hop', 'None')
        if not hasattr(last_link_rcvr_nd_obj,'next_hop'):
            setattr(last_link_rcvr_nd_obj,'next_hop', 'None')

    def set_hop_info(self, p_obj):
        '''
        Prepare the previous and next hop information for all nodes in the session
        p_obj - object of session
        '''
        link_set = p_obj.link_set
        for link in link_set:
            prev_hop_list = []
            next_hop_list = []
            link_obj = self.get_netelmt_g2(link)
            tsmt_nd = link_obj.tsmt_nd
            rcvr_nd = link_obj.rcvr_nd
            tsmt_nd_obj = self.get_netelmt_g2(tsmt_nd)
            rcvr_nd_obj = self.get_netelmt_g2(rcvr_nd)
            if not hasattr(rcvr_nd_obj,'prev_hop'):
                setattr(rcvr_nd_obj,'prev_hop', [tsmt_nd])
            else:
                old_hop = rcvr_nd_obj.prev_hop
                for hop in old_hop:
                    prev_hop_list.append(hop)
                prev_hop_list.append(tsmt_nd)
                setattr(rcvr_nd_obj,'prev_hop', prev_hop_list)
            if not hasattr(tsmt_nd_obj,'next_hop'):
                setattr(tsmt_nd_obj,'next_hop', [rcvr_nd])
            else:
                old_hop = tsmt_nd_obj.next_hop
                for hop in old_hop:
                    next_hop_list.append(hop)
                next_hop_list.append(rcvr_nd)
                setattr(tsmt_nd_obj,'next_hop', next_hop_list)
            
    def write_hop_info_to_file(self, p_obj):        
        '''
        Write the hop information to a file
        Name of the file is defined in net_name_g2 as driver_plane_filename
        p_obj - object of session
        '''
        link_set = p_obj.link_set
        node_set = []
        for link in link_set:
            link_obj = self.get_netelmt_g2(link)
            tsmt_nd = link_obj.tsmt_nd
            rcvr_nd = link_obj.rcvr_nd
            if tsmt_nd not in node_set:
                node_set.append(tsmt_nd)
            if rcvr_nd not in node_set:
                node_set.append(rcvr_nd)

        self.write_content(node_set)

    def write_content(self, elmnt_set):
        h_file = open(net_name_g2.driver_plane_filename, 'a+')
        for node in elmnt_set:
            node_obj = self.get_netelmt_g2(node)  
            next_node = node_obj.next_hop
            prev_node = node_obj.prev_hop
            content = '%s = {}\n%s["'"prev_hop"'"]="'"%s"'"\n%s["'"next_hop"'"]="'"%s"'"'%(node,node, prev_node, node, next_node) +'\n'
            h_file.write(content)
        h_file.close()
        
    def get_expr_g2(self, elmnt_name, para):
        '''
        This is the wrapper funciton for get_expr defined below. Function get_expr will be called
        twice, returning the expanded expression and the original expression, respectively
        
        elmnt_name:  network element 
        para: parameter of the network element         
        '''
        
        # get the original expression
        expr_ori = self.gen_expr_g2(elmnt_name, para, False)

        # get the expanded expression
        expr_xpd =  self.gen_expr_g2(elmnt_name, para, True)

        return {'expr_ori': expr_ori, 'expr_xpd': expr_xpd}
        
    def gen_expr_g2(self, obj_name, para, b_xpd = True):
        '''
        Get information about the object name and ns object name with parameter
        :param obj_name:  network element 
        :param para: parameter of the network element 
        b_xpd: False - get the original expression; True - get the expanded expression
        
        :return: object name with parameter
        '''
        #get object name through get netelmt method in net func
        obj = self.get_netelmt_g2(obj_name)

        #get para obj through net func get para
        para_obj = obj.get_para_g2(para)

        # if the para does not exist
        if para_obj is None:
           return None        

        expr_tuple = para_obj.get_para_expr_g2(b_xpd)  # function defined in net_func        

        expr = expr_tuple[0]
        expr_type = expr_tuple[1]
 
        # for leaf, measured and external parameter, no need to expand
        list_type = [net_name_g2.leaf_para, net_name_g2.mesr_para, net_name_g2.xtnl_para]
        #if expr_type == net_name.leaf_para or expr_type == net_name.mesr_para or expr_type == net_name.xtnl_para or b_xpd == False:
        if expr_type in list_type or b_xpd == False:
            if hasattr(para_obj, 'soln_hldr'):
                para_soln_expr_name = para_obj.name
                return para_soln_expr_name
            return expr
            pass
        elif expr_type == net_name_g2.itmd_para:
            '''
            New code for solution method
            '''
            #print('xxxxxxxxxxxxxxxxxx')
            #exit()
            if hasattr(para_obj, 'soln_hldr'):
                para_soln_expr_name = para_obj.name+'_'+net_name_g2.soln_mthd[para_obj.soln_hldr]
                setattr(self, '_'+para_soln_expr_name, para_obj)
                obj = self.get_netelmt_g2(para_soln_expr_name)
                return para_soln_expr_name
            # expand the expression by calling embedded function self.get_expr()
            operand_list = self.walk_tree_g2(expr)
            
            # the operand_list contains at least expr itself 
            if operand_list == []:
                operand_list = [expr]

            list2 = []
            [list2.append(x) for x in operand_list if x not in list2]
            operand_list = list2

            # for each operand, get the expression
            for operand in operand_list:
                sub_expr = self.gen_expr_g2(obj_name, str(operand))    # str: expression should be in string
                                
                # if sub_expr is None, it means no need to expand the expression for this operand
                if sub_expr is not None:
                    # Take the original expression only, the expanded expression is not used
                    # replace the original operand with the new sub expression
                    expr = expr.replace(str(operand), sub_expr)

            return expr
                
    def walk_tree_g2(self, expr):    
        '''
        Walk through the tree of the expression, return all the operands contained in the expression
        
        expr: the string expression tree to walk through
        
        return: the list of all the operands
        '''
       
        # convert to symbolic domain
        expr = parse_expr(expr)
        
        # expand the symbolic expression
        expr = smp.expand(expr)

        list_operand = []   
        for arg in expr.args:
            list_operand.append(arg)                                # Record the current operand
            operands_in_child_expr = self.walk_tree_g2(str(arg))       # Record the operands in the current operands; str: convert back to string first
            list_operand = list_operand + operands_in_child_expr
           
        return list_operand  

    def record_aux_var_expr_g2(self, elmt_obj, model_name, dependent_name):
        '''
        Record the expression to the element
        elmt_obj - the object of the element for which the expression has to be recorded
        model_name- name of the model for which the corresponding auxil variable and expression will be obtained
        '''

        # Based on the model name, obtain the corresponding aux var and expr
        aux_var_mod_name = elmt_obj.aux_vars[model_name]
        aux_var = aux_var_mod_name[0]
        aux_expr_ori = aux_var_mod_name[1]
        aux_expr_expd = aux_var_mod_name[2]

        aux_expr_ori = '('+aux_var+'-'+'('+aux_expr_ori+')'+')'
        aux_expr_expd = '('+aux_var+'-'+'('+aux_expr_expd+')'+')'

        # Format the aux_var and aux_expr as expr = {'expr_xpd': aux_expr, 'expr_ori':aux_var} 
        expr_aux = {'expr_xpd': aux_expr_expd, 'expr_ori':aux_expr_ori}

        netcfg_g2.ntctl.record_expr_g2(expr_aux, dependent_name) 
        
    def add_cstr_g2(self, elmt_obj, para_val, para_name):
        '''
        func: Add a new constraint to the problem where LHS >= RHS
        elmt_obj: object of the element for which the constraint has to be added
        para_val: the bound for the value
        operator: '+' or '-' operator
        '''

        # Create the name for the variable
        expr1 = para_val+'_'+elmt_obj.name
        expr2 = para_name+'_'+elmt_obj.name

        dep_link_name = elmt_obj.__dict__['link_set'][0]

        cstr_expr = '('+expr1+'-'+expr2+')'
        
        expr_cstr = {'expr_xpd': cstr_expr, 'expr_ori':cstr_expr}
        
        #Record the expression
        netcfg_g2.ntctl.record_expr_g2(expr_cstr, dep_link_name) 
        
    def write_config_info(self, elmnt_name, key_name, key_value):
        h_file = open(net_name_g2.driver_plane_filename, 'a+')

        content = '%s["'"%s"'"]="'"%s"'"'%(elmnt_name, key_name, key_value) +'\n'
        h_file.write(content)
        h_file.close()
        
    def configure(self, elmnt_name, info_dict):
        '''
        Store the name of the dataset in the element object
        Then write the details to the driver_plane_filename
        '''
        for key in info_dict.keys():
            elmnt_obj = self.get_netelmt_g2(elmnt_name)
            setattr(elmnt_obj, key, info_dict[key])
            self.write_config_info(elmnt_name, key, info_dict[key])
        
    
        
        
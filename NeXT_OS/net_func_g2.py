#######################################################
# Author: Zhangyu Guan, Sabarish
# Project Manager: Zhangyu Guan
# functions and classes
#######################################################

# add external dir into search list
# Add search paths
import sys, os, inspect

sys.path.append("./wos-dir")
sys.path.append("./wos-ncp")
sys.path.append("./wos-network")
sys.path.append("../")
sys.path.append("../NeXT-PPS")
sys.path.append("../../")
sys.path.insert(0, './wos-network')
sys.path.insert(0, './wos-ncp')
sys.path.insert(0, './wos-dir')
sys.path.insert(0, '../NeXT-PPS')

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
### print the currrent and parent directory 2/27/2025 ###
# print(f"Current Directory: {current_dir}")
# print(f"Parent Directory: {parent_dir}")

sys.path.insert(0, parent_dir + '\OSW_G2_elmtlib\element_library')
sys.path.insert(0, './wos-decomp')

# from current folder
import net_name_g2


from sympy.parsing.sympy_parser import parse_expr
import sympy as smp
import types
# -------------------------------------------------------------------------
# network element operations
# -------------------------------------------------------------------------
       
def create_dependent_attr(attr_name):
    '''
    Create dependent attribute name
    This will be used to get attribute object
    :return: dependent attribute name
    '''
    return 'dependent_' + attr_name

def mkinfo_g2(elmt_type, elmt_subtype, elmt_num, addi_info):
    '''
    basic information to define a network element
    '''
    net_info = {'elmt_type': elmt_type, 'elmt_subtype': elmt_subtype, 'elmt_num': elmt_num, 'addi_info': addi_info}
    return net_info 
    
def mkinfo(elmt_type, elmt_subtype, elmt_num, addi_info):
    '''
    basic information to define a network element
    '''
    net_info = {'elmt_type': elmt_type, 'elmt_subtype': elmt_subtype, 'elmt_num': elmt_num, 'addi_info': addi_info}
    return net_info   


# mapping from attributes to network element
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))

# sys.path.insert(0, parent_dir+'\OSW_G2_elmtlib\attribute_library')
# sys.path.insert(0, parent_dir+'\OSW_G2_elmtlib\model_library\Expression_Model')
# sys.path.insert(0, parent_dir+'\OSW_G2_elmtlib\model_library\Script_Model')
sys.path.insert(0, os.path.join(parent_dir, "OSW_G2_elmtlib", "attribute_library"))
sys.path.insert(0, os.path.join(parent_dir, "OSW_G2_elmtlib", "model_library","Expression_Model"))
sys.path.insert(0, os.path.join(parent_dir, "OSW_G2_elmtlib", "model_library","Script_Model"))

import attribute_mapping

# -------------------------------------------------------------------------
# add attributes to network element 
# -------------------------------------------------------------------------
def add_attributes(obj_netelmt, key_netelmt):
    '''
    # Get element name from element mapping file; this will generate the variable for one_sess class
    '''
    list_of_elements_mapped = dir(elmt_mapping)
    for item in list_of_elements_mapped:
        if item.find(key_netelmt) is not -1:               #returns index of substring
            value = getattr(elmt_mapping,item)   
            module = __import__(value)

            class_handle = getattr(module,value)    #from class module (py file, here __ssrate__.py) get class definition 

            # First, get the additional information
            info_file_name = value + 'info__'       # get the name of the information file
            module = __import__(info_file_name)     # load the module 
            addi_info = getattr(module, 'addi_info')# get the additional informaiton
            
            # Second, add ntwk and parent information to addi_info
            addi_info['ntwk'] = obj_netelmt.ntwk
            addi_info['parent'] = obj_netelmt
            
            # Create the info dictionary
            info = mkinfo(addi_info['class_name']+'_'+obj_netelmt.name, addi_info['class_name'], 1, addi_info)             
            
            obj = class_handle(info)             #use class definition to creat object in this one_sess class 
            setattr(obj_netelmt, value, obj)            #use value as attribute to the object created

def add_attributes_g2(obj_netelmt, key_netelmt):
    '''
    # Get element name from element mapping file; this will generate the variable for one_sess class
    '''
    list_of_elements_mapped = dir(attribute_mapping)

    for item in list_of_elements_mapped:
        if item.find(key_netelmt) is not -1:               #returns index of substring
            value = getattr(attribute_mapping,item)   

            module = __import__(value)

            class_handle = getattr(module,value)    #from class module (py file, here __ssrate__.py) get class definition 

            # First, get the additional information
            info_file_name = value + 'info___'       # get the name of the information file
            module = __import__(info_file_name)     # load the module 
            addi_info = getattr(module, 'addi_info')# get the additional informaiton
            
            # Second, add ntwk and parent information to addi_info
            addi_info['ntwk'] = obj_netelmt.ntwk
            addi_info['parent'] = obj_netelmt

            # Create the info dictionary
            info = mkinfo(addi_info['class_name']+'_'+obj_netelmt.name, addi_info['class_name'], 1, addi_info)             

            obj = class_handle(info)             #use class definition to creat object in this one_sess class 
            setattr(obj_netelmt, value, obj)            #use value as attribute to the object created

            if hasattr(obj_netelmt, 'oper_freq'):
                setattr(obj, 'oper_freq', obj_netelmt.oper_freq)

            if hasattr(obj_netelmt.ntwk, 'attribute_list'):
                curr_attr_list = getattr(obj_netelmt.ntwk, 'attribute_list')
                new_attr_list = []
                for atr in curr_attr_list:
                    new_attr_list.append(atr)
                new_attr_list.append(obj.name)
                setattr(obj_netelmt.ntwk, 'attribute_list', new_attr_list)
            else:
                setattr(obj_netelmt.ntwk, 'attribute_list', [obj.name])

            list_name = obj.stype+'_list'

            if hasattr(obj_netelmt.ntwk, list_name):
                curr_attr_list = getattr(obj_netelmt.ntwk, list_name)
                new_attr_list = []
                for atr in curr_attr_list:
                    new_attr_list.append(atr)
                new_attr_list.append(obj.name)
                setattr(obj_netelmt.ntwk, list_name, new_attr_list)
            else:
                setattr(obj_netelmt.ntwk, list_name, [obj.name])

# -------------------------------------------------------------------------
# network an expression
# -------------------------------------------------------------------------    
def mkexpr(fmlr, *args):
    '''
    fmlr: math expression
    varlst: variable list used in fmlr
    '''
    if len(args) == 0:                # no variable
        varlst = None
    else:
        varlst = args
            
    return {'fmlr':fmlr, 'varlst':varlst}    
    

def mkvarname(var_expr):
    '''
    new function to replace the old mkvarname()
    make up a variable name based on the variable expression
    '''     
    return var_expr    
    


# -------------------------------------------------------------------------
# basic network element class 
# base class of all other element classes
# -------------------------------------------------------------------------
class netelmt_g2:
    def __init__(self, info):
        self.type       = info['elmt_type']                       # network element type: network, node, session, parameter (variable) ...
        self.name       = self.type
        self.stype      = info['elmt_subtype']                    # subtype: Parameter: power, frequency, rate ...
        self.para_type  = None                                    # leaf element, intermediate element, external element
        self.is_var     = None                                    # is this element an optimization variable?  
        self.layer      = None                                    # protocol layer 
        self.hid        = None                                    # horizontal identification for distributed decomposition

        # pointer to network, parent, and itself
        self.ntwk       = info['addi_info']['ntwk']                 # to network
        if self.ntwk == None:                                       # when creating a network, None 
            self.ntwk = self 

        self.parent     = info['addi_info']['parent']               # to parent
                          
        if 'layer' in info['addi_info'].keys():
            self.layer = info['addi_info']['layer']      

        if 'hid' in info['addi_info'].keys():
            self.hid = info['addi_info']['hid']   

        if 'para_type' in info['addi_info'].keys():
            self.para_type = info['addi_info']['para_type'] 

        # register the element according to addi_info
        if net_name_g2.if_rgst in info['addi_info'].keys():
            if info['addi_info'][net_name_g2.if_rgst] == net_name_g2.no:  # no need to register
                b_rgst = 0
            else:
                b_rgst = 1
        else:             
            b_rgst = 1
                      
        if b_rgst == 1:                                             # need to register, or not specified    
            ptr_name = '_'+self.type                                # to itself; pointer name format: node: _node
            if hasattr(self.ntwk, ptr_name):
                print('Error: Duplicated network element!')           
                exit(0)
            else:
                setattr(self.ntwk, ptr_name, self)
        else:
            pass
          
    def ping(self):
        '''
        display information
        '''              
        print(self.__dict__.keys())
        for attr in self.__dict__.keys():
            print(attr, ':', getattr(self, attr))
                
    def get_ntwk(self):
        '''
        return the network object
        '''         
        return self.ntwk

    def get_netelmt_g2(self, elmt_name):
        '''
        return the network object
        '''   
       
        # get network
        ntwk = self.get_ntwk()
         
        # get network element
        # construct network attribute corresponding to elmt_name
        _elmt_name = '_'+elmt_name
        
        if hasattr(ntwk, _elmt_name) == False:      
            # the requested network element doesn't exist
            # if the wanted element does not exist, notify the network
            # will be implemented in future
            
            return None
        else:
            return getattr(ntwk, _elmt_name)
       
    def get_hid_g2(self):
        '''
        func
        - this function get_hid is only for parameters, like session rate, link capacity
        - get the horizontal node id (hid) for distributed decomposition
        - not all networ elements have hid attribute, only network parameters have, like power, rate
        - the hid type is stored in the object itself, but the hid name is stored in its parent object
        - for parametes, the self.hid is the type of the hid
        - for network element, the hid is the controlling element; e.g., the hid of a session is its
          source node
        - currently hid is not defined in this basic class, it is in each specific class
        
        return
        - the hid; none if no hid is found
        '''
        
        # check if the object has hid
        if hasattr(self, net_name_g2.hid):       
            # get the hid type
            hid_type = getattr(self, net_name_g2.hid)      
            # find the name of the hid in the parent network element
            hid_name = getattr(self.parent, hid_type)
        else:
            hid_name =  None                 # no hid found, return None
            
        return hid_name
        
    def get_para_expr_g2(self, b_xpd = True):
        '''
        func
        -- get the mathematical expression of a parameter, e.g., lkcap, lkpwr
        
        return
        -- the mathematical expression in string
        
        4.25.2020: Add b_xpd to indicate if expanded or the original expression will be returned
        b_xpd = True: return the expanded expression
        b_xpd = False: return the original expression, which is the name of the parameter
        '''
        
        # supported parameter types
        type1 = [net_name_g2.leaf_para, net_name_g2.mesr_para, net_name_g2.xtnl_para]
        type2 = [net_name_g2.itmd_para]
        type_supported = type1 + type2

        if b_xpd == False:
            return (self.name, self.para_type)
        
        # if the parameter is leaf parameter or to be measured, use its name as expression
        if self.para_type in type1:
            expr = self.name
            
        # for intermediate parameter, expand the expression
        if self.para_type in type2:
            # get the module name which stores the expression
 
            mod_name = self.get_expr_module_name_g2(self.expr_hldr)

            # load the module 
            module = __import__(mod_name) 

            ## check if the module has the mod_name attribute
            ## if yes, get the expr value stored in the attribute directly
            ## if not, prepare the function name to be called and pass the parent object to obtain the expr
            if hasattr(module, mod_name):
                # get the expression from the module
                expr = getattr(module, mod_name)    # attribute has the same name as the module

                expr_script = expr
                if not type(expr) is str:
                    expr_script = expr(self.parent, self.model_parameter)
                    expr = expr_script
                    
        # for other cases, not supported for now
        if self.para_type not in type_supported:
            print('Error: Network parameter type', self.name, ':', self.para_type, 'is not supported for now.')
            exit(0)
        return (expr, self.para_type)
        
    def get_para_g2(self, para):
        '''
        Get independent parameter name through net func for net element
        Example: Net element: "link" will return link + name
        '''
        para_name = para+'_'+self.name
        para_obj = self.get_netelmt_g2(para_name)
        return para_obj
        
    def get_func_name(self):
        '''
        Prepare the function name to be called to obtain the expression
        '''
        function_name = self.stype+'_'+'model'+'_'+self.expr_hldr
        
        return function_name
        
    def get_func_name_g2(self):
        '''
        Prepare the function name to be called to obtain the expression
        '''
        function_name = '__'+self.stype+'__'+self.expr_hldr+'__'

        return function_name
    
    def get_expr_module_name_g2(self, expr_hldr):
        '''
        func
        -- get the module name which stores the expression
        
        args
        -- expr_type: the model of the expression
        
        return
        -- module name in string
        '''

        if expr_hldr!='script__def':
            mod_name = '__'+expr_hldr+'__'
        else:
            mod_name = '__'+self.stype+'__'+self.oper_freq+'__'+self.expr_hldr+'__'

        return mod_name
        
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

    def set_para_value(self, para_val):
        '''
        Sabarish
        func: Set the value of the parameter
        para_val: The value of the parameter
        return: nothing
        where the func is called: called in net_ntwk - set_para_value()
        
        How to use this default value?
        
        The default value should be initialized to "NAN"
        '''

        if hasattr(self,net_name.default_val):
            self.default_val = para_val
        else:
            setattr(self, net_name.default_val, para_val)

    def attach(self, elmnt_name, idx, addi_info=None):
        '''
        func: Attach the specified element to the network
        elmt_name: Name of the network element to be added to the network
        '''

        elmnt_obj = self.ntwk.get_netelmt_g2(elmnt_name)

        list_name = elmnt_obj.type+'_list'

        if not hasattr(self,list_name):
            setattr(self, list_name, [])
            
        if not hasattr(self.ntwk,list_name):
            setattr(self.ntwk, list_name, [])   
        
        # Construct local name to be stored at the element level
        elmt_name_local = self.ntwk.cnst_local_name(elmnt_name, idx) 
        
        # Construct global name to be stored at the network level
        elmt_name_global = self.ntwk.cnst_global_name(elmnt_name) 
        
        # Prepare the info and call the corresponding class to get the element object
        elmt_num  = 1    
        info = {'ntwk':self.ntwk, 'parent':getattr(self.ntwk, elmnt_name)}
        info = mkinfo_g2(elmt_name_global, getattr(net_name_g2, elmnt_name), elmt_num, info)  
        
        if addi_info != None:
            info['addi_info'].update(addi_info)
            
        elmt_module = __import__(elmnt_name)
        class_to_call = getattr(elmt_module, elmnt_name)

        elmnt_obj = class_to_call(info)

        setattr(elmnt_obj, 'index', idx)
        setattr(self.ntwk, elmt_name_global, elmnt_obj)

        # Update the list of elements in network element 
        list_elmnt_global = getattr(self.ntwk, list_name)
        if elmt_name_global not in list_elmnt_global:
            list_elmnt_global.append(elmt_name_global)
            setattr(self.ntwk, list_name, list_elmnt_global)

        # Add the attributes corresponding to the network element
        add_attributes_g2(elmnt_obj, elmnt_obj.type)

        return elmt_name_global#, list_elmnt_global
        
    def add_one_link(self, tx_node, rx_node):
        print('Adding link between node', tx_node, 'and', rx_node)
        
        elmnt_name = 'link'
        list_name = elmnt_name+'_list'
        
        if not hasattr(self.ntwk,list_name):
            setattr(self.ntwk, list_name, [])
            
        link_name = self.ntwk.construct_link_name(tx_node, rx_node) 

        # Prepare the info and call the corresponding class to get the element object
        elmt_num  = 1    
        addi_info = {'ntwk':self.ntwk, 'parent':getattr(self, elmnt_name)}
        info = mkinfo_g2(link_name, None, elmt_num, addi_info)     
        elmt_module = __import__(elmnt_name)
        class_to_call = getattr(elmt_module, elmnt_name)
        
        elmnt_obj = class_to_call(info)

        # Update the links using the tx node
        node_obj = self.ntwk.get_netelmt_g2('g_node'+str(tx_node))  

        if not hasattr(node_obj,'links'):
            setattr(node_obj, 'links', [])
        list_lk = getattr(node_obj, 'links') 
        list_lk.append(link_name)

        setattr(node_obj, 'links', list_lk) # Set node object with the link name
        setattr(elmnt_obj, 'tx_node', 'node'+str(tx_node)) # Set the tx node attribute for link object  
        setattr(elmnt_obj, 'rx_node', 'node'+str(rx_node)) # Set the rx node attribute for link object 
        setattr(self.ntwk, link_name, elmnt_obj) 
        list_elmnt = getattr(self, list_name) 
        list_elmnt.append(link_name)
        setattr(self, list_name, list_elmnt)

# add external dir into search list
import sys, os, inspect

sys.path.append("../")
sys.path.append("../wos-dir/")
sys.path.append("../wos-ncp/")
sys.path.append("../../")
sys.path.append("../../NeXT-PPS")
sys.path.append("../../../")

sys.path.insert(0, './wos-decomp')
sys.path.insert(0, '../wos-ncp')
sys.path.insert(0, '../wos-dir')
sys.path.insert(0, '../../NeXT-PPS')

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))

sys.path.insert(0, parent_dir + '\OSW_G2_elmtlib\element_library')

# from current folder
import net_name_g2

from sympy.parsing.sympy_parser import parse_expr
import sympy as smp

        
def create_dependent_attr(attr_name):
    '''
    Create dependent attribute name
    This will be used to get attribute object
    :return: dependent attribute name
    '''
    return 'dependent_' + attr_name

def mkinfo(elmt_type, elmt_subtype, elmt_num, addi_info):
    '''
    basic information to define a network element
    '''
    net_info = {'elmt_type': elmt_type, 'elmt_subtype': elmt_subtype, 'elmt_num': elmt_num, 'addi_info': addi_info}
    return net_info   


# mapping from attributes to network element
import elmt_mapping

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
class netelmt_group:
    def __init__(self, info):
        self.type       = info['elmt_type']                       # network element type: network, node, session, parameter (variable) ...
        self.name       = self.type
        self.stype      = info['elmt_subtype']                    # subtype: Parameter: power, frequency, rate ...
        self.member     = []                                      # members list in the current group
        self.subgroup   = []                                      # elements are grouped into different groups; e.g., node: source, destination, relay
        self.para_type  = None                                    # leaf element, intermediate element, external element
        self.is_var     = None                                    # is this element an optimization variable?  
        self.layer      = None                                    # protocol layer 
       
        # if elmtobj is None, the network element is self
        # otherwise, if not None, self is just a wrapper with elmtobj referring to the actual element
        # this attribute is added later, in order to include more types of network elements
        self.elmtobj    = None
        
        # for some elements implemented earlier, this parameters is not passed
        if 'elmtobj' in info['addi_info'].keys():
            self.elmtobj = info['addi_info']['elmtobj']        
            

        # for back compatibility
        # rngtype means if the element is single, subset, or full set
        self.rngtype    = None

        # for some elements implemented earlier, this parameters is not passed        
        if 'rngtype' in info['addi_info'].keys():
            self.rngtype = info['addi_info']['rngtype']          
            
        # add members of current type
        self.addmember(info['elmt_num'])


        # pointer to network, parent, and itself
        self.ntwk       = info['addi_info']['ntwk']                 # to network
        if self.ntwk == None:                                       # when creating a network, None 
            self.ntwk = self 

        self.parent     = info['addi_info']['parent']               # to parent

        # register the element according to addi_info
        if net_name.if_rgst in info['addi_info'].keys():
            if info['addi_info'][net_name.if_rgst] == net_name.no:  # no need to register
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
            
        self.varcnt = 0                                             # recording the number of variables this parameter has been made as
        
        # changes:
        # add layer to indicate which layer the network element belongs to
        # hid added to indicate if the element corresponds to a horizontal network element, like src, node
        if 'layer' in info['addi_info'].keys():
            self.layer = info['addi_info']['layer']      

        if 'hid' in info['addi_info'].keys():
            self.hid = info['addi_info']['hid']   

        # changes:
        # add 'para_type' to indicate type of the elements
        if 'para_type' in info['addi_info'].keys():
            self.para_type = info['addi_info']['para_type']
        
        # changes
        # add is_var to indicate if a network element 
        if 'is_var' in info['addi_info'].keys():
            self.is_var = info['addi_info']['is_var']  

        # Add sub_type to indicate the category of a network variable, e.g., the subtype of "lnkpwr" is "power"
        # This information will be used to configure the lower and upper bounds of a variable
        if 'sub_type' in info['addi_info'].keys():
            self.sub_type = info['addi_info']['sub_type']        

        # Add an attribute for external parameter to record derivative of the parameter with respect to external variables
        # Used in alglib_func.gnrt_pnl() to generate penalization when generating solution algorithms
        # Initialized to an empty dictionary, updated in self.add_xtnl_der()
        if 'para_type' in info['addi_info'].keys() and info['addi_info']['para_type'] == net_name.xtnl_para:
            self.der = {}                 
    
    def add_xtnl_der(self, var_name, der_expr):    
        '''
        Add a derivative for external parameters
        
        var_name: variable name with respective to which the derivative is defined
        der_expr: derivative expression
        
        Return: -1 if error, 1 if new entry added
        
        Called By: net_link.net_link.new_lkitf()                
        '''
        
        # This element must have attribute para_type with value net_name.xtnl_para
        if hasattr(self, 'para_type') and self.para_type == net_name.xtnl_para:
            self.der.update({var_name: der_expr})
        else:
            print('Error: This element doesn\'t have attribute para_type or is not external, -1 returned!')
            return -1                                                                    
        
    
            
    def ping(self):
        '''
        display information
        '''       
        print('Elmt: {}, members: {}'.format(self.type, self.member))
        print('Sub-elmt: {}'.format(self.subgroup))
        for subgrp in self.subgroup:           
            if subgrp == net_name.default:                          # skip the default dumb subgroup
                pass
            else:
                print(subgrp)
                x = getattr(self, subgrp)
                print('{}, members: {}'.format(x.type, x.member))
  
        print('layer:', self.layer)
        print('is_var:', self.is_var)      
         
        print(self.__dict__.keys())
        for attr in self.__dict__.keys():
            print(attr, ':', getattr(self, attr))
                
    def hasgroup(self, groupname):
        '''
        check if an element has a group 
        '''
        return hasattr(self, groupname)


    def addgroup(self, groupname, groupvalue):
        '''
        add a new group to an element
        '''
        if self.hasgroup(groupname):
            print('Error: group {} already exists.'.format(groupname))
            exit(0)
        elif groupname == net_name.default:
            self.subgroup.append(groupname)              # add default group (just name, a dumb group)
        else:
            setattr(self, groupname, groupvalue)         # create new subgroup
            self.subgroup.append(groupname)              # add subgroup name to the group list

    def addmember(self, mem_num):
        '''
        add new members to current group
        '''       
        self.member = range(len(self.member) + mem_num)    
           
    def delmember(self, mem_num):
        '''
        delete members from current group
        '''                   
        self.member = range(len(self.member) - mem_num)
        print('{}, members: {}'.format(self.type, self.member))

    def get_memnum(self):
        '''
        the number of members
        '''  
        return len(self.member)
        
    def set_memnum(self, mem_num):
        '''
        set the number of membes in this group
        '''        
        if mem_num < 0:
            print('Error: The number of members must be >= 0! ')
            Exit(0)
        else:
            self.member = range(mem_num)        

    def get_ntwk(self):
        '''
        return the network object
        '''         
        return self.ntwk

    def get_netelmt(self, elmt_name):
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

    def get_depth(self):
        '''
        get the depth information of the current element in the network tree
        '''
        depth = 0                           # initialized to 03/12/2016
        elmt = self         
        while elmt.parent != None:          # not the top element
            depth += 1 
            elmt = elmt.parent
            
        return depth        
        
    def mkvar(self, var_expr, *args):
        '''
        make a (or a set) network parameters variables
        #) var_expr: the expression of the variable
        #) args: a list of parameters indicating the range of ntwk elements
        
        Changes(5/28/2016):
        This function will be discarded. Instead, variables will be created by calling ntwk.make_var() directly
        '''             
        # only enabled for leaf parameters 
        if len(self.subgroup) != 0:
            print('Error: Only leaf parameters can be made variables!')
            exit(0)
        
        # check if the number of parameters are correct
        elmt_depth = self.get_depth()                                       # depth of the network element
        num_arg = len(args)                                                 # number of parameters
        if elmt_depth != num_arg:                                           # the two should equal to each other
            print('Error: The number of argments should equal to elment depth!')

        # count up the variables this parameter has been made as
        self.varcnt += 1
        
        # create variable by calling mkvar of the network
        newvar = self.ntwk.mkvar(self, var_expr, *args)

    def newfam_xxx(self, dict_info):
        '''
        create a family for a network element
        '''
        return dcp_set.newfam(dict_info)

    def get_fulfamset_xxx(self):                                                        # _xxx: discarded function
        '''
        get the full familiy set
        '''
        # for a parameter (or variable), get the full set of its elmt_asct
        # for network element, get the full set of itself        
        if hasattr(self, net_name.elmt_asct): 
            return self.elmt_asct.get_fulfamset()                                       # the parameter is associated to other network element
        else:                                                                           # otherwise
            # if full list does not exist, create one
            if self.fam.full_list == None:                              
                lst = list(range(dcp_name.allnum))                                      # generate the full list, here allnum is the size of the full set
                self.fam.full_list = dcp_set.subset(lst)
                
            # return the full list    
            return self.fam.full_list
                       
    def create_every_xxx(self):
        '''
        create an EVERY subset and add the corresponding attribute in this element
        return the object of EVERY set
        '''
        return dcp_set.create_every(self)
        
    def is_leaf(self):
        '''
        func: determine if a network element is a leaf element by checking if the element has attribute 'expr_hldr'
        return: True for leaf or False non-leaf
        '''        
        if hasattr(self, net_name.expr_hldr):
            obj_expr_hldr = getattr(self, net_name.expr_hldr)
            if obj_expr_hldr == None:
                return True                             # is leaf
            else:
                return False                            # not leaf
        else:
            return True                                 # is leaf
            
    def is_xtnl(self):
        '''
        func: determine if the element is external element
        return: True or False        
        '''
        if self.para_type == net_name.xtnl_para:
            return True
        else:
            return False
            
    def get_para(self, para):
        '''
        Get independent parameter name through net func for net element
        Example: Net element: "link" will return link + name
        '''
        para_name = para+'_'+self.name
        para_obj = self.get_netelmt(para_name)
        
        return para_obj

    def get_dependent_para(self, para_name, dependent_netelmt):
        '''
        Get dependent parameter through net func for net element
        Example: Net Element "link" + dependent netelmt, Dependent_var = session_rate; return links, associated session name, session rate
        Return para obj + list of dependent var
        '''
        para_obj = self.get_netelmt(para_name)

        attr_name = 'dependent_' + dependent_netelmt
        
        dependent_para = getattr(para_obj, attr_name)
        
        return dependent_para

        
    def connect_to_dependent(self, dependent_name):
        '''
        Connect dependent variable to independent variable
        Example: This can connect link to all sessions associated with a link
        '''
        dependent_obj = self.get_netelmt(dependent_name)

        #Using subtype in elmt info
        dependent_attr = create_dependent_attr(dependent_obj.stype)
                
        if hasattr(self, dependent_attr):
            attr_obj = getattr(self, dependent_attr)
        else:
            setattr(self, dependent_attr, [])
            attr_obj = getattr(self, dependent_attr)
            
        attr_obj.append(dependent_name)
        
    def get_hid(self):
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
        if hasattr(self, net_name.hid):       
            # get the hid type
            hid_type = getattr(self, net_name.hid)      

            # find the name of the hid in the parent network element
            hid_name = getattr(self.parent, hid_type)  

        else:
            hid_name =  None                 # no hid found, return None
            
        return hid_name
        
    def get_para_expr(self, b_xpd = True):
        '''
        func
        -- get the mathematica expression of a parameter, e.g., lkcap, lkpwr
        
        return
        -- the mathematical expression in string
        
        b_xpd = True: return the expanded expression
        b_xpd = False: return the original expression, which is the name of the parameter
        '''
        
        # supported parameter types
        type1 = [net_name.leaf_para, net_name.mesr_para, net_name.xtnl_para]
        type2 = [net_name.itmd_para]
        type_supported = type1 + type2

        if b_xpd == False:
            return (self.name, self.para_type)
        
        # if the parameter is leaf parameter or to be measured, use its name as expression
        if self.para_type in type1:
            expr = self.name
            
        # for intermediate parameter, expand the expression
        if self.para_type in type2:
            # get the module name which stores the expression

            mod_name = self.get_expr_module_name(self.expr_hldr)

            # load the module 
            module = __import__(mod_name) 
            #print('G', module)
            
            ## check if the module has the mod_name attribute
            ## if yes, get the expr value stored in the attribute directly
            ## if not, prepare the function name to be called and pass the parent object to obtain the expr
            if hasattr(module, mod_name):
                # get the expression from the module
                expr = getattr(module, mod_name)    # attribute has the same name as the module
            else:

                ## Get the function name that should be called to get the expression
                func_name = self.get_func_name()

                ## Based on the function name, obtain the expression
                func_handle = getattr(module,func_name)

                expr = func_handle(self)

            
        # for other cases, not supported for now
        if self.para_type not in type_supported:
            print('Error: Network parameter type', self.name, ':', self.para_type, 'is not supported for now.')
            exit(0)
        
        return (expr, self.para_type)
        
    def get_func_name(self):
        '''
        Prepare the function name to be called to obtain the expression
        '''
        function_name = self.stype+'_'+'model'+'_'+self.expr_hldr
        
        return function_name
    
    def get_expr_module_name(self, expr_type):
        '''
        func
        -- get the module name which stores the expression
        
        args
        -- expr_type: the model of the expression
        
        return
        -- module name in string
        '''
        
        # module name is defined as: "class of parent element"_"expr_type"

        mod_name = self.stype + '_' + expr_type
        
        return mod_name
        
    def walk_tree(self, expr):    
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
            operands_in_child_expr = self.walk_tree(str(arg))       # Record the operands in the current operands; str: convert back to string first
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

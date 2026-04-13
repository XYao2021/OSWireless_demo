#######################################################
# Date: 03/19/2016
# Author: Zhangyu Guan
# Project Manager: Tommaso Melodia, Zhangyu Guan
# decomposition functions
#######################################################

import sys
sys.path.insert(0, './wos-network')

# from external folder
import net_name, net_func

# from local folder
import dcp_name

class inst(net_func.netelmt_group):
    '''
    definition of instance
    '''
    def __init__(self, info):  
        # from base network element
        net_func.netelmt_group.__init__(self, info)   
              
        self.obj_every = info['addi_info']['every']                 # every object
        self.obj_nonevery = info['addi_info']['nonevery']           # nonevery object
        
        self.lst_varstr = self.ps_varstr()                          # list of variable names
        
        self.obj_expr = None                                        # expression for which the instance has been generated

    def set_expr(self, obj_expr):
        '''
        configure the expression to which the instance is associated
        '''
        self.obj_expr = obj_expr
        
    def get_expr(self):
        '''
        get the expression associated to this instance
        return the expression in string
        '''
        return self.obj_expr.expr
        
    def disp_varinst(self):
        '''
        get the instance variable
        '''
        # get the list of variables
        varlst = self.get_varlst() 

        # get information of all variables
        for var in varlst:              
            str_varinst = self.get_instvar(var)
            #print(str_varinst)
                    
    def get_varlst(self):
        '''
        get the list of the variables related to this instance
        '''
        return self.obj_expr.varlst
        
    def get_instvar(self, str_var):
        '''
        func: get the instance set of a variable
        return: the list of variable instance
        '''
        # get the element name for the variable
        obj_var = self.get_netelmt(str_var)         # varible object
        elmt_asct_name = obj_var.elmt_asct[-1]      # name of associated element; the last one in the element list  
        para_name = obj_var.getpara()               # parameter name of the variable
        
        lst_inst = None                              
        # check EVERY 
        inst_elmt_name = self.obj_every.lst_mb[0]   # get the name of the every element
        if elmt_asct_name in inst_elmt_name:        # if the two names match each other
            lst_inst = self.obj_every.lst_mb
            
            # changes:
            # added for consitent information retrieve
            obj_instset = self.obj_every
        else:        
            # check NONEVERY
            for instset_name in self.obj_nonevery.lst_mb:                      # check all NONEVERY subsets
                obj_instset = self.get_netelmt(instset_name)                   # get the object of the instance set
                inst_elmt_name = obj_instset.lst_mb[0]                         # take any member element, say the frist one
                
                # changes: var_key has been added for easy information retreive
                #if elmt_asct_name in inst_elmt_name:                          # if the two names match each other
                if elmt_asct_name == obj_instset.var_key:
                    lst_inst = obj_instset.lst_mb
                    break
        
        # did not find the matched element?
        if lst_inst == None:
            print('Error: No matched instance element found!')
         
        # changes: 
        # var_key and var_id have been added for easy information retrieve
        # a new method to construct new_str
        #
        # # convert the list of instance elements to a string
        # str_lst_inst = str(lst_inst)
        
        # # replace the element name with the parameter name (i.e., the variable name)
        # new_str = str_lst_inst.replace(elmt_asct_name, para_name)
        # #print(elmt_asct_name, para_name)
        #print(obj_instset.var_idx)
        
        # changes: add .zfill(dcp_name.zflen) for fixed length index
        new_str = ['__' + para_name + '___' + str(id).zfill(dcp_name.zflen) for id in obj_instset.var_idx]                
        
        
        return new_str
        
    def ps_varstr(self):
        '''
        pass list of variables based on the every and nonevery objects 
        '''
        return None
    
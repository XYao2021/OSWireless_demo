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

# from local directory
import net_name_g2, net_func

def new_exprdb(ntwk):
    '''
    create a database of expressions
    '''
    #---------------------------------------------------------------      
    elmt_name = net_name.expr_db                                        # element info
    elmt_num = 1     
    
    addi_info = {'ntwk':ntwk, 'parent':ntwk}
    info = net_func.mkinfo(elmt_name, None, elmt_num, addi_info)        

    elmt = net_exprdb(info)                                             # create element
    ntwk.addgroup(elmt_name, elmt)                                      # add element as a subgroup 
        
    x = getattr(ntwk, elmt_name)
    
    return x

def get_exprdb(ntwk):
    '''
    return the expression database
    if it hasn't been created, create one for the network
    
    ntwk: for which the expression database is returned or created
    '''
    
    # if expression database has been created, create one
    if ntwk.hasgroup(net_name.expr_db) == False:
        exprdb = new_exprdb(ntwk)
    else:
        exprdb = ntwk.get_netelmt(net_name.expr_db)   
        
    return exprdb

class net_exprdb(net_func.netelmt_group):
    '''
    data base of expressions
    '''
    def __init__(self, info):
 
        # from base network element
        net_func.netelmt_group.__init__(self, info) 
        
        # number of expressions, initialized to 0
        self.max_exprcnt = net_name.max_exprcnt                        # the predefined maximum number of variable index
        self.expr_cnt = 0

    def set_utility(self, expression, *args):
        '''
        set utility
        '''
        # if network utility has been created, update it
        if self.hasgroup(net_name.utility):
            x = self.get_netelmt(net_name.utility)
            
        # otherwise, create new utility
        else:
            #---------------------------------------------------------------      
            elmt_name = net_name.utility                                        # element info
            elmt_num = 1     
            
            addi_info = {'ntwk':self.ntwk, 'parent':self, 'expr': expression, 'expr_name': elmt_name}
            info = net_func.mkinfo(elmt_name, None, elmt_num, addi_info)        

            elmt = net_expr_hldr(info)                                          # create element
            self.addgroup(elmt_name, elmt)                                      # add element as a subgroup 
                
            x = getattr(self, elmt_name)
     
    def add_cstr(self, expression, *args):
        '''
        add constraint expression
        '''
        
        # first, generate a unique name for the constraint
        cstr_name = self.mk_exprname()
        
        
        # create a new expression
        #---------------------------------------------------------------      
        elmt_name = cstr_name                                                  # element info
        elmt_num = 1     
            
        addi_info = {'ntwk':self.ntwk, 'parent':self, 'expr': expression, 'expr_name': elmt_name}
        info = net_func.mkinfo(elmt_name, None, elmt_num, addi_info)        

        elmt = net_expr_hldr(info)                                             # create element
        self.addgroup(elmt_name, elmt)                                         # add element as a subgroup 
                
        x = getattr(self, elmt_name)

    def mk_exprname(self):
        '''
        generate a unique name for constraint expression
        '''
        
        # count up by 1 
        self.expr_cnt += 1
        
        # if maximum number reached?
        if self.expr_cnt > self.max_exprcnt:
            print('Error: Expression index ({}) has reached the maximum ({})!'.format(self.expr_cnt, maxcnt))
            exit(0)
              
        return mkcstrname(self.expr_cnt)  
        
class net_expr_hldr(net_func.netelmt_group):
    '''
    network expressions: utility, constraints
    '''
    def __init__(self, info):
 
        # from base network element
        net_func.netelmt_group.__init__(self, info)     
        
        # record the expression name for future use
        # only for utility and constraints
        # not for expression of intermediate parameters (e.g., SINR)
        if 'expr_name' in info['addi_info'].keys():
            self.expr_name = info['addi_info']['expr_name']
        
        # initialize expression
        self.expr = info['addi_info']['expr']['fmlr']       # formular 
        self.varlst = info['addi_info']['expr']['varlst']   # variable list used in this expression, initialized to be empty

        # following attributes will be updated when decomposing the NUM problem
        # record how many specific instances have been generated for this utility (must be one) and constraint (can be multiple)
        self.exprinst_cnt = 0                               # how many instances? initialized to 0        
        # different instances will be inserted upon running
        
        # instance generator
        self.gn = None
                
    def set_gn(self, obj_gn):
        '''
        configure the generator for the expression
        '''
        self.gn = obj_gn
        
    def dtm_every_elmt(self, gn):
        '''
        determine the instance set of element with EVERY range
        set the resulting set object as the EVERY element in generator gn
        '''       
        # the associated elements and corresponding range of all variables
        elmt_asct = []                                  # initialized to empty
        elmt_asct_rng = []
        for str_var in self.varlst:                     # name of each single variable
            obj_var = self.get_netelmt(str_var)         # get the object
            elmt_asct += obj_var.elmt_asct              # retrieve the elmt and range         
            elmt_asct_rng += obj_var.elmt_asct_rng       

        # get the name of every element, ntwk as default if no every element
        if net_name.every not in elmt_asct_rng:                             # every does not exist  
            elmt_every_name = net_name.ntwk                  
        else:
            elmt_every_idx = elmt_asct_rng.index(net_name.every)            # index of every element
            elmt_every_name = elmt_asct[elmt_every_idx]                     # every element name
   
        # create the every object
        obj_elmt = self.get_netelmt(elmt_every_name)                        # get the network element object
        obj_every = dcp_set.create_every(obj_elmt)                          # create an every instance set for the element
        
        # set obj_every in expression instance generator gn (defined in dcp_gn.py)
        gn.set_every_elmt(obj_every)
        
    def add_exprinst(self, lst_inst):
        '''
        add an instant for an expression (utlity or constraint)
        '''
        # instance count up 1
        self.exprinst_cnt += 1
        
        # construct a name for the instance
        instname = self.get_instname(self.exprinst_cnt)
        
        # add the instance
        setattr(self, instname, None)             # add a new attribute
        x = getattr(self, instname)               # get the attribute        
        x = lst_inst

    def get_instname(self, int_instid):
        '''
        construct a name for a instance
        '''
        return self.expr_name + '#' + str(int_instid)
                      
    def get_expr(self):
        '''
        get the expression
        '''
        return {'fmlr': self.expr, 'varlst': self.varlst}
        
    def set_expr(self, new_expr):
        '''
        set the expression
        '''
        self.expr = new_expr['fmlr']
        self.varlst = new_expr['varlst']

        return {'fmlr': self.expr, 'varlst': self.varlst}    
        
    def ping(self):
        '''
        display information
        '''
        # from base class
        net_func.netelmt_group.ping(self)

def disp_expr(ntwk, dict_expr):
    '''
    display informaiton of a formula
    ntwk: network object
    dict_expr: {fmlr, varlst}
    '''    
    
    # extract formular and variable list
    fmlr = dict_expr[net_name.fmlr]
    varlst = dict_expr[net_name.varlst]

    # extract the information of each variable in the variable list
    varinfo = ''
    for x in varlst:
        varobj = ntwk.get_netelmt(x)
        varinfo = varinfo + ', ' + varobj.getvarinfo()
           
    print('  ', fmlr, varinfo)

    
def mkcstrname(int_id):
    '''
    consruct a constraint name
    '''
    str_id = str(int_id)
    return net_name.constraint + '_' + str_id.zfill(len(str(net_name.max_exprcnt)))      # example: constraint_001      
    
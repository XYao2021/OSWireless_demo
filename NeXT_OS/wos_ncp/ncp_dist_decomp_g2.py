# Decompose a centralized singler-layer network control problem (vdcp) into multiple
# single-layer distributed network control problem


# symbolic computing library
from sympy.parsing.sympy_parser import parse_expr
import sympy as smp

# general functions for problem decomposition
import ncp_g2, ncp_name_g2, net_name_g2
        
class ncp_dist_decomp_g2(ncp_g2.ncp_func_g2):
    '''
    Class of the horizontally decomposed network control problem
    ncp_func: inherit those common functions for symbolic expression analysis
    '''
    
    def __init__(self, vdcp_obj):  
        '''
        vdcp_obj: the vertical decomposed network control for further horizontal decomposition
        '''
        
        # save network object for future user
        self.ncp  = vdcp_obj.ncp
        self.ntwk = vdcp_obj.ntwk
        self.vncp = vdcp_obj
        
        # get the list of single-layer network  control problem
        self.list_layer_prob = self.vncp.list_subprob

        # the list of generated distributed subproblems
        # record the name of the problem only
        # the corresponding objects will be created dynamically during decomposition
        # use self.get_subprob(name) to get the object
        self.list_dist_prob = []    
        
        # mapping between hid and subproblem
        self.hid_prob_mapping = {}
        
        # horizontally decompose each single-layer subproblem
        for prob in self.list_layer_prob:  
            self.dist_decomp_one_prob_g2(prob)  

    def dist_decomp_one_prob_g2(self, prob_layer):
        '''
        Func: Horizontally decompose a subproblem
        
        Input:
        prob: the problem to be decomposed
        
        Output:
        The generated distributed subproblems will be logged in this class
        '''
        
        # get the subproblem
        subprob = self.vncp.get_subprob_g2(prob_layer)
        # print("Sub-problems expression:", subprob)

        # get component expressions
        comp_expr = self.gen_component_g2(str(subprob))       # gen_component accepts only string expression
        # print("Components expression:", comp_expr,"\n")

        # loop over all component expressions
        for expr in comp_expr:
            # for each component expression, determine the horizontal node id
            hid = self.det_hid_g2(expr)

            '''
            ### Replaced with the implementation 3.27.2020 
            # if no hid found, do not know how to decompose this problem, raise and error
            if len(hid[ncp_name.primary]) == 0 and len(hid[ncp_name.secondary]) == 0:
                print('Error: No hid found for expression', expr)
                exit(0)
            
            # each component must has one and at most one primary hid
            if len(hid[ncp_name.primary]) > 1:
                print('Error: Multiple primary hid found for expression', expr)
                exit(0)            
            
            # if no primary hid, then at most one secondary hid
            # each component must has one and at most one primary hid
            if len(hid[ncp_name.primary]) == 0 and len(hid[ncp_name.secondary]) > 1:
                print('Error: No primary hid, multiple secondary hid found for expression', expr)
                exit(0)  
            '''
            #######################################################
            selected_hid = None
            if len(hid[ncp_name_g2.primary]) == 0:
                if len(hid[ncp_name_g2.secondary]) == 0:
                    print('Error: No primary or secondary hid found for expression', expr)
                    exit(0)                    
                elif len(hid[ncp_name_g2.secondary]) == 1:
                    # select the only secondary hid
                    selected_hid = hid[ncp_name_g2.secondary][0]
                else:
                    print('Error: No primary hid, multiple secondary hid found for expression', expr)
                    exit(0)                     
            elif len(hid[ncp_name_g2.primary]) == 1:
                # select the only primary hid
                selected_hid = hid[ncp_name_g2.primary][0]     
            else:
                print('Warning: Multiple primary hid found for expression', expr)                  
                selected_hid = hid[ncp_name_g2.primary]

                # Temporary work around
                selected_hid_new = hid[ncp_name_g2.primary]

                # sort hid
                selected_hid.sort()
                
                # Temporary work around
                selected_hid_new.sort()

                # join different elements
                selected_hid = '_'.join([str(elem) for elem in selected_hid]) 
     
                # Temporary work around
                selected_hid = selected_hid_new[0]

            #######################################################
 
            # construct the name of the subproblem
            name_dist_sub = self.cstr_name_dist_subprob_g2(prob_layer, selected_hid)
            
            # add this component expression to the corresponding subproblem
            new_prob = self.add_expr_to_suprob_g2(name_dist_sub, expr)
            # create mapping between hid and problem

            self.hid_prob_mapping[name_dist_sub] = selected_hid

    def cstr_name_dist_subprob_g2(self, layer, hid):  
        return '__' + layer + '_' + str(hid)

    def det_hid_g2(self, expr):
        '''
        Func: determine the horizontal node id for an expression
        
        Input
        expr: the expressions
        
        Output
        hid: horizontal node id
        '''
        
        # since an expression may contain multiple opreands, we need to determine 
        # hid for each operand. of course, only one operand should have valid hid
        # otherwise, the expression cannote be decomposed to a distributed problem
        
        # primary: hid of network elements; secondary: hid of constraints and lagrangian coefficients
        hid = {ncp_name_g2.primary: [], ncp_name_g2.secondary:[]}
        
        # get the operands contained in the expressions
        list_operand = self.walk_tree_g2(expr)

        # if no operations contained in expr, the operand is expr itself
        if list_operand == []:  
            list_operand = [expr]        
        
        # determine hid for each operand
        for operand in list_operand:
            cur_hid = self.det_hid_one_op_g2(operand)
            # record the hid for the current operand
            if cur_hid['hid_type'] is None:
                # use the default hid of the problem
                pass
            else:
                hid_type = cur_hid['hid_type']  # get hid type
                if cur_hid['hid'] not in hid[hid_type]:
                    hid[hid_type].append(cur_hid['hid'])

        return hid
    
    def det_hid_one_op_g2(self, op):
        '''
        Func: determine the horizontal node id for an operand
        
        Input
        op: the operand
        
        Output
        hid: horizontal node id for the operand
        '''    
        # get the object of corresponding to the operand
        # if not existent, return none
        # otherwise, get the hid
        hid =  None
        hid_type = None
        
        op_obj = self.ntwk.get_netelmt_g2(str(op))      # get_netelmt accepts only string   

        if op_obj is not None:    
            hid = op_obj.get_hid_g2()      # get_hid defined in net_func.py 
            if hid is not None:
                # the returned hid is only node index, we want to return the node name
                hid_type = ncp_name_g2.primary
                
        else:
            # if op a ncp element?
            op_obj = self.vncp.get_netelmt(str(op))
            if op_obj is not None:
                hid = op_obj.hid
                hid_type = ncp_name_g2.secondary

        return {'hid_type': hid_type, 'hid': hid}
        
    def ping(self):           
        
        print('#################################################')
        print('        ## Distributed Problems ##')
        print('#################################################')
        
        # print all subproblems
        self.ntwk.hori = self
        for expr in self.__dict__.keys():
            if '__' in expr:
                value = getattr(self, expr)
                print(expr, ':', value)


    def get_list_prob(self):
        '''
        Get the list of algorithms to be generated
        
        return: the name list of subproblems
        '''
        list_prob = []
        
        for expr in self.__dict__.keys():
            # The name of subproblem starts with '__'
            if '__' in expr:
                list_prob.append(expr)
                
        return list_prob
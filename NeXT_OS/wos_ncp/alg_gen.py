# Automated Algorithm Generation
# import sys
# sys.path.insert(0, '../wos-network')
import net_name, netcfg
import numpy as np
import os, time
import subprocess
import ncp
from sympy.parsing.sympy_parser import parse_expr
import sympy as smp
import platform

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

# import directory module
import os_dir

import pps_dir

import mobi_config

class alg_config():
    '''
    Configure agent for algorithm generation 
    '''
    def __init__(self):
        self.pnl_scheme = 'None'               # penalization scheme; no penalization by default
        self.driver_file = 'usrp_pps_para'     # driver file     
        
class alg_gen(ncp.ncp_func):
    '''
    Definition of algorithm generation logic
    '''
    def __init__(self, hdcp, cfg):
        '''
        hdcp: object of horizontally decomposed subprbolems
        cfg: algortihm generation configuration
        '''
        self.hdcp = hdcp      
        self.ncp  = self.hdcp.ncp
        self.ntwk = self.hdcp.ntwk
        self.vncp = self.hdcp.vncp    
        
        # list of nodes who need to update Lagrangian coefficients
        self.list_node = []    

        self.cfg = cfg
        
        self.scrp_name = self.get_script_name() #Store the name of the script, later will be used to retrieve the name of the NCP

        #######################################################
        # get the list of subproblems
        #######################################################
        list_prob = self.hdcp.get_list_prob()  

        # Check for optimization variables in the subproblems and create a new list for algorithm generation
        list_prob = self.detect_opt_var(list_prob)

        #######################################################
        # Create a file for mapping the generated algorithms to each node
        #######################################################
        file_name = 'map_alg2node.py'
        file_dir = os_dir.driver_dir
        ini_content = '# Mapping from the generated algorithms to nodes\n'
        self.file_map_alg2node = file_dir+file_name
        self.ini_file(self.file_map_alg2node, ini_content)

        #######################################################
        # initialize algorithm files
        #######################################################   
        directory1 = './'+self.alg_folder_name+'/'        
        self.ini_lag_file(directory1, '.py', 'lag_in')       # lag files used by algorithms
        self.ini_lag_file(directory1, '.py', '__net_para')   # network parameters used by algorithms

        #######################################################
        # generate algorithm for each problem
        #######################################################
        for prob in list_prob:
            self.alg_gen_one_prob(self.hdcp, self.cfg, prob)
        #######################################################        
        # generate Lagrangian coefficnet to be updated for each node
        #######################################################      
        # prepare for generation of lag_out file
        for lag in self.vncp.list_lag:
            self.prepare_grt_lag_out_file(lag)
            
        # generate lag out file, i.e., Lagrangian coefficients to be udpated by nodes
        print('----------------------------------------------------')
        for node in self.list_node:
            # store in a file the list of lag coefficients to be updated by this node
            # and return the lag list
            lag_list = self.gnrt_lag_out_file(node)

            # generate updating algorithm for each lagrangian coefficient
            for lag in lag_list:

                # create a folder for each lagrangian coefficient
                result_dict = self.gnrt_lag_update_folder(lag)                
                directory = result_dict['directory']
                
                # generate algorithm file
                self.gnrt_lag_alg_node_perlag(directory, node, lag)
                            
    def ini_file(self, file_dir_name, ini_content):
        '''
        Initialize the file. If not existent, crate a new one, otherwise delete the existing content
        '''
        h_file = open(file_dir_name, 'w+') 
        h_file.write(ini_content)
        h_file.close()         
      
          
    def gnrt_lag_update_folder(self, lag):
        '''
        Generate the folder for updating the lagrangian coefficient
        
        lag: the lagrangian coefficient
        
        return: a dictionary containing the created folder
        '''
        
        # construct dirctory where the algroithms will be stored
        directory1 = './'+self.alg_folder_name+'/'
        directory = directory1 + lag + '/'
        
        # create a folder for this algorithm if haven't yet
        if not os.path.isdir(directory):
            os.mkdir(directory)  

        return {'directory': directory}
        
    
    def gnrt_lag_alg_node(self, node):
        '''
        Func: generate algorithms for updating Lagrangian coefficients for a node
        
        node: the node
        
        This funcion is not used any more. Instead of creating a folder for each node,
        a folder will be created for each lagrangian coefficient
        '''        
        
        # construct dirctory where the algroithms will be stored
        directory1 = './'+self.alg_folder_name+'/'
        directory = directory1 + '_lag_' + node + '/'
        
        # create a folder for this algorithm if haven't yet
        if not os.path.isdir(directory):
            os.mkdir(directory)         
        
        # get the list of Lagrangian coefficients this node needs to update
        list_lag = getattr(self, node)

        # for each lagrangian coefficnet, generat the algorithm
        for lag in list_lag:
            self.gnrt_lag_alg_node_perlag(directory, node, lag)
            
    def gnrt_lag_alg_node_perlag(self, directory, node, lag):
        '''
        Func: generate updating algorithm for one Lagrangian coefficient
        
        directory: the dirctory where the generated algorithm will be stored
        node: the node who will run the algorithm at network run time
        lag: Lagrangian coefficient to be updated
        '''        
        
        ##########################################################################
        # Generate the mathematical expression for updating this lagrangian coefficient
        ##########################################################################
        
        # get the name of the constraint associated to this lagrangian coefficient
        name_cstr = self.vncp.mapping_lag_to_cstr[lag]
        
        # get the corresponding object
        obj_cstr = self.ncp.get_netelmt(name_cstr)
        
        # get the expression of the constraint. For updating Lagrangian coefficients, the original
        # expression will be used rather than the expanded expression
        expr_cstr = obj_cstr.expr_ori
        
        ##########################################################################
        # Create a file for the derivative of the lagrangian coefficient
        ##########################################################################         
        file_name = directory + 'lag_der.py'
        h_file = open(file_name, 'w+')

        content = 'value = ' + '\'' + expr_cstr + '\''
        
        h_file.write(content)
        h_file.close()
        #return
        
        ##########################################################################
        # Create a file for the name of the lagrangian coefficient
        ##########################################################################
        file_name = directory + 'lag_name.py'
        h_file = open(file_name, 'w+')
        content = 'value = ' + '\'' + lag + '\'\n' 
        
        h_file.write(content)
        content = 'alg_name = '+ '\'' + net_name.alg_dir + '\''
        h_file.write(content)
        
        h_file.close() 

        ##########################################################################
        # Create a file for the node of the lagrangian coefficient
        ##########################################################################
        file_name = directory + 'lag_node.py'
        h_file = open(file_name, 'w+')

        content = 'value = ' + '\'' + node + '\''
        
        h_file.write(content)
        h_file.close()         
        
        ##########################################################################
        # Copy the required template file to the corresponding folder
        ########################################################################## 
        
        # folder and name of the source template file
        src_directory = './wos-ncp/'
        template_file = 'lag_update_template.py'
                
        # creat a copy of the template file in the destination folder
        self.add_to_algorithm(directory+template_file, src_directory+template_file, 'w+')        
        
        ##########################################################################
        # Generate the algorithm file
        ##########################################################################        
        # construct the name for the destination algorithm file
        directory1 = './'+self.alg_folder_name+'/'        
        dst_directory = directory1                   
        dst_file = dst_directory + 'lag_update_' + lag + '.py'
        
        print('Generating algorithm ', 'lag_update_' + lag, '...')
        # Check if the file already exists in the directory. If not, add the algorithm to the directory
        # if not os.path.isfile(dst_file):
        # template file
        template_file = directory + 'lag_update_template.py'
        
        # Generate the algorithm file based on the template
        subprocess.call('python -m cogapp -d -o' + ' ' + dst_file + ' ' + template_file)
               
        ##########################################################################
        # Generate the file storing the lag parameters used in the algorithm
        ##########################################################################          
        
        # Create the file
        #file_name = directory + 'lag_para.py'
        file_name = dst_directory + 'lag_para_' + lag + '.py'
        h_file = open(file_name, 'w+')

        content = '# Current value, initialized to 1, updated at network run time. \n'
        
        # current value of the lagrangian coefficient
        cur_val = 'cur_val = ' + '1\n\n'        
        content = content + cur_val
        
        # step size
        comment = '# Step size, initialized to 0.1\n'
        step_size = 'lag_step = ' + '0.1'
        content = content + comment + step_size
        
        h_file.write(content)
        h_file.close()

        ##########################################################################
        # Generate the file storing the network parameters used in the algorithm
        # The parameters are those used in expr_cstr above
        ##########################################################################          
        
        # Create the file
        # Instead of creating a network parameter file for each lag coefficient,
        # the file will be created for each node

        file_name = dst_directory + '__net_para_' + node + '.py'

        # If the file is already created, open in append mode;
        # otherwise, create a new one
        if not os.path.isfile(file_name):
            h_file = open(file_name, 'w+')
            h_file.write('import numpy as np\n')
            h_file.close()
        h_file = open(file_name, 'a')    
        
        # detect all the network elements in the expression
        result_dict = self.detect_netelmt(expr_cstr)
        elmt_list = result_dict['elmt_list']

        # prepare the content to be written to the file
        content = ''       
        for elmt in elmt_list:
            cur_content = elmt + ' = 1 \n'
            content = content + cur_content

        # write content to the file and close the file
        h_file.write(content)
        h_file.close()    

    def detect_netelmt(self, str_expr):
        '''
        func: detect all the network elements involved in a string expression
        
        str_expr: the string expression 
        
        return: dictionary containing the element list
        '''
        
        # convert the string expression to symbolic
        sym_expr = parse_expr(str_expr)
        
        # get the component expressions contained in the expression
        comp_expr = self.walk_tree(sym_expr)
        
        # if the expression contains only single item, the returned list is empty
        # in this case, add the item manually
        if len(comp_expr) == 0:
            comp_expr.append(sym_expr)  
        
        # Initialize the network element list to an empty list
        elmt_list = []
        
        # check each component expression if it is a network element
        for expr in comp_expr:
            obj_elmt = self.ntwk.get_netelmt(str(expr))
            if obj_elmt is not None:  # not an element
                elmt_list.append(str(expr))
     
        return {'elmt_list':elmt_list}
           
    def gnrt_lag_out_file(self, node_name):
        '''
        Func: generate a lag_out file to record the list of Lagrangian coefficnet a node
        needs to udpate at network run time
        
        node_name: the node who will update the Lagrangian coefficients
        
        return: the list of lagrangian coefficients to be updated by this node
        '''
        # directory where the file will be located
        directory1 = './'+self.alg_folder_name+'/'    
        directory1 = directory1      
        #directory1 = './wos-algorithm-next-demo2/'      
        
        # construct file name
        file_name = directory1 + 'lag_out_' + node_name + '.py'
        
        # open the file; create one if nonexistent yet
        file = open(file_name, 'w+')
        
        #########################################
        # prepare the content to be written      
        #########################################
        content = 'value = '
        
        # get the lag list
        lag_list = getattr(self, node_name)
        
        # append to the content
        content = content + str(lag_list)        
        
        #########################################
        # write the content to the file
        file.write(content)
        
        # close file
        file.close()       

        return lag_list
                
            
    def prepare_grt_lag_out_file(self, lag_name):
        '''
        Func: Preparation for generation of lag_out file. Create a list of lag names that each node needs
        to update at network run time
        
        lag_name: Lagrangian coefficnet
        '''
        
        # get the  hid for this Lagrangian coefficnet
        hid = self.vncp.mapping_lag_to_node[lag_name]

        # if the node is not an element of the list. then add this node to the list
        if hid not in self.list_node:
            self.list_node.append(hid)

        # Create a lag list for this node if have not yet
        if not hasattr(self, hid):
            setattr(self, hid, [])
        
        # Get the list, append this lag to the list, update the list
        list_lag = getattr(self, hid)
        list_lag.append(lag_name)                        
        setattr(self, hid, list_lag)

    def ini_lag_file(self, tgtdir, ext, keyword):  
        '''
        func: initialize algorithm files by deleting the content
        
        tgtdir: target directory1
        ext: extension of the file
        keyword: a file will be initialized if the file name contains the keyword
        '''       
        for file in os.listdir(tgtdir):               
            if file.endswith(ext) and keyword in file:
                h_file = open(tgtdir + file, "w")
                h_file.write('import numpy as np\n')
                h_file.close()
            
    def add_to_algorithm(self, alg_file, new_file, mode):
        '''
        func: append new file to the algorithm file
        
        alg_file: algorithm file
        new_file: new algorithm file to be appended
        mode: overwrite ('w+') or append ('a')
        
        return: updated algorithm file
        '''
        
        # open files
        f1 = open(alg_file, mode)  # for appending 
        f2 = open(new_file, 'r')  # for reading
        
        # append
        content = f2.read()
        f1.write(content)        
        
        # close files
        f1.close()
        f2.close()        
            
    def alg_gen_one_prob(self, hdcp, cfg, prob):
        '''
        func: generate algorithm for one distributed problem
        
        hdcp: object of horizontally decomposed subprbolems
        cfg: algortihm generation configuration
        prob: the problem for which algorithm to be generated
        
        return: algorithms generated for prob, stored in folder "wos-algorithm-next"
        '''
        print('Generating algorithm', prob, '...')
        #######################################################
        # Preparing directories
        #######################################################
        directory1 = './'+self.alg_folder_name+'/'
        
        directory2 = './wos-ncp/'
        dst_directory = directory1
        
        new_path = directory1 + prob + '/'      
        if not os.path.isdir(new_path):
            os.mkdir(new_path) 
            
        dst_file = 'alg_template_objective.py'       
        self.add_to_algorithm(new_path+dst_file, directory2+dst_file, 'w+')
        
        dst_file = 'alg_template_header.py'
        self.add_to_algorithm(new_path+dst_file, directory2+dst_file, 'w+')
        
        #######################################################
        # Detecting optimization variables 
        #######################################################
        
        # keywords of the optimization variables
        key_var = self.ncp.list_var
        
        # get the expression of the utility
        expr = getattr(hdcp, prob)

        # detect the variables
        result_dict = self.detect_key(key_var, expr)
        var_name_list = result_dict['list_var']
        key_name_list = result_dict['list_key']
        netcfg.var_name_list = var_name_list

        if len(var_name_list) == 0:
            print('No optimization variable detected in problem', prob)
            exit(0) 
        
        if len(var_name_list) > 1:

            mobi_config.mul_var_flag = True

        #######################################################
        # Detecting lagrangian variables 
        #######################################################        
        result_dict = self.detect_key(['lag'], expr)
        lag_list = result_dict['list_var']
        
        # hid of this problem
        hid = self.hdcp.hid_prob_mapping[prob]

        if hid not in net_name.node_list:
            net_name.node_list.append(hid)

        # file name to be created
        lag_in_name = 'lag_in_' + hid + '.py'   
        file_name = directory1 + lag_in_name

        # Cannot check the existence of the file here
        # Otherwise, the file may be overwritten later
        # Existence check is done in ini_lag_file()
        
        # If the file does not exist, create one
        if not os.path.isfile(file_name):
            file = open(file_name, 'w+')
            file.close()
        
        # define lagrangian coefficients in the file    
        for lag in lag_list:
            content = lag + ' = 0  # Initialized to zero, updated at network run time' + '\n' 

            # Append the new content to the file if the content is not in the file
            self.check_and_append(file_name, lag, content)
            
        #######################################################
        # detecting network elements involved in this problem
        #######################################################            
        result_dict = self.detect_netelmt(str(expr))
        elmt_list = result_dict['elmt_list']
        
        # file name for network elements for this problem
        net_para_file = dst_directory + '__net_para_' + hid + '.py'
        
        # For each network element, add it to the file if it is not there yet 
        # and if the element is not the optimization variable        
        for elmt in elmt_list:
            # if elmt in var_name_list:
                # # This element is an optimization variable, no need to add to network parameter file
                # # Still need to add to network parameter file, to store the current value of the parameter1
                # pass
            # else:
                # Add to network parameter file
                content = elmt + ' = 1\n'
                self.check_and_append(net_para_file, elmt, content)
                #pass 
               
        # add panel coefficient as network parameters
        zero_list = []
        # Update the pnl coefficient array based on number of opt var elmt
        for var in range(len(var_name_list)):
            zero_list.append(0)

        content = 'pnl_coefficient = np.array('+str(zero_list)+')'+'\n' 
        file = open(net_para_file,'a')  # open in append mode   
        file.write(content)          
        file.close()
        
        #######################################################
        # file name to store optimization varibale
        #######################################################
        if not mobi_config.mul_var_flag:
            file = open(new_path + "__alg_variable.py",'w+')
            content = 'value = \'' + str(var_name_list[0]) + '\'\n'
            file.write(content)
            content = 'key = \'' + str(key_name_list[0]) + '\'\n'
            file.write(content)
            file.close()  
        else:
            file = open(new_path + "__alg_variable.py",'w+')
            content = '#This file contains multiple values and keys for the optimization variables\n#This file is automatically generated\n'
            file.write(content)
            val_array = []
            key_array = []
            for varid in range(len(var_name_list)): 
                val_array.append(str(var_name_list[varid]).replace("'", ""))
                key_array.append(str(key_name_list[varid]).replace("'", ""))
                
            content = 'value = ' +'"'+'np.array('+str(val_array).replace("'", "")+')'+'"'+'\n'
            file.write(content)
            content = 'key = ' +'"'+'np.array('+str(key_array).replace("'", "")+')'+'"'
            file.write(content)
            file.close()
            

        #######################################################
        # prepare algorithm name
        #######################################################
        file = open(new_path + "__alg_name.py",'w+')
        content = 'value = \'' + prob + '\'\n'
        file.write(content)
        content = 'hid = \'' + self.hdcp.hid_prob_mapping[prob] + '\'\n'
        file.write(content)
        content = 'algo_name = \'' + net_name.alg_dir + '\''
        file.write(content)
        file.close()
        
        #######################################################
        # generate utility function
        #######################################################
        file = open(new_path + "__alg_utility.py",'w+')

        objvar_key = None
        '''
        Based on the multiple variable flag (mul_var_flag) we prepare the objvar variables
        If the mul_var_flag is not set (i.e., there is only one opt variable, 
        we just use objvar and then prepare the corresponding lower and upper default expressions
        '''
        if not mobi_config.mul_var_flag:
            expr_new = str(expr).replace(var_name_list[0],"objvar")
            expr = expr_new
            objvar_key = 'objvar'
            lwr_cstr = 'net_name.'+key_name_list[0]+'_lwr_default'
            upr_cstr = 'net_name.'+key_name_list[0]+'_upr_default'
        else:
            '''
            If the mul_var_flag is set (i.e., there are more than one opt variables, 
            we loop over the length of the opt variable list and prepare the corresponding objvar array
            then prepare the corresponding lower and upper default expressions
            '''
            objvarkey_array = []
            lwr_cst_array = []
            upr_cst_array = []
            for varid in range(len(var_name_list)): 
                objvar_name = 'objvar'+'['+str(varid)+']'
                expr_new = str(expr).replace(var_name_list[varid],objvar_name)
                expr = expr_new
                objvarkey_array.append(objvar_name.replace("'", ""))
                lwr_cstr_name = 'net_name.'+key_name_list[varid]+'_lwr_default'
                upr_cstr_name = 'net_name.'+key_name_list[varid]+'_upr_default'
                lwr_cst_array.append(lwr_cstr_name.replace("'", ""))
                upr_cst_array.append(upr_cstr_name.replace("'", ""))
            objvar_key = objvarkey_array

        content = 'value = \'' + str(expr) + '\'' 
        file.write(content)
        content = '\n' 
        file.write(content)
        '''
        All the following details are automatically generated and stored in the corresponding __alg_utility file
        '''
        if not mobi_config.mul_var_flag: 
            # Objvarkey will hold the values objvar 
            content = 'objvarkey =\'' +objvar_key+ '\''+'\n'
            file.write(content)
            # lwrkey will hold the lower bound of the objvar
            content = 'lwrkey =\'' +lwr_cstr+ '\''+'\n'
            file.write(content)
            # uprkey will hold the upper bound of the objvar
            content = 'uprkey =\'' +upr_cstr+ '\''+'\n'
            file.write(content)
            # lwr will hold the lower bounds of the objvars which will be used as a argument in scipy.minimize
            content = 'lwr =\'' +lwr_cstr+ '\''+'\n'
            file.write(content)
            # pnl_sum will hold the addition technique for the pnl coefficient received from other nodes, here we just use regular addition
            content = 'pnl_sum =\'' +'pnl_coefficient'+ '\''+'\n'
            file.write(content)
        else:
            # Objvarkey will hold the values [objvar[0], objvar[1] and so on...] 
            content = 'objvarkey = ' +'"'+'np.array('+str(objvar_key).replace("'", "")+')'+'"'+'\n'
            file.write(content)
            # lwrkey will hold the lower bound of the objvar
            content = 'lwrkey = ' +'"'+str(lwr_cst_array[0]).replace("'", "")+'"'+'\n'
            file.write(content)
            # uprkey will hold the upper bound of the objvar
            content = 'uprkey = ' +'"'+str(upr_cst_array[0]).replace("'", "")+'"'+'\n'
            file.write(content)
            # lwr will hold the lower bounds of the objvars which will be used as a argument in scipy.minimize
            content = 'lwr = ' +'"'+str(lwr_cst_array).replace("'", "")+'"'+'\n'
            file.write(content)
            # pnl_sum will hold the addition technique for the pnl coefficient received from other nodes,
            # here we use row wise addition since each nodes penalization terms are stored in that format e.g., [[x1 x2 ...]\[y1 y2...] ]
            content = 'pnl_sum =\'' +'sum(pnl_coefficient, axis = 1)'+ '\''+'\n'
            file.write(content)
            
        file.close()  
        
        #######################################################
        # generate header information
        #######################################################
        alg_file = dst_directory + prob + '.py'
        template_file = new_path + 'alg_template_header.py'        
        subprocess.call('python -m cogapp -d -o' + ' ' + alg_file + ' ' + template_file)
        
        #######################################################
        # Map this file to the corresponding node
        #######################################################
        filename = self.file_map_alg2node
        node_name = hid
        alg_name = prob
        self.map_alg2node(filename, node_name, alg_name)
        
        
        #print('4')
        #######################################################
        # generate objective information  
        #######################################################        
        temporary_file = new_path + 'temporary.py'
        template_file = new_path + 'alg_template_objective.py' 
        subprocess.call('python -m cogapp -d -o' + ' ' + temporary_file + ' ' + template_file)
        
        self.add_to_algorithm(alg_file, temporary_file, 'a')
        
        #######################################################
        # generate algorithms for updating the penalization terms
        ####################################################### 
        
        # prepare information used when generating the algorithm
        dic_alg_info = {'dir': directory1}                      # dirctory to generate the algorithm file
        dic_alg_info['hid'] = self.hdcp.hid_prob_mapping[prob]  # node that will execute the algorithm
        dic_alg_info['prob'] = prob                             # name of the problem being processed
        
        # generate the algorithm
        dic_rslt = self.gnrt_pnl_updt_term(dic_alg_info)

        # if no external variable involved in this problem, do nothing; otherwise, generate the algorithm file         
        if dic_rslt is None: 
            # do nothing
            pass                            
        else: 
            # generate the py algorithm file
        
            # first, symbolic expression of the penalization term
            der_sym = dic_rslt['der_sym']   
            
            # then, generate the algorithm py file
            self.gnrt_pnl_updt_alg(dic_alg_info, der_sym)
            
            #print(der_sym)
            #input('...')
            
    def map_alg2node(self, filename, node_name, alg_name):
        '''
        map alg_name to node_name and write the information to filename
        '''
        # open the file to read its content
        file = open(filename, 'r')
        cur_content = file.read()
        file.close()
        
        # open the file to append new content
        # if the node name does not exist in the file, then append it
        file = open(filename, 'a')
        if node_name not in cur_content:                        
            content = node_name + '= []\n'
            file.write(content)
            
        # append the algorithm name to the node name
        content = node_name + '.append(\'' + alg_name + '\')\n'
        file.write(content)
            
        file.close()
        

    def gnrt_pnl_updt_alg(self, dic_alg_info, der_sym):
        '''
        Generate the penalization algorithm py file
        
        dic_alg_info: dictionary of algorithm information
        der_sym: symbolic expression of the penaliation term
        
        output: generated py files in wos-algorithm-next/
        '''

        ##############################################################
        # write the penalization term in a tempary file for later use
        ##############################################################
        
        # destination dirctory and file 
        dst_dir = dic_alg_info['dir'] + dic_alg_info['prob'] + '/'        
        dst_file_name = dst_dir + 'pnl_term.py'
        dst_file = open(dst_file_name, 'w+', newline='')
        
        # write the penalization term
        content = 'value = \'' + str(der_sym) + '\''
        dst_file.write(content.replace("\n", ""))
        
        # close the file
        dst_file.close()
        
        ##############################################################
        # copy the algorithm template to the folder for this problem
        ##############################################################   
        
        # folder and name of the source template file
        src_directory = './wos-ncp/'
        template_file = 'alg_template_pnl.py'
                
        # creat a copy of the template file in the destination folder
        self.add_to_algorithm(dst_dir+template_file, src_directory+template_file, 'w+')         

        ##############################################################
        # generate the algorithm file
        ##############################################################          
        
        alg_file = dic_alg_info['dir'] + 'pnl' + dic_alg_info['prob'] + '.py' 
        template_file = dst_dir+template_file
        #print(alg_file)
        #print(template_file)
        #exit()
        subprocess.call('python -m cogapp -d -o' + ' ' + alg_file + ' ' + template_file)
        
        #print(alg_file)
        #input('...')      
              
    def gnrt_pnl_updt_term(self, dic_info):
        '''
        Generate penalization term for the updating algorithm. The updated penalization terms will be 
        sent to the node where the penalization coefficient will be used
        
        An algorithm file will be generaeted if the problem involves external variables
        Otherwise, no need to generate the penaliation updating algorithm
        
        dic_info: dictionary containing the information needed to generat the algorithm
        '''
        
        # get the expression of the problem
        expr = getattr(self.hdcp, dic_info['prob'])
        
        # Get the list of network elements involved in the problem expression
        list_elmt = self.detect_netelmt(str(expr))

        # Detect external variables in the expression
        dict_rslt = self.detect_xtnl(list_elmt)
        list_xtnl = dict_rslt['list_xtnl']
                
        # If no external variabls detected, no need to generate penalization algorithms
        if len(list_xtnl) == 0:
            #print('No external parameters detected.')
            return None
        
        ###############################################################################
        # One external variables detected, generate the penalization algorithm
        ###############################################################################
        # convert the string external varible to symbolic'
        
        if len(list_xtnl) == 1:
            para_sym = parse_expr(list_xtnl[0])
            der_sym = smp.diff(expr, para_sym)
        else:
            expr_array = ''
            para_sym = parse_expr(list_xtnl[0])
            der_sym = smp.diff(expr, para_sym)
            expr = der_sym
            length = len(list_xtnl[1:])
            for xtnl in list_xtnl[1:]:
                expr2 = smp.diff(expr, xtnl)
                expr_array = expr_array+'['+str(expr2)+']'+','
            der_sym = expr_array[:-1] # Remove the last unnecessary comma before returning the derivative
            der_sym = '['+str(der_sym)+']' # Add outer square bracket to form an array

        # returning 
        dic_rslt = {'der_sym': der_sym}        
        
        return dic_rslt
               
    def detect_xtnl(self, list_elmt):
        '''
        Detect external variables in the element list
        '''
        # list of external parameters, initialized to be empty
        list_xtnl = []
        
        # get the parameter type of each network element
        for elmt in list_elmt['elmt_list']:                     
            obj_elmt = self.ntwk.get_netelmt(elmt)            

            # get the type of the parameter
            elmt_type = obj_elmt.para_type

            # If this element is external and has not been recorded before, record it
            if elmt_type == net_name.xtnl_para and not elmt in list_xtnl:
                list_xtnl.append(elmt)
        
        # returning
        dic_rslt = {'list_xtnl': list_xtnl}
        return dic_rslt        
        
    def check_and_append(self, file_name, str_elmt, content):
        '''
        Check if str_elmt is contained in file_name. If not, append the conent to file_name
        '''
        # if the file does not exist, creat it
        if not os.path.isfile(file_name):
            file = open(file_name,'w+')
            file.close()
        
        # get the current content                 
        file = open(file_name,'r')      # open in read mode   
        cur_content = file.read()
        file.close
        
        # write if content has not been written before
        if str_elmt not in cur_content:
            file = open(file_name,'a')  # open in append mode   
            file.write(content)          
            file.close()        
    
    def detect_key(self, key_var, prob_expr):
        '''
        detect the variables in prob_expr with keywords key_var
        '''
        
        ######################################################
        # first, get the component expression in prob_expr
        
        # get the component expressions
        comp_expr = self.walk_tree(prob_expr)
        
        # if the expression contains only single item, the returned list is empty
        # in this case, add the item manually
        if len(comp_expr) == 0:
            comp_expr.append(expr_sym)
        
        ######################################################
        # second, loop over all keywords
        
        # initialize the variable list to be empty
        list_var = []
        list_key = []
        
        # check each keywords
        for keyword in key_var:
            # loop over all component expressions
            for expr in comp_expr:
                # if the expression contains the keyword?
                if keyword in str(expr):
                    # the expression must be a single-item expression
                    if self.is_single_item_expr(expr):
                        # if the expression is not recorded yet
                        if str(expr) not in list_var:
                            list_var.append(str(expr))
                            list_key.append(keyword)
                                   
        return {'list_var': list_var, 'list_key': list_key}
        
    def detect_opt_var(self, prob_list):
        '''
        func: Detect the optimization variables in the sub problems and create a new sub prob list that contains the optimization variable
        prob_list: list of the subproblems
        '''
        hdcp = self.hdcp
        key_var = self.ncp.list_var
        new_prob_list = []
        
        # loop over all the subproblems and get the corresponding expression and the optimization variable in the expression.
        # if the number of optimization variable is 1, append the problem to the list else ignore
        
        for prob in prob_list:
            expr = getattr(hdcp, prob)
            result_dict = self.detect_key(key_var, expr)
            var_name_list = result_dict['list_var']
            if len(var_name_list) >= 1:
                new_prob_list.append(prob)

        return new_prob_list
        
    def get_script_name(self):
        '''
        Func: Get the name of the script and also create a new directory (if it does not exist).
        The script name will be appended to the 'wos-algorithm-next'+'xxx' and a new directory will be created
        to store the generated algorithms
        
        Returns the name of the script 
        '''
        # Get the name of the executed file
        script_name = sys.argv[0][3:-3]
        
        # Obtain the name of the folder based on the script name
        name_folder = net_name.dict_ncp_names_file[script_name]
        
        # Create the algorithm repository name
        alg_fldr_name = '/NCP-'+name_folder
        
        # Store the name of the algorithm repository. It will be used later while algorithm generation
        self.alg_folder_name = alg_fldr_name
        
        # Create the name of the path where the repository should be stored
        path =os.getcwd()+alg_fldr_name+'/'
        
        # Store the path of the algorithm in net_name, this will be used as a part of the algorithm template
        net_name.alg_dir = '../NeXT-OS'+alg_fldr_name
                
        # Check if the repository already exits, if it does not exist, make the repository in the specified path
        if not os.path.isdir(path):
            os.mkdir(path)
            
        ###############################################################################
        # Record the algorithm repo in Next-Driver. This will be used when executing the PPS code

        file_name = os_dir.driver_dir+'alg_dir_name.py'

        # get the current content                 
        file = open(file_name,'r')      # open in read mode   
        cur_content = file.read()
        file.close
        # write the content 
        file = open(file_name,'w+')  # open in append mode   
        content = '\'../NeXT-OS'+alg_fldr_name+'/'+'\''
        file.write(content)          
        file.close() 
      
        return script_name
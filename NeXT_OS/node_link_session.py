# Add search paths
import sys, os, inspect

sys.path.append("./wos-dir/")
sys.path.append("./wos-ncp/")
sys.path.append("./wos-network/")
sys.path.append("../")
sys.path.append("../NeXT-PPS")
sys.path.append("../../")
sys.path.insert(0, './wos-network')
sys.path.insert(0, './wos-ncp')
sys.path.insert(0, './wos-dir')
sys.path.insert(0, '../NeXT-PPS')

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))

sys.path.insert(0, parent_dir + '\OSW_G2_elmtlib\element_library')

import pps_dir

file_name = 'node_link_session.py'
file_dir = pps_dir.driver_dir
ini_content = '#######################################################\n###\
 Automatically Generated File\n### Mapping nodes to corresponding session and link\n\
#######################################################\n'
file_dir_name = file_dir+file_name
h_file = open(file_dir_name, 'w+')       
h_file.write(ini_content)
h_file.close()
    
def file_write(dict_info):
    print(dict_info)
    file = open(file_dir_name, 'r')
    cur_content = file.read()
    file.close()
    
    # open the file to append new content
    # if the node name does not exist in the file, then append it
    node_name = dict_info['node']
    link_name = dict_info['link']
    session_name = dict_info['session']
    file = open(file_dir_name, 'a')
    if node_name not in cur_content:                        
        content = node_name + '= {}\n'
        file.write(content)
            
    # add the link name and session name to the node
    content = node_name + '.update({\'' +'link'+ '\':\'' +link_name+ '\',\'' +'session'+ '\':\'' +session_name+ '\'})\n'
    file.write(content)
            
    file.close()

import netcfg

def coord():
    # Update the coordinate of this node and the next hop node
    # The next hop node coord will be further updated during optimization in signalling.py

    # This node location
    next_loc = netcfg.location[netcfg.next_hop_usrp[netcfg.idx_thisnode]] 
    
    # Next hop node location
    this_loc = netcfg.location[netcfg.all_usrp_ip[netcfg.idx_thisnode]] 

    # Retrieve the net_para_node file from the loaded dictionary (from loading.py) to update the coordinates
    netpara_file = netcfg.values_net_para['__net_para_']
    
    # First Update this node's location
    for crd in netcfg.coord_list:
        crd_name = 'coord_'+crd+'_'+netcfg.lnk_name
        crd_val = this_loc[crd]

        # Set the value
        setattr(netpara_file, crd_name, crd_val)
        
    # Now update the next node location
    for crd in netcfg.coord_list:
        crd_name = 'fx_crd_'+crd+'_'+netcfg.lnk_name
        crd_val = next_loc[crd]
        
        # Set the value
        setattr(netpara_file, crd_name, crd_val)
        
    

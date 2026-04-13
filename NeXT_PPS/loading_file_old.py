
import importlib.util

import netcfg
import pps_dir
import pickle


def load(node, node_rolee):
    netcfg.values_net_para = {}
    # list_files_to_be_loaded = ['__net_para_', '__pnl__phy_', '__lag_update_', '__lag_in_', '__phy_']
    list_files_to_be_loaded = ['__net_para_', '__pnl__phy_', '__lag_in_', '__lag_out_', '__phy_']
    # copied from OSWireless_v1 original folder

    # Get the name of the algorithm directory
    # Prepear the name of the directory storing the path of the algorithm repo
    alg_dir = pps_dir.driver_dir+'alg_dir_name.py'
    print('100', alg_dir)

    # open the algorithm directory in read mode and get the path of the alg repo
    # file = open(alg_dir,'r')      # open in read mode
    #
    # # The stored alg path has 'alg_path' - Remove the quotation marks
    # # alg_dir = file.read()[1:-1]
    # # print (alg_dir[0:-1])
    # alg_dir = file.read().replace("dir_name = '../NeXT-OS/NCP-g2_rate_power/'", "../NeXT-OS/NCP-g2_rate_power/").strip()
    with open(alg_dir, 'r') as file:
        alg_dir = file.read().replace("dir_name = '../NeXT-OS/NCP-g2_rate_power/'",
                                      "../NeXT_OS/NCP_g2_rate_power/").strip()

    # Store the path in network config file for later use7
    netcfg.alg_dir = alg_dir
    netcfg.expr_lag = {}
    print('101', alg_dir)

    for file_name in list_files_to_be_loaded:
        file_to_be_loaded = alg_dir+file_name+node+'.py'

        # # MINIMUM CHANGE: Specific correction for '__net_para_node0.py' to '__net_para_node_0.py'
        # if file_name == '__net_para_' and node == 'node0':
        #     file_to_be_loaded = alg_dir + '__net_para_node_0.py'
        #
        # # MINIMUM CHANGE: Specific correction for '__net_para_node0.py' to '__net_para_node_0.py'
        # if file_name == '__pnl__phy_' and node == 'node0':
        #     file_to_be_loaded = alg_dir + '__pnl__phy_node_0.py'

        if file_name == 'lag_update_':
            node_expr_map_file = alg_dir+'__lag_out_'+node+'.py'
            # loaded_source  = imp.load_source(node, node_expr_map_file)
            spec_expr = importlib.util.spec_from_file_location(node, node_expr_map_file)
            loaded_source = importlib.util.module_from_spec(spec_expr)
            spec_expr.loader.exec_module(loaded_source)
            # print("Node expression map file:", node_expr_map_file)
            # print("Loaded source expression:", loaded_source)

            # print("Loaded source:",loaded_source)
            file_name2 = getattr(loaded_source, 'value')[0]
            netcfg.expr_lag[file_name2] = file_name2
            file_to_be_loaded = alg_dir+'__lag_update_'+file_name2+'.py'
            print('102', file_to_be_loaded)

            # loaded_source = imp.load_source(node, file_to_be_loaded)
            spec_lag = importlib.util.spec_from_file_location(node, file_to_be_loaded)
            loaded_source = importlib.util.module_from_spec(spec_lag)
            spec_lag.loader.exec_module(loaded_source)

            netcfg.values_net_para.update({file_name: loaded_source})
            continue

        # loaded_source = imp.load_source(node, file_to_be_loaded)
        spec = importlib.util.spec_from_file_location(node, file_to_be_loaded)
        # print(("Specification:", spec))
        # print("Node:", node)
        # print("File to be loaded:", file_to_be_loaded)
        loaded_source = importlib.util.module_from_spec(spec)
        # print("Loaded source:", loaded_source)
        spec.loader.exec_module(loaded_source)
        # print("Print up to here")

        netcfg.values_net_para.update({file_name: loaded_source})

    node_link_file = 'node_link_session_g2'
    map_path = pps_dir.driver_dir+node_link_file+'.py'

    # loaded_file = imp.load_source(pps_dir.driver_dir, map_path)
    spec_node_link = importlib.util.spec_from_file_location("node_link_session_g2", map_path)
    loaded_file = importlib.util.module_from_spec(spec_node_link)
    spec_node_link.loader.exec_module(loaded_file)

    # print("Loaded file:", loaded_file)

    details = getattr(loaded_file, node)
    session_name = details['session'][0]
    link_name = details['link']
    netcfg.lnk_name = link_name
    netcfg.ses_name = 'ssrate_'+session_name

    # print("--------------- RUN UP TO HERE ------------------")

    if node_rolee == 'tx':
        file_name = '__tspt_'
        file_to_be_loaded = alg_dir+file_name+node+'.py'

        # loaded_source  = imp.load_source(node, file_to_be_loaded)
        spec_tspt = importlib.util.spec_from_file_location(node, file_to_be_loaded)
        loaded_source_tspt = importlib.util.module_from_spec(spec_tspt)
        spec_tspt.loader.exec_module(loaded_source_tspt)

        netcfg.values_net_para.update({file_name: loaded_source})

    # print("------------------- Finish compiling loading_file_old.py -------------------------")

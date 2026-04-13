#######################################################
# Date: 04/12/2017
# Author: Zhangyu Guan
# Project Manager: Tommaso Melodia, Zhangyu Guan
#
# Module description: name space of wos-alglib module
#######################################################

import sys
sys.path.insert(0, './wos-network')
sys.path.insert(0, './wos-decomp')
sys.path.insert(0, './wos-algorithm')

# Debug code, commented
# import os
# p = os.getcwd()
# print(p)
# p1 = os.path.dirname(p)
# print(p1+'/WNOS/wos-algorithm')
# input('Debug: ...')

# from wos-network
import net_name


# constant parameters
PROCESSED = 1


# for code name generation, used in dcp_hsub.gen_code_name()
code_prefix = 'code'
code_connection = '_'
alg_type = 'itpt'     # interior point, used in alglib_func.fmincon_py.gnrt_alg_name()


# Used for Lagrangian coefficient construction 
Lag_prefix = 'inst'
Lag_connect = '_'
Lag_suffix = 'lbd'

# Type of Lagrangian coefficient
sngl = 'sngl'                                       # single-type, the Lagrangian coefficient is related to a single element (e.g., link)

# Patterns of elements, e.g., the set of sessions sharing the same link
sess_lnks = 'sess_links'                            # Set of links passed by a sessions
link_sses = 'link_sses'                             # Set of sessions sharing a link
link_sngl = 'link' + Lag_connect + sngl             # A single local link

# Flag of keyword
key_flag = '00'
key_flag2 = 'lbd'
key_flag3 = 'pnl'

lst_flag = [key_flag, key_flag2, key_flag3]

# Suffix of tempary optimization variable
tmp_optvar_suf = 'tmp'

# String name of optimization variable
str_optvar = 'opt_var'
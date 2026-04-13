#######################################################
# Date: 03/19/2016
# Author: Zhangyu Guan
# Project Manager: Tommaso Melodia, Zhangyu Guan
# Name space for algorithm generation
#######################################################

#------------------------------------------
#                 general
#------------------------------------------
netalg     =   'netalg'                   # algorithm for the whole network
lexpr      =   'lexpr'                    # long expression
sep        =   '---------------------------------------------------'
stars      =   'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

#------------------------------------------
#                 suffix
#------------------------------------------
lenid      =   3                          # length of id, used together with zfill
suffix1    =   '_'                        # '_'
suffix2    =   '__'                       # '__'
suffix3    =   '___'                      # '___'

#------------------------------------------
#       polynomial regression models
#------------------------------------------
num_pnc   =   6                           # number of polynomial coefficents
pnlvar    =   'v_pnlvar'                  # penal variable
pnlpar    =   'v_pnlpar'                  # penal parameter
v_pnc0    =   'v_pnc0'                    # 1st penal coefficient
v_pnc1    =   'v_pnc1'                    # 2nd penal coefficient
v_pnc2    =   'v_pnc2'                    # 3rd penal coefficient
v_pnc3    =   'v_pnc3'                    # 4th penal coefficient
v_pnc4    =   'v_pnc4'                    # 5th penal coefficient

# multivariable (2 variable) polynomial model
mvp       =   'v_pnc0 + v_pnc1*v_pnlvar + v_pnc2*v_pnlvar**2 + v_pnc3*v_pnlvar*v_pnlpar + v_pnc4*v_pnlpar**2'   



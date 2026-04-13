
########################################################
#              Define Objective Function
########################################################
def func(objvar, sign=-1.0):
	utlt = -expr_4_lag*objvar
	pnl = - sum(pnl_coefficient*(lkcap_link_3 - objvar))
	ovl_utlt = utlt + pnl
	return ovl_utlt

########################################################
#                    Constraints
########################################################
cons = (
{'type': 'ineq',
'fun':lambda objvar: objvar - net_name_g2.lkcap_lwr_default},
{'type': 'ineq',
'fun':lambda objvar: net_name_g2.lkcap_upr_default - objvar})

########################################################
#                    Optimization
########################################################
def wnos_optimize():
    result = minimize(func, net_name_g2.lkcap_lwr_default, constraints=cons, method='SLSQP', options={'disp': False})
    return result


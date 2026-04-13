
########################################################
#              Define Objective Function
########################################################
def func(objvar, sign=-1.0):
	utlt = -expr_1_lag*objvar + expr_1_lag*theta_0_0 - expr_2_lag*objvar + expr_2_lag*theta_1_0 - expr_3_lag*objvar + expr_3_lag*theta_2_0 + 1/theta_2_0 + 1/theta_1_0 + 1/theta_0_0
	pnl = - sum(pnl_coefficient*(ssrate_session_0 - objvar))
	ovl_utlt = utlt + pnl
	return ovl_utlt

########################################################
#                    Constraints
########################################################
cons = (
{'type': 'ineq',
'fun':lambda objvar: objvar - net_name_g2.ssrate_lwr_default},
{'type': 'ineq',
'fun':lambda objvar: net_name_g2.ssrate_upr_default - objvar})

########################################################
#                    Optimization
########################################################
def wnos_optimize():
    result = minimize(func, net_name_g2.ssrate_lwr_default, constraints=cons, method='SLSQP', options={'disp': False})
    return result


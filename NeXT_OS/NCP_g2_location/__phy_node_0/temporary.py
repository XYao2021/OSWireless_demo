
########################################################
#              Define Objective Function
########################################################
def func(objvar, sign=-1.0):
	utlt = -expr_1_lag*log(1 + lkpwr_link_0/(lkitf_link_0*((objvar[0] - fx_crd_x_link_0)**2 + (objvar[1] - fx_crd_y_link_0)**2)**2))/log(2)
	pnl = - sum(sum(pnl_coefficient, axis = 1)*(np.array([coord_x_link_0, coord_y_link_0]) - np.array([objvar[0], objvar[1]])))
	ovl_utlt = utlt + pnl
	return ovl_utlt

########################################################
#                    Constraints
########################################################
cons = (
{'type': 'ineq',
'fun':lambda objvar: objvar - net_name_g2.coord_x_lwr_default},
{'type': 'ineq',
'fun':lambda objvar: net_name_g2.coord_x_upr_default - objvar})

########################################################
#                    Optimization
########################################################
def wnos_optimize():
    result = minimize(func, [net_name_g2.coord_x_lwr_default, net_name_g2.coord_y_lwr_default], constraints=cons, method='SLSQP', options={'disp': False})
    return result


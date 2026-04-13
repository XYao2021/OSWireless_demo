value = '-expr_1_lag*log(1 + lkpwr_link_0/(lkitf_link_0*((objvar[0] - fx_crd_x_link_0)**2 + (objvar[1] - fx_crd_y_link_0)**2)**2))/log(2)'
objvarkey = "np.array([objvar[0], objvar[1]])"
lwrkey = "net_name_g2.coord_x_lwr_default"
uprkey = "net_name_g2.coord_x_upr_default"
lwr = "[net_name_g2.coord_x_lwr_default, net_name_g2.coord_y_lwr_default]"
pnl_sum ='sum(pnl_coefficient, axis = 1)'

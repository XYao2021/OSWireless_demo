optvar = 'ssrate00'
objective = 'ssrate00*(-sum(sess_links_lbd)) + log(ssrate00)'

keyword = ['ssrate00','sess_links_lbd']
lb = 'net_name.rate_lwr_default'
ub = 'net_name.rate_upr_default'
scheme = 2
coef = 1000

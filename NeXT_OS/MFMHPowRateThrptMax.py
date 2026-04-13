# Network construction
...
 
# Network behavior description
nt_ctl = ncp(nt)
expr = {'expr_xpd': '', 'expr_ori': ''}
allsess = nt.get_sess_set()                     
for sess in allsess:                            
    x = nt.get_expr_new(sess, net_name.ssrate)            
    x = nt_ctl.mkexpr_new(x, 'log')    
    expr = nt_ctl.mkexpr_new(expr, x, '+')      
expr = nt_ctl.mkexpr_new(expr, '(-1)', '*')    
expr_name,info = nt_ctl.record_expr(expr)       
nt_ctl.set_utlt(expr_name)                      
alllink = nt.get_link_set()                     

for link in alllink:                            
    link_obj = nt.get_netelmt(link)             
    x = nt.get_expr_new(link, net_name.lkcap)       
    list_ses_name = nt.get_dependent_para(link, net_name.ses)                  
    y = ''
    for ses in list_ses_name:                                               
        z = nt.get_expr_new(ses, net_name.ssrate)                                   
        y = nt_ctl.mkexpr_new(y, z, '+')                                       
    expr = nt_ctl.mkexpr_new(y, x, '-')                                     
    expr_name2, info = nt_ctl.record_expr(expr, link)     
nt_ctl.set_var(net_name.ssrate)
nt_ctl.set_var(net_name.lkpwr)  
  
# Decomposition and algorithm generation
...





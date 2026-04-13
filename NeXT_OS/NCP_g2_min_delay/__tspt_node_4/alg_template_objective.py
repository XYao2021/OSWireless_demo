
########################################################
#              Define Objective Function
########################################################
#[[[cog
#   import sys, importlib
#   import cog, __alg_name, __alg_utility, __alg_variable
#   cog.outl("def func(%s, sign=-1.0):"% 'objvar')
#   cog.outl("	utlt = %s"%(__alg_utility.value))
#   cog.outl("	pnl = - sum(%s*(%s - %s))"%(__alg_utility.pnl_sum, __alg_variable.value, __alg_utility.objvarkey))
#   cog.outl("	ovl_utlt = utlt + pnl")
#   cog.outl("	return ovl_utlt")
#]]]
#[[[end]]]

########################################################
#                    Constraints
########################################################
cons = (
{'type': 'ineq',
#[[[cog
#   import cog, __alg_name, __alg_utility, __alg_variable
#   cog.outl("'fun':lambda %s: %s - %s},"%('objvar', 'objvar', __alg_utility.lwrkey))
#   cog.outl("{'type': 'ineq',")
#   cog.outl("'fun':lambda %s: %s - %s})"%('objvar', __alg_utility.uprkey, 'objvar'))
#]]]
#[[[end]]]

########################################################
#                    Optimization
########################################################
def wnos_optimize():
    #[[[cog
    #   import cog
    #   cog.outl("result = minimize(func, %s, constraints=cons, method='SLSQP', options={'disp': False})"%__alg_utility.lwr)
    #]]]
    #[[[end]]]
    return result


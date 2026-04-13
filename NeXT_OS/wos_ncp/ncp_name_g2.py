#######################################################
# Name space for network control problem
#######################################################

# sptd_oprt = ['log', 'add', 'subt', 'mul', 'div', 'sqrt', 'pow', 'exp']
sptd_oprt = ['log', '+', '-', '*', '/', 'sqrt', 'pow', 'exp', '=']

#holding names used by ncp.py here
expr = 'expr'

# type of horizontal id (hid)
primary = 'primary'     # primary hid, defined for network elements
secondary = 'secondary' # secondary hid, defined for constraints and lagrangian coefficients

# Constraints ? AA: 3/8/2020
# gt - greater than
# lt - less than
# eq - equal
# geq - greater than or equal to
# leq - less than or equal to
# how?
#constraints_list = ['geq','leq','eq','gt','lt']

#how to add this
#constraints_type  = ['None','All']
      
    
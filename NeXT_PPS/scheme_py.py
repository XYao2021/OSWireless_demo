def sch():
    scheme_dict = {'1': 'Best Response', '2': 'Power Minimization and Rate Maximization', '3': 'Only Rate Maximization',
                   '4': 'No Optimization - Fixed Rate and Power', '5': 'Only Power Minimization',
                   '6': 'Fixed Rate/Power for "n" time slots and then optimize', '7': 'End-to-End Delay Minimization'}
    print("----------------------------------------------------------")
    print("----------------Existing OpenWiNAR Schemes----------------")
    print("----------------------------------------------------------")
    print("1. Best Response")
    print("2. Power Minimization and Rate Maximization")
    print("3. Only Rate Maximization")
    print("4. No Optimization - Fixed Rate and Power")
    print("5. Only Power Minimization")
    print("6. Fixed Rate/Power for \n time slots and then optimize")
    print("8. End-to-End Delay Minimization")
    print("----------------------------------------------------------")
    scheme = input('Enter your choice: ')
    print("##########################################################")
    print("Chosen NCP is ", scheme_dict[str(scheme)])
    print("##########################################################")
    print("\n\n\n\n")

    return scheme 

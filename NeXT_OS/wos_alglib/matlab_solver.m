% Matlab Solver

function matlab_solver(str_prob)

	% Define problem options
	options = optimoptions('fmincon','Display','iter','Algorithm','sqp')
	problem.options = options
	problem.solver = 'fmincon'
	
	

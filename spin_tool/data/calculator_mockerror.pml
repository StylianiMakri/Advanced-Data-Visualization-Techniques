// reverse polish

#define N 12

mtype = { operator, value }

chan f = [N] of { mtype, int }

proctype calc(chan you)
{	int s, lft, rgt
	chan me = [0] of { int }
 	calc_started: 

	if
	:: f?operator(s)
		run calc(me); me?lft
		run calc(me); me?rgt
		if
		:: s == '+' -> you!(lft+rgt)
		:: s == '-' -> you!(lft-rgt)
		:: s == '*' -> you!(lft*rgt)
		:: s == '/' -> assert(rgt != 0)
			       you!(lft/rgt)
		:: else -> assert(false)
		fi
	:: f?value(s) -> you!s; result_produced: skip
	fi
}

init {
	chan me = [0] of { int }
	int result

	f!operator('+')
	f!operator('/')
	f!value(84)
	f!value(0)
	f!operator('-')
	f!value(36)
	f!operator('*')
	f!value(3)
	f!value(4)

	run calc(me); me?result
	printf("result: %d\n", result)
}   

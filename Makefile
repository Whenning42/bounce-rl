all:
	g++ -m32 -fPIC -shared -o time_intercept.so libc_time_intercepts.cpp -ldl

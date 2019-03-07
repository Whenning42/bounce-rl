all:
	g++ -m32 -fPIC -shared -o time_intercept.so libc_time_intercepts.cpp -ldl
	g++ -m32 -fPIC -shared -o gl_intercept.so gl_passthrough.cpp -ldl

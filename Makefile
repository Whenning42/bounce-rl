all:
	python gl_inject.py
	g++ -m32 -fPIC -shared -o build/time_intercept.so libc_time_intercepts.cpp -ldl
	g++ -m32 -fPIC -shared -o build/gl_intercept.so build/gl_passthrough.cpp -ldl -I./

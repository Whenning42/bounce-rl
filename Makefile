all:
	python gl_inject.py
	g++ -m32 -fPIC -shared -o time_intercept.so libc_time_intercepts.cpp -ldl
	g++ -m32 -fPIC -shared -o gl_intercept.so gl_passthrough.cpp -ldl
	gcc image_capture.c -lX11 -lXext

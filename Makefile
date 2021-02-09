# Note we should be careful about 32 vs 64 bit libraries.

all:
	python gl_inject.py
	g++ -m32 -fPIC -shared -o build/time_intercept.so libc_time_intercepts.cpp -ldl
	g++ -m32 -fPIC -shared -o build/gl_intercept.so build/gl_passthrough.cpp -ldl -I./
	gcc -fPIC -shared -o libimage_capture.so src/image_capture.c -lXext -lX11
	CFLAGS="-I./src" LDFLAGS="-L./" python setup.py build_ext -i

time_intercept:
	g++ -fPIC -shared -o build/time_intercept.so libc_time_intercepts.cpp -ldl
	g++ -m32 -fPIC -shared -o build/time_intercept32.so libc_time_intercepts.cpp -ldl

dlfcn_intercept:
	g++ -fPIC -shared -o build/dlfcn_intercept.so dlfcn_intercept.cpp -ldl

clean:
	rm *.so

erase_memories:
	rm -rf memories/*

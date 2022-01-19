all:
	mkdir -p build
	python gl_inject.py
	g++ -m32 -fPIC -shared -o build/gl_intercept.so build/gl_passthrough.cpp -ldl -I./
	gcc -fPIC -shared -o libimage_capture.so src/image_capture.c -lXext -lX11
	CFLAGS="-I./src" LDFLAGS="-L./" python setup.py build_ext -i

dlfcn_intercept:
	g++ -fPIC -shared -o build/dlfcn_intercept.so dlfcn_intercept.cpp -ldl

console:
	g++ -o build/console.bin src/console/console.cpp -lreadline

clean:
	rm *.so

erase_memories:
	rm -rf memories/*

vd:
	g++ -Wall -shared -std=c++11 -fPIC $$(python3 -m pybind11 --includes) bind_virtual_device.cpp virtual_device.cpp -lX11 -lXi -lXtst -o UserKeyboard$$(python3-config --extension-suffix)

lib_mpx_input:
	gcc -fPIC -shared -o lib_mpx_input.so lib_mpx_input.c -lX11 -lXi -lXtst


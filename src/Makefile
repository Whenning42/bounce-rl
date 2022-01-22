all:
	gcc -g3 -c runner.c image_capture.c
	gcc -g3 image_capture.o runner.o -lX11 -lXext -o runner
	gcc -g3 focus.c -o focus -lX11

time_control:
	g++ -g3 -fPIC -shared -march=native -o ../build/time_control.so time_control.cpp -ldl -latomic
	g++ -g3 -m32 -fPIC -shared -march=native -o ../build/time_control32.so time_control.cpp -ldl -latomic

time_control_test:
	g++ -g3 -o ../build/time_control_test time_control_test.cpp time_control.cpp -ldl -lgtest_main -lgtest -latomic
	../build/time_control_test

time_writier_test:
	g++ child.cpp
	python time_writer.py

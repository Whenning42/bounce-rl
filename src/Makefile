all: time_control time_control_test time_writer_test

time_control:
	g++ -pthread -std=c++17 -fPIC -shared -march=native -o ../build/time_control.so time_control.cpp -ldl -latomic
	g++ -pthread -std=c++17 -m32 -fPIC -shared -march=native -o ../build/time_control32.so time_control.cpp -ldl -latomic

time_control_test:
	g++ -pthread -std=c++17 -g3 -o ../build/time_control_test time_control_test.cpp time_control.cpp -ldl -lgtest_main -lgtest -latomic
	../build/time_control_test

time_writer_test: time_control
	g++ child.cpp
	python time_writer.py

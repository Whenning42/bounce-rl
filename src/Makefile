all: time_control time_control_test time_writer_test

clean:
	rm ../build/*

time_control:
	g++ -pthread -std=c++17 -fPIC -shared -march=native -o ../build/libtime_control.so time_control.cpp -ldl -latomic
	g++ -pthread -std=c++17 -m32 -fPIC -shared -march=native -o ../build/libtime_control32.so time_control.cpp -ldl -latomic
	g++ -pthread -std=c++17 -fPIC -shared -march=native -DDLSYM_OVERRIDE -o ../build/libtime_control_dlsym.so time_control.cpp -ldl -latomic
	g++ -pthread -std=c++17 -m32 -fPIC -shared -march=native -DDLSYM_OVERRIDE -o ../build/libtime_control_dlsym32.so time_control.cpp -ldl -latomic

install_time_control: time_control
	sudo cp ../build/libtime_control.so /usr/lib/libtime_control.so
	sudo cp ../build/libtime_control32.so /usr/lib32/libtime_control.so
	sudo cp ../build/libtime_control_dlsym.so /usr/lib/libtime_control_dlsym.so
	sudo cp ../build/libtime_control_dlsym32.so /usr/lib32/libtime_control_dlsym.so

time_control_test:
	g++ -pthread -std=c++17 -g3 -o ../build/time_control_test time_control_test.cpp time_control.cpp -ldl -lgtest_main -lgtest -latomic
	../build/time_control_test

time_writer_test: time_control
	g++ child.cpp
	python time_writer.py

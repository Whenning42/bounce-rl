all:
	glslangValidator fill_buffer.comp -V -o comp.spv
	g++ -g3 main.cc -lvulkan -ldl

write:
	g++ -g3 write_values.cc -o write.out
	g++ -g3 write_values_full.cc -o full.out

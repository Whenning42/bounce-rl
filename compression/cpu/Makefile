all:
	clang++ -O3 -march=native comp.cc lodepng.cc -std=c++17 -o comp.out

debug:
	clang++ -g3 comp.cc lodepng.cc -std=c++17 -o comp.out

gcc:
	g++ -O3 comp.cc lodepng.cc -std=c++17 -o comp.out

benchmark:
	clang++ -O3 -march=native coded_buffer_benchmark.cc coded_buffer.cc -o coded_buffer_benchmark.out
	clang++ -O3 -march=native fast_map_benchmark.cc -o fast_map_benchmark.out

bench_asm:
	clang++ -O3 -march=native -g coded_buffer_benchmark.cc coded_buffer.cc -o coded_buffer_benchmark.out
	clang++ -O3 -march=native -g fast_map_benchmark.cc -o fast_map_benchmark.out

all:
	gcc -g3 -c runner.c image_capture.c
	gcc -g3 image_capture.o runner.o -lX11 -lXext -o runner
	gcc -g3 focus.c -o focus -lX11

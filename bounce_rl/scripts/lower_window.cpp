// A utility for lowering X11 windows.

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <window_id>\n", argv[0]);
        return 1;
    }

    Display *display = XOpenDisplay(NULL);
    if (!display) {
        fprintf(stderr, "Cannot open display\n");
        return 1;
    }

    Window root = DefaultRootWindow(display);
    int screen = DefaultScreen(display);

    Window target_win = (Window)strtoul(argv[1], NULL, 0);
    XLowerWindow(display, target_win);
    XFlush(display);
    return 0;
}

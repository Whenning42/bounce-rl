// Mirrors the target X11 window's pixel contents to a new window.
// Allows for visual inspection of offscreen window contents.

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <X11/extensions/Xcomposite.h>

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

    XWindowAttributes source_attrs;
    if (!XGetWindowAttributes(display, target_win, &source_attrs)) {
        fprintf(stderr, "Cannot get window attributes\n");
        XCloseDisplay(display);
        return 1;
    }

    Window mirror_win = XCreateSimpleWindow(display, root, 
                                               0, 0, 
                                               source_attrs.width, source_attrs.height,
                                               1, BlackPixel(display, screen), WhitePixel(display, screen));
    XMapWindow(display, mirror_win);

    GC gc = DefaultGC(display, screen);
    Pixmap target_pxm = XCompositeNameWindowPixmap(display, target_win);
    while (1) {
        XCopyArea(display, target_pxm, mirror_win, gc,
                    0, 0, source_attrs.width, source_attrs.height, 0, 0);
        XFlush(display);
        usleep(16000);
    }
    return 0;
}

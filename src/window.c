#include <X11/X.h>
#include <X11/Xlib.h>

int get_x(Display* display, Window window) {
    XWindowAttributes attributes;
    XGetWindowAttributes(display, window, &attributes);
    return attributes.x;
}

int get_y(Display* display, Window window) {
    XWindowAttributes attributes;
    XGetWindowAttributes(display, window, &attributes);
    return attributes.y;
}



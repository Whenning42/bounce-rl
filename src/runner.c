#include "image_capture.h"
#include <X11/Xlib.h>

#include <stdio.h>

int main(int argc, char **argv) {
    capture_t capture = SetupImageCapture(640, 480);
    unsigned char* val = CaptureImage(capture, DefaultRootWindow(XOpenDisplay(NULL)));
    for(int i=0; i<9; ++i) {
        printf("%u\n", val[i]);
    }
    CleanupImageCapture(capture);
    return 0;
}

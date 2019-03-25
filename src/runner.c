#include "image_capture.h"

#include <stdio.h>

int main(int argc, char **argv) {
    capture_t capture = SetupImageCapture(640, 480);
    unsigned char* val = CaptureImage(capture, 0, 0);
    for(int i=0; i<9; ++i) {
        printf("%u\n", val[i]);
    }
    CleanupImageCapture(capture);
    return 0;
}

// To investigate events not happening on ubuntu X11, we can use three tests:
// 1. Look at xtrace output to see if input events are being sent to the client
// 2. Run a debug app that queries the server via XIGetClientPointer to check the
//    target app's state
// 3. Run a test app that maps a window and then prints its client pointer state and
//    received events.

// This program implements a repl for 2.

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>

#include <X11/Xlib.h>
#include <X11/extensions/XInput2.h>

int main(int argc, char** argv) {
    int window_id = 0;
    Display* display = XOpenDisplay(NULL);

    if (strcmp(argv[1], "get-client-pointer") == 0) {
        if (argc != 3) {
            printf("Usage: %s get-client-pointer <window_id>\n", argv[0]);
            return 1;
        }
        window_id = atoi(argv[2]);

        int device_id = 0;
        XIGetClientPointer(display, window_id, &device_id);
        printf("Client pointer: %d\n", device_id);
    } else if (strcmp(argv[1], "raise-window") == 0) {
        if (argc != 3) {
            printf("Usage: %s raise-window <window_id>\n", argv[0]);
            return 1;
        }
        window_id = atoi(argv[2]);

        XRaiseWindow(display, window_id);
    } else if (strcmp(argv[1], "lower-window") == 0) {
        if (argc != 3) {
            printf("Usage: %s lower-window <window_id>\n", argv[0]);
            return 1;
        }
        window_id = atoi(argv[2]);

        XLowerWindow(display, window_id);
    } else if (strcmp(argv[1], "move-window") == 0) {
        if (argc != 5) {
            printf("Usage: %s move-window <window_id> <x> <y>\n", argv[0]);
            return 1;
        }
        window_id = atoi(argv[2]);
        int x = atoi(argv[3]);
        int y = atoi(argv[4]);

        XMoveWindow(display, window_id, x, y);
    } else {
        printf("Unknown command: %s\n", argv[1]);
        return 1;
    }
}

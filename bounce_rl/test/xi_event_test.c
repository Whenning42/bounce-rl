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
#include <readline/readline.h>
#include <readline/history.h>

#include <X11/Xlib.h>
#include <X11/extensions/XInput2.h>

int x_error_handler(Display* display, XErrorEvent* error_event) {
    char error_text[1024];
    XGetErrorText(display, error_event->error_code, error_text, sizeof(error_text));
    printf("X11 Error: %s\n", error_text);
    printf("Request code: %d, Minor code: %d\n", error_event->request_code, error_event->minor_code);
    return 0;
}

int main(int argc, char** argv) {
    int window_id = 0;
    Display* display = XOpenDisplay(NULL);
    XSetErrorHandler(x_error_handler);

    rl_initialize();
    using_history();
    while (true) {
        char* command = readline("Enter command: ");
        printf("Received: %s\n", command);
        add_history(command);

        if (strncmp(command, "set-window", 10) == 0) {
            int read = sscanf(command, "set-window %i", &window_id);
            if (read != 1) {
                printf("Failed to read window id: %s\n", command + 11);
                continue;
            }
            printf("Window set to: %d\n", window_id);
        }
        else if (strncmp(command, "get-client-pointer", 18) == 0) {
            int device_id = 0;
            XIGetClientPointer(display, window_id, &device_id);
            printf("Client pointer: %d\n", device_id);
        } else {
            printf("Unknown command: %s\n", command);
        }
        free(command);
    }
}

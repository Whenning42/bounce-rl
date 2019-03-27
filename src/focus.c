#include <X11/X.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <assert.h>

const char* to_focus = "Sky Rogue";

void AppendChildrenWindows(Display* display, Window** window_list, int* window_count, Window window) {
    Window root;
    Window parent;
    Window* child_list;
    unsigned int num_children;
    XQueryTree(display, window, &root, &parent, &child_list, &num_children);
    if(num_children) {
        *window_list = realloc(*window_list, sizeof(Window) * (*window_count + num_children));
        assert(*window_list);

        for(int i=0; i<num_children; ++i) {
            (*window_list)[*window_count + i] = child_list[i];
        }
        *window_count += num_children;

        for (int i=0; i<num_children; ++i) {
            AppendChildrenWindows(display, window_list, window_count, child_list[i]);
        }
    }
}

Window* GetAllWindows(Display* display, int* count) {
    Window root = DefaultRootWindow(display);
    Window* windows = NULL;

    AppendChildrenWindows(display, &windows, count, root);
    return windows;
}

Window* GetAllWindowsWithName(Display* display, const char* name, int* count) {
    int num_windows = 0;
    Window* all_windows = GetAllWindows(display, &num_windows);
    Window* matching_windows = malloc(sizeof(Window) * num_windows);

    char* window_name;
    int num_matching_windows = 0;
    *count = 0;
    for(int w=0; w<num_windows; ++w) {
        XFetchName(display, all_windows[w], &window_name);
        if(window_name && !strcmp(window_name, name)) {
            matching_windows[*count] = all_windows[w];
            (*count)++;
        }
        XFree(window_name);
    }
    free(all_windows);

    matching_windows = realloc(matching_windows, sizeof(Window) * *count);
    if(*count > 0) {
        assert(matching_windows);
    }
    printf("Focused %d windows named: %s\n", *count, name);
    return matching_windows;
}

#include "image_capture.h"
int main(int argc, char** argv) {
    Display *display = XOpenDisplay(NULL);

    int num_windows;
    Window* windows = GetAllWindowsWithName(display, to_focus, &num_windows);

    capture_t c = SetupImageCapture(1, 1);
    for(int w = 0; w < num_windows; ++w) {
        FocusAndIgnoreAllEvents(c, windows[w]);
    }

    XFlush(display);
    free(windows);
}

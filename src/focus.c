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

int main(int argc, char** argv) {
    Display *display = XOpenDisplay(NULL);

    int num_windows;
    Window* windows = GetAllWindowsWithName(display, to_focus, &num_windows);

    int num_details = 8;
    int details[] = {NotifyAncestor, NotifyVirtual, NotifyInferior, NotifyNonlinear, NotifyNonlinearVirtual, NotifyPointer, NotifyPointerRoot, NotifyDetailNone};

    int num_modes = 3;
    int modes[] = {NotifyNormal, NotifyGrab, NotifyUngrab};

    // Sends the focus in event
    for(int i = 0; i < num_details; ++i) {
        for(int w = 0; w < num_windows; ++w) {
            XEvent focus_in;
            focus_in.type = FocusIn;
            focus_in.xfocus.display = display;
            focus_in.xfocus.window = windows[w];
            focus_in.xfocus.mode = NotifyNormal;
            focus_in.xfocus.detail = details[i];
            assert(XSendEvent(display, windows[w], /*propagate=*/True, FocusChangeMask/*?*/, &focus_in));

            int tile_x = 3;
            int x = w%tile_x;
            int y = w/tile_x;
            XMoveWindow(display, windows[w], 640*x, 480*y);
        }
    }

    XFlush(display);
    free(windows);
}

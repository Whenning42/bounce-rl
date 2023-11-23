#include <stdbool.h>
#include <X11/Xlib.h>

Display* open_display(char* display_name);
void make_cursor(Display* display, char* cursor_name);
void assign_cursor(Display* display, Window client_connection_window, char* cursor_name);
void delete_cursor(Display* display, char* cursor);

void key_event(Display* display, unsigned int keycode, bool is_press);
void move_mouse(Display* display, int x, int y);
void button_event(Display* display, unsigned int button, bool is_press);

void xflush(Display* display);
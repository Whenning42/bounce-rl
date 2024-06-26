import os

from cffi import FFI

from bounce_rl.utilities.paths import project_root


def cursor_name(instance: int):
    return f"mpx_cursor_{instance}"


def make_lib_mpx_input():
    """Create the lib_mpx_input library and return its FFI instance."""
    mpx_input_ffi = FFI()
    mpx_input_ffi.cdef(
        """
        typedef ... Display;
        typedef long Window;

        Display* open_display(char* display_name);
        void close_display(Display* display);

        void make_cursor(Display* display, char* cursor_name);
        void assign_cursor(Display* display, Window client_connection_window, char* cursor_name);
        void delete_cursor(Display* display, char* cursor);

        void key_event(Display* display, unsigned int keycode, bool is_press);
        void move_mouse(Display* display, int x, int y);
        void button_event(Display* display, unsigned int button, bool is_press);

        void xflush(Display* display);
    """
    )
    libmpx_path = os.path.join(
        project_root(), "bounce_rl/core/keyboard/libmpx_input.so"
    )
    return (
        mpx_input_ffi.dlopen(libmpx_path),
        mpx_input_ffi,
    )

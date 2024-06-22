#include <iostream>
#include <string>
#include <unistd.h>
#include <cstring>
#include <sys/time.h>

#include <X11/Xlib.h>
#include <X11/extensions/XInput2.h>
#include <X11/keysym.h>

int main(int argc, char **argv) {
    if (argc != 2)
    {
        std::cerr << "Usage: " << argv[0] << " <window_id>" << std::endl;
        return 1;
    }

    Display *display = XOpenDisplay(NULL);
    Window window = std::stoi(argv[1], nullptr, 16);

    Window root;
    Window child;
    int root_x;
    int root_y;
    int win_x;
    int win_y;
    unsigned int mask;
    XQueryPointer(display, window, &root, &child, &root_x, &root_y, &win_x, &win_y, &mask);

    std::cout << "XQueryPointerResult: " << std::endl;
    std::cout << std::hex;
    std::cout << "Root: 0x" << root << std::endl;
    std::cout << "Child: 0x" << child << std::endl;
    std::cout << std::dec;
    std::cout << "Root X: " << root_x << std::endl;
    std::cout << "Root Y: " << root_y << std::endl;
    std::cout << "Win X: " << win_x << std::endl;
    std::cout << "Win Y: " << win_y << std::endl;
    std::cout << "Mask: " << mask << std::endl;
}


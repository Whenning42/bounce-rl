#include <array>
#include <atomic>
#include <cstdint>
#include <string>
#include <thread>

const std::string kKeyboardRegex = "AT Translated";

// For internal use only.
struct Devices {
  int master_pointer;
  int master_keyboard;
  int device_keyboard;
};

class UserKeyboard {
  public:
    UserKeyboard();
    ~UserKeyboard();
    void Disable();
    void Enable();

    // Owned by the main loop.
    const std::array<uint8_t, 256>& KeyState();

  private:
    void StartLoop();

    std::thread loop_;
    Devices devices_;
    bool disabled_ = false;
    std::atomic<bool> running_ = true;
};

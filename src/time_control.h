#include <cstdint>
#include <time.h>
#include <ostream>

void __set_speedup(float speedup);
void __sleep_for_nanos(uint64_t nanos);
void __real_clock_gettime(int clkid, timespec* t);

// Exposed to ease testing.
float get_speedup();
timespec operator*(const timespec& t, double f);
timespec operator-(const timespec& t1, const timespec& t0);
std::ostream& operator<<(std::ostream& o, const timespec& t);

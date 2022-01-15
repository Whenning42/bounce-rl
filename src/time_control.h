#include <cstdint>
#include <time.h>

void __set_speedup(float speedup);
void __sleep_for_nanos(uint64_t nanos);
void __real_clock_gettime(int clkid, timespec* t);

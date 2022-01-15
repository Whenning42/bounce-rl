#include <gtest/gtest.h>

// Test should be run with LD_PRELOAD set to the time_control .so.

const int kBillion = 1000000000;

TEST(TimeControl, TimeSpeedup) {
  time_t start_time = time(nullptr);
  __set_speedup(30);
  __real_nanosleep(kBillion);
  time_t end_time = time(nullptr);
  time_t delta = start_time - end_time;

  // Timing and rounding might make the time delta a little different than expected.
  EXPECT_LE(delta, 31);
  EXPECT_GE(delta, 29);
}

TEST(TimeControl, TimeSlowdown) {
  time_t start_time = time(nullptr);
  __set_speedup(.5);
  __real_nanosleep(6 * kBillion);
  time_t end_time = time(nullptr);
  time_t delta = start_time - end_time;

  // Timing and rounding might make the time delta a little different than expected.
  EXPECT_LE(delta, 4);
  EXPECT_GE(delta, 2);
}

#include <gtest/gtest.h>

#include "time_control.h"

const int64_t kMillion = 1000000;
const int64_t kBillion = 1000000000;

double timespec_to_sec(timespec t) {
  return t.tv_sec + (double)(t.tv_nsec) / kBillion;
}

TEST(TimeControl, Time) {
  __set_speedup(30);

  time_t start_time = time(nullptr);
  __sleep_for_nanos(kBillion);
  time_t end_time = time(nullptr);
  time_t delta = end_time - start_time;

  // Timing and rounding might make the time delta a little different than expected.
  EXPECT_LE(delta, 31);
  EXPECT_GE(delta, 29);
}

TEST(TimeControl, ClockGettime) {
  __set_speedup(3);
  timespec start, end;

  clock_gettime(CLOCK_REALTIME, &start);
  __sleep_for_nanos(kBillion);
  clock_gettime(CLOCK_REALTIME, &end);

  EXPECT_NEAR(timespec_to_sec(end - start), 3, .01);
}

TEST(TimeControl, ClockGettimeSubsecond) {
  __set_speedup(2);
  timespec start, end;

  clock_gettime(CLOCK_REALTIME, &start);
  __sleep_for_nanos(.1 * kBillion);
  clock_gettime(CLOCK_REALTIME, &end);

  EXPECT_NEAR(timespec_to_sec(end - start), .2, .01);
}

TEST(TimeControl, ClockGettimeWallClocks) {
  timespec start, end, end2;
  const std::vector<int> wall_clocks = {CLOCK_REALTIME, CLOCK_MONOTONIC,
    CLOCK_MONOTONIC_RAW, CLOCK_REALTIME_COARSE, CLOCK_MONOTONIC_COARSE,
    CLOCK_BOOTTIME, CLOCK_REALTIME_ALARM, CLOCK_BOOTTIME_ALARM
  };

  for (int clock : wall_clocks) {
    __set_speedup(2);

    clock_gettime(clock, &start);
    __sleep_for_nanos(.1 * kBillion);
    clock_gettime(clock, &end);

    __set_speedup(3);
    clock_gettime(clock, &end2);
    EXPECT_NEAR(timespec_to_sec(end - start), .2, .01);
    EXPECT_NEAR(timespec_to_sec(end2 - end), 0, .01);
  }
}
// Clock measures process time, not wall time.

TEST(TimeControl, Clock) {
  int acc = 0;
  clock_t start_1, end_1, start_2, end_2;

  __set_speedup(1);
  start_1 = clock();
  for (int i = 0; i < .5 * kBillion; ++i) {
    acc += i * 57 + 3;
  }
  end_1 = clock();

  __set_speedup(10);
  start_2 = clock();
  for (int i = 0; i < .5 * kBillion; ++i) {
    acc += i * 57 + 3;
  }
  end_2 = clock();

  double time_1 = (double)(end_1 - start_1) / CLOCKS_PER_SEC;
  double time_2 = (double)(end_2 - start_2) / CLOCKS_PER_SEC;
  // For some reason the error here tends to be large.
  EXPECT_NEAR(time_2 / time_1, 10, 5);
}

// The sleep functions are no longer implemented, but could be in the future.
// Uncomment these tests if re-implemented.
TEST(TimeControl, Nanosleep) {
  timespec sleep;
  sleep.tv_sec = 4;
  sleep.tv_nsec = 0;
  __set_speedup(4);

  timespec start, end;

  __real_clock_gettime(CLOCK_REALTIME, &start);
  nanosleep(&sleep, nullptr);
  __real_clock_gettime(CLOCK_REALTIME, &end);

  EXPECT_NEAR(timespec_to_sec(end - start), 1, .01);
}

TEST(TimeControl, Usleep) {
  __set_speedup(2);
  timespec start, end;

  __real_clock_gettime(CLOCK_REALTIME, &start);
  usleep(2 * kMillion);
  __real_clock_gettime(CLOCK_REALTIME, &end);

  EXPECT_NEAR(timespec_to_sec(end - start), 1, .01);
}

TEST(TimeControl, Sleep) {
  __set_speedup(10);
  timespec start, end;

  __real_clock_gettime(CLOCK_REALTIME, &start);
  sleep(10);
  __real_clock_gettime(CLOCK_REALTIME, &end);

  EXPECT_NEAR(timespec_to_sec(end - start), 1, .01);
}

TEST(TimeControl, MulOperator) {
  timespec t_1_5;
  t_1_5.tv_sec = 1;
  t_1_5.tv_nsec = 500 * kMillion;

  EXPECT_EQ(((t_1_5) * 4.0).tv_sec, 6);
  EXPECT_EQ(((t_1_5) * 4.0).tv_nsec, 0);
}

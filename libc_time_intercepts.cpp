#include <cassert>
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <iostream>
#include <utime.h>
#include <time.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <semaphore.h>
#include <math.h>

const char* FIFO = "/tmp/time_control";

// Intercepted functions
// - time
// - gettimeofday
// - clock_gettime
// - clock
// - nanosleep
// - usleep
// - sleep
// - clock_nanosleep
// x pthread_cond_timedwait
// x sem_timedwait

// A helper macro that takes in a function name "func" and declares a
// pointer type "PFN_func" of that function;s type.
#define PFN_TYPEDEF(func) typedef decltype(&func) PFN_##func

// A helper macro that takes in a function name "func" and dlsym loads the
// function if it's global value is nullptr. This requires real_func to be
// declared globally.
#define LAZY_LOAD_REAL(func) if(!real_##func) { \
    real_##func = (PFN_##func)dlsym(RTLD_NEXT, #func); \
}

PFN_TYPEDEF(time);
PFN_TYPEDEF(gettimeofday);
PFN_TYPEDEF(clock_gettime);
PFN_TYPEDEF(clock);
PFN_TYPEDEF(nanosleep);
PFN_TYPEDEF(usleep);
PFN_TYPEDEF(sleep);
PFN_TYPEDEF(clock_nanosleep);

// Global
PFN_time real_time = nullptr;
PFN_gettimeofday real_gettimeofday = nullptr;
PFN_clock_gettime real_clock_gettime = nullptr;
PFN_clock real_clock = nullptr;
PFN_nanosleep real_nanosleep = nullptr;
PFN_usleep real_usleep = nullptr;
PFN_sleep real_sleep = nullptr;
PFN_clock_nanosleep real_clock_nanosleep = nullptr;

const int MILLION = 1e6;
const int BILLION = 1e9;

float speedup = 5;
int speed_file = 0;

struct timespec clock_origin_real[4];
struct timespec clock_origin_fake[4];

// Helpers functions.
namespace {

int base_clock(int clkid) {
  switch (clkid) {
    case CLOCK_REALTIME:
      return CLOCK_REALTIME;
    case CLOCK_MONOTONIC:
      return CLOCK_MONOTONIC;
    case CLOCK_PROCESS_CPUTIME_ID:
      return CLOCK_PROCESS_CPUTIME_ID;
    case CLOCK_THREAD_CPUTIME_ID:
      return CLOCK_THREAD_CPUTIME_ID;
    case CLOCK_MONOTONIC_RAW:
      return CLOCK_MONOTONIC;
    case CLOCK_REALTIME_COARSE:
      return CLOCK_REALTIME;
    case CLOCK_MONOTONIC_COARSE:
      return CLOCK_MONOTONIC;
    case CLOCK_BOOTTIME:
      return CLOCK_MONOTONIC;
    case CLOCK_REALTIME_ALARM:
      return CLOCK_REALTIME;
    case CLOCK_BOOTTIME_ALARM:
      return CLOCK_MONOTONIC;
    default:
      return -1;
  }
}

void speed_update(float new_speed) {
  for (int clock = 0; clock < CLOCKS; clock++) {
    real_clock_gettime(clock, &clock_origins[clock]);
  }
  speedup = new_speed;
}

void try_speed_update() {
  if (!speed_file) {
    speed_file = open(FIFO, O_RDONLY | O_NONBLOCK);
    if (!speed_file) {
      printf("Failed to open fifo.\n");
    }
  }

  char buf[64];
  ssize_t read_num = read(speed_file, &buf, 64);
  if (read_num > 0) {
    speedup = *(buf + read_num - 4);
    speed_update(speedup);
    printf("Changing speed-up to: %f\n", speedup);
  }
}

timespec fake_time(int clock) {
  timespec real;
  real_clock_gettime(clock, &real);
  timespec real_delta = real - clock_origin_real[clock];
  return clock_origin_fake[clock] + real_delta * speedup;
}

time_t time(time_t* arg) {
  struct timespec tp = fake_time(CLOCK_REALTIME);
  return tp.tv_sec;
}

int gettimeofday(struct timeval *tv, struct timezone *tz) {
  LAZY_LOAD_REAL(gettimeofday);
  int out = real_gettimeofday(tv, tz);
  *tv = speedup_timeval(*tv);
  return out;
}

// tm* localtime(const time_t *timep) {
//   LAZY_LOAD_REAL(localtime);
//   time_t t = speedup_time_t(*timep);
//   return real_localtime(&t);
// }
// 
// tm* localtime_r(const time_t* timep, struct tm* result) {
//   LAZY_LOAD_REAL(localtime_r);
//   time_t t = speedup_time_t(*timep);
//   return real_localtime_r(&t, result);
// }
// 
// tm* gmtime(const time_t *timep) {
//   LAZY_LOAD_REAL(gmtime);
//   time_t t = speedup_time_t(*timep);
//   return real_gmtime(&t);
// }
// 
// tm* gmtime_r(const time_t* timep, struct tm* result) {
//   LAZY_LOAD_REAL(gmtime_r);
//   time_t t = speedup_time_t(*timep);
//   return real_gmtime_r(&t, result);
// }
//
int clock_gettime(clockid_t clk_id, struct timespec *tp) {
  LAZY_LOAD_REAL(clock_gettime);
  int out = real_clock_gettime(clk_id, tp);
  *tp = speedup_timespec(*tp);
  return out;
}
// 
// double difftime(time_t t1, time_t t0) {
//   LAZY_LOAD_REAL(difftime);
//   return speedup * real_difftime(t1, t0);
// }

int pthread_cond_timedwait(pthread_cond_t *cond, pthread_mutex_t *mutex, const struct timespec *abstime) {
  LAZY_LOAD_REAL(pthread_cond_timedwait);
  return real_pthread_cond_timedwait(cond, mutex, abstime);
}

int sem_timedwait(sem_t *sem, const struct timespec *abs_timeout) {
  LAZY_LOAD_REAL(sem_timedwait);
  return real_sem_timedwait(sem, abs_timeout);
}
 
// time_t mktime(struct tm *tm) {
//   LAZY_LOAD_REAL(mktime);
//   time_t out = real_mktime(tm);
//   return speedup_time_t(out);
// }

clock_t clock() {
  LAZY_LOAD_REAL(clock);
  return speedup * real_clock();
}



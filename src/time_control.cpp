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
#include <mutex>
#include <atomic>

const char* FIFO = "/tmp/time_control";
const int NUM_CLOCKS = 4;

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
std::atomic<PFN_time> real_time = nullptr;
std::atomic<PFN_gettimeofday> real_gettimeofday = nullptr;
std::atomic<PFN_clock_gettime> real_clock_gettime = nullptr;
std::atomic<PFN_clock> real_clock = nullptr;
std::atomic<PFN_nanosleep> real_nanosleep = nullptr;
std::atomic<PFN_usleep> real_usleep = nullptr;
std::atomic<PFN_sleep> real_sleep = nullptr;
std::atomic<PFN_clock_nanosleep> real_clock_nanosleep = nullptr;

const int MILLION = 1000000;
const int BILLION = 1000000000;

std::mutex update_mutex;
int speed_file = 0; // guarded by update_mutex.
bool clock_init = false; // guarded by update_mutex.

int test_update = 0;
float new_speedup = 0;

struct ClockState {
  float speedup;
  timespec clock_origins_real[4];
  timespec clock_origins_fake[4];
};
std::atomic<ClockState> global_clock_state;

float get_speedup() {
  return global_clock_state.load().speedup;
}

timespec operator-(const timespec& t1, const timespec& t0) {
  timespec out;
  int64_t sec_delta = t1.tv_sec - t0.tv_sec;
  int64_t nsec_delta = t1.tv_nsec - t0.tv_nsec;
  if (nsec_delta > BILLION) {
    sec_delta += 1;
    nsec_delta -= BILLION;
  } else if (nsec_delta < 0) {
    sec_delta -= 1;
    nsec_delta += BILLION;
  }
  out.tv_sec = sec_delta;
  out.tv_nsec = nsec_delta;
  return out;
}

std::ostream& operator<<(std::ostream& o, const timespec& t) {
  o << "tv_sec: " << t.tv_sec << " " << "tv_nsec: " << t.tv_nsec;
  return o;
}

// Helpers functions.
namespace {

// To reduce to number of clocks we have to fetch each time we change our speedup,
// we only use a few real clocks, and redirect calls for the other clock, to this
// set of base clocks (REALTIME, MONOTONIC, PROCESS_CPUTIME_ID, THREAD_CPUTIME_ID).
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

timespec operator+(const timespec& t1, const timespec& t0) {
  timespec neg_t0;
  neg_t0.tv_sec = -t0.tv_sec;
  neg_t0.tv_nsec = -t0.tv_nsec;
  return t1 - neg_t0;
}

timespec operator*(const timespec& t, double s) {
  timespec out;

  double s_sec = t.tv_sec * s;
  double s_nsec = t.tv_nsec * s;

  int64_t s_sec_int = s_sec;
  double s_sec_dec = s_sec - s_sec_int;
  int64_t s_nsec_int = s_nsec + BILLION * s_sec_dec;

  if (s_nsec_int > BILLION) {
    s_sec_int += 1;
    s_nsec_int -= BILLION;
  } else if (s_nsec_int < 0) {
    s_sec_int -= 1;
    s_nsec_int += BILLION;
  }

  out.tv_sec = s_sec_int;
  out.tv_nsec = s_nsec_int;
  return out;
}

timespec operator/(const timespec& t, double s) {
  return t * (1 / s);
}

timespec fake_time_impl(int clock) {
  LAZY_LOAD_REAL(clock_gettime);
  clock = base_clock(clock);
  timespec real;
  real_clock_gettime(clock, &real);
  ClockState clock_state = global_clock_state;
  timespec real_delta = real - clock_state.clock_origins_real[clock];
  return clock_state.clock_origins_fake[clock] + real_delta * clock_state.speedup;
}

void update_speedup(float new_speed) {
  ClockState new_state;
  new_state.speedup = new_speed;
  for (int clock = 0; clock < NUM_CLOCKS; clock++) {
    if (clock_init) {
      timespec fake = fake_time_impl(clock);
      real_clock_gettime(clock, &new_state.clock_origins_real[clock]);
      new_state.clock_origins_fake[clock] = fake;
    } else {
      LAZY_LOAD_REAL(clock_gettime);
      real_clock_gettime(clock, &new_state.clock_origins_real[clock]);
      real_clock_gettime(clock, &new_state.clock_origins_fake[clock]);
      clock_init = true;
    }
  }
  global_clock_state = new_state;
  // printf("New speed: %f\n", global_clock_state.load().speedup);
}

void try_updating_speedup() {
  if (!update_mutex.try_lock()) {
    return;
  }

  if (!speed_file) {
    // printf("Opening speed file.\n");
    speed_file = open(FIFO, O_RDONLY | O_NONBLOCK);
    if (!speed_file) {
      return;
    }
  } else {
    // printf("Speed file is open.\n");
  }

  bool should_change_speed = false;
  float changed_speed = 0;;

  if (test_update) {
    changed_speed = new_speedup;
    test_update = 0;
    should_change_speed = true;
  }

  char buf[64];
  ssize_t read_num = read(speed_file, &buf, 64);
  // printf("Read %d bytes.\n", read_num);
  if (read_num > 0) {
    // printf("Reading float at offset: %d\n", read_num - 4);
    changed_speed = *(float*)(buf + read_num - 4);
    should_change_speed = true;
  } else {
    // printf("Leaving speedup at: %f\n", global_clock_state.load().speedup);
  }

  if (should_change_speed) {
    // printf("Changing speed to: %f\n", changed_speed);
    update_speedup(changed_speed);
  }

  update_mutex.unlock();
}

timespec fake_time(int clock) {
  try_updating_speedup();
  return fake_time_impl(clock);
}
}  // namespace

time_t time(time_t* arg) {
  timespec tp = fake_time(CLOCK_REALTIME);
  return tp.tv_sec;
}

int gettimeofday(struct timeval *tv, struct timezone *tz) {
  timespec tp = fake_time(CLOCK_REALTIME);
  tv->tv_sec = tp.tv_sec;
  tv->tv_usec = tp.tv_nsec / 1000;
  return 0;
}

int clock_gettime(clockid_t clk_id, struct timespec *tp) {
  *tp = fake_time(clk_id);
  return 0;
}

clock_t clock() {
  timespec tp = fake_time(CLOCK_PROCESS_CPUTIME_ID);
  return (tp.tv_sec + (double)(tp.tv_nsec) / BILLION) * CLOCKS_PER_SEC;
}

// NOTE: The error semantics for the sleep family of functions isn't preserved in these wrappers.
int nanosleep(const struct timespec* req, struct timespec* rem) {
  try_updating_speedup();
  LAZY_LOAD_REAL(nanosleep);
//  float speedup = global_clock_state.load().speedup;
  float speedup = 1;
  timespec goal_req = *req / speedup;
  timespec goal_rem;
  int ret = real_nanosleep(&goal_req, &goal_rem);
  if (rem) {
    *rem = goal_rem * speedup;
  }
  return ret;
}

int usleep(useconds_t usec) {
  timespec orig_nanosleep;
  orig_nanosleep.tv_sec = usec / MILLION;
  orig_nanosleep.tv_nsec = (uint64_t)(usec * 1000) % BILLION;
  // Time speedup happens in the call to our override nanosleep.
  nanosleep(&orig_nanosleep, nullptr);
  return 0;
}

unsigned int sleep(unsigned int seconds) {
  LAZY_LOAD_REAL(nanosleep);
  timespec sleep;
  sleep.tv_sec = seconds;
  sleep.tv_nsec = 0;
  nanosleep(&sleep, nullptr);
  return 0;
}

int clock_nanosleep(clockid_t clockid, int flags, const struct timespec* request, struct timespec* remain) {
  LAZY_LOAD_REAL(clock_nanosleep);
  float speedup = global_clock_state.load().speedup;
  timespec goal_req = *request;
  // timespec goal_req = *request / speedup;
  timespec goal_rem;
  int ret = real_clock_nanosleep(clockid, flags, &goal_req, &goal_rem);
  *remain = goal_rem * speedup;
  return ret;
}

void __set_speedup(float speedup) {
  test_update = 1;
  new_speedup = speedup;
}

void __sleep_for_nanos(uint64_t nanos) {
  LAZY_LOAD_REAL(nanosleep);
  timespec n;
  n.tv_sec = nanos / BILLION;
  n.tv_nsec = nanos % BILLION;
  real_nanosleep(&n, nullptr);
}

int __real_clock_gettime(int clkid, timespec* t) {
  LAZY_LOAD_REAL(clock_gettime);
  return real_clock_gettime(clkid, t);
}

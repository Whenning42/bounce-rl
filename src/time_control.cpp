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

const float INITIAL_SPEED = 1;

const int MILLION = 1000000;
const int BILLION = 1000000000;

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

// Statically initialize our global pointers.
class InitPFNs {
 public:
  InitPFNs() {
    LAZY_LOAD_REAL(time);
    LAZY_LOAD_REAL(gettimeofday);
    LAZY_LOAD_REAL(clock_gettime);
    LAZY_LOAD_REAL(clock);
    LAZY_LOAD_REAL(nanosleep);
    LAZY_LOAD_REAL(usleep);
    LAZY_LOAD_REAL(sleep);
    LAZY_LOAD_REAL(clock_nanosleep);
  }
};

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

timespec operator*(const timespec& t, double s) {
  timespec out;

  double s_sec = t.tv_sec * s;
  double s_nsec = t.tv_nsec * s;

  int64_t s_sec_int = s_sec;
  double s_sec_dec = s_sec - s_sec_int;
  int64_t s_nsec_int = s_nsec + BILLION * s_sec_dec;

  int64_t mod = (s_nsec_int % BILLION + BILLION) % BILLION;

  s_sec_int += (s_nsec_int - mod) / BILLION;
  s_nsec_int = mod;

  out.tv_sec = s_sec_int;
  out.tv_nsec = s_nsec_int;
  return out;
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

timespec operator/(const timespec& t, double s) {
  return t * (1 / s);
}

timespec fake_time_impl(int clk_id, const ClockState* clock) {
  clk_id = base_clock(clk_id);
  timespec real;
  real_clock_gettime(clk_id, &real);
  // std::cout << "Real time fetched: " << real << std::endl;
  timespec real_delta = real - clock->clock_origins_real[clk_id];
  // std::cout << "Real baseline:     " << clock->clock_origins_real[clk_id] << std::endl;
  // std::cout << "Fake baseline:     " << clock->clock_origins_fake[clk_id] << std::endl;
  return clock->clock_origins_fake[clk_id] + real_delta * clock->speedup;
}

void update_speedup(float new_speed, const ClockState* read_clock, ClockState* write_clock, bool should_init = false) {
  ClockState new_clock;
  new_clock.speedup = new_speed;
  for (int clk_id = 0; clk_id < NUM_CLOCKS; clk_id++) {
    real_clock_gettime(clk_id, &new_clock.clock_origins_real[clk_id]);
    timespec fake;
    if (should_init) {
      real_clock_gettime(clk_id, &fake);
    } else {
      fake = fake_time_impl(clk_id, read_clock);
    }
    // std::cout << "Real baseline new: " << new_clock.clock_origins_real[clk_id] << std::endl;
    // std::cout << "Fake baseline new: " << fake << std::endl;
    new_clock.clock_origins_fake[clk_id] = fake;
  }
  *write_clock = new_clock;
}

bool get_new_speed(float* new_speed) {
  bool changed_speed = false;
  if (!speed_file) {
    // printf("Opening speed file.\n");
    speed_file = open(FIFO, O_RDONLY | O_NONBLOCK);
    if (!speed_file) {
      return false;
    }
  } else {
    // printf("Speed file is open.\n");
  }

  char buf[64];
  lseek(speed_file, 0, SEEK_SET);
  ssize_t read_num = read(speed_file, &buf, 64);
  // printf("Read %d bytes.\n", read_num);
  if (read_num > 0) {
    // printf("Reading float at offset: %d\n", read_num - 4);
    *new_speed = *(float*)(buf + read_num - 4);
    changed_speed = true;
  }
  return changed_speed;
}

ClockState init_clock() {
  ClockState clock;
  update_speedup(INITIAL_SPEED, /*read_clock=*/nullptr, &clock, /*should_init=*/true);
  return clock;
}

timespec fake_time(int clk_id) {
  static InitPFNs init_static_pfns;
  int orig_errno = errno;

  struct TaggedClockPtr {
    int64_t tag;
    ClockState* clock;
  };
  // TaggedClockPtr isn't necessarily lock-free.

  static ClockState clock_0 = init_clock();
  static ClockState clock_1 = init_clock();
  static std::atomic<TaggedClockPtr> read_clock = TaggedClockPtr{0, &clock_0};
  static std::atomic<int> clock_tag;

  // Try updating fake time.
  {
    static std::atomic<bool> write_lock = false;
    static std::atomic<ClockState*> write_clock = &clock_1;

    // If we can't get write lock, break.
    bool was_locked = write_lock.exchange(true);
    if (was_locked) {
      goto cont;
    }

    float new_speed;
    bool change_speed = get_new_speed(&new_speed);
    if (test_update) {
      change_speed = true;
      new_speed = new_speedup;
      test_update = 0;
      // printf("Setting speed to: %f\n", new_speed);
    }

    if (change_speed) {
        TaggedClockPtr old_read_clock = read_clock.load();

        // Write to the write clock's state.
        update_speedup(new_speed, old_read_clock.clock, write_clock);

        // Move the newly written clock into read_clock and make the other clock the write_clock.
        TaggedClockPtr new_read_clock = {old_read_clock.tag + 1, write_clock};
        read_clock.store(new_read_clock);
        write_clock = old_read_clock.clock;
    }

    // Release the write lock.
    write_lock.store(false);
  }
cont:

  clk_id = base_clock(clk_id);
  timespec fake;
  TaggedClockPtr local_clock;
  do {
    local_clock = read_clock.load();
    fake = fake_time_impl(clk_id, local_clock.clock);
  } while (local_clock.tag != read_clock.load().tag);

  errno = orig_errno;
  return fake;
}
}  // namespace

time_t time(time_t* arg) {
  timespec tp = fake_time(CLOCK_REALTIME);
  return tp.tv_sec;
}

// NOTE: The error semantics here are a little off.
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

// // NOTE: The error semantics for the sleep family of functions isn't preserved in these wrappers.
// int nanosleep(const struct timespec* req, struct timespec* rem) {
//   try_updating_speedup();
//   LAZY_LOAD_REAL(nanosleep);
//   float speedup = global_clock_state.load().speedup;
//   timespec goal_req = *req / speedup;
//   timespec goal_rem;
//   int ret = real_nanosleep(&goal_req, &goal_rem);
//   if (rem) {
//     *rem = goal_rem * speedup;
//   }
//   return ret;
// }
//
// int usleep(useconds_t usec) {
//   timespec orig_nanosleep;
//   orig_nanosleep.tv_sec = usec / MILLION;
//   orig_nanosleep.tv_nsec = (uint64_t)(usec * 1000) % BILLION;
//   // Time speedup happens in the call to our override nanosleep.
//   nanosleep(&orig_nanosleep, nullptr);
//   return 0;
// }
//
// unsigned int sleep(unsigned int seconds) {
//   LAZY_LOAD_REAL(nanosleep);
//   timespec sleep;
//   sleep.tv_sec = seconds;
//   sleep.tv_nsec = 0;
//   nanosleep(&sleep, nullptr);
//   return 0;
// }
//
// int clock_nanosleep(clockid_t clockid, int flags, const struct timespec* request, struct timespec* remain) {
//   LAZY_LOAD_REAL(clock_nanosleep);
//   float speedup = global_clock_state.load().speedup;
//   timespec goal_req = *request / speedup;
//   timespec goal_rem;
//   int ret = real_clock_nanosleep(clockid, flags, &goal_req, &goal_rem);
//   *remain = goal_rem * speedup;
//   return ret;
// }

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

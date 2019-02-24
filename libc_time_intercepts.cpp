#include <cassert>
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <iostream>

#include <utime.h>
#include <time.h>
#include <sys/time.h>
#include <semaphore.h>

// Intercepted functions
// time
// gettimeofday
// localtime
// localtime_r
// gmtime
// clock_gettime
// gmtime_r
// difftime
// pthread_cond_timedwait
// sem_timedwait
// mktime
// Not intercepted functions
// utime

typedef decltype(&time) PFN_time;
typedef decltype(&gettimeofday) PFN_gettimeofday;
typedef decltype(&localtime) PFN_localtime;
typedef decltype(&localtime_r) PFN_localtime_r;
typedef decltype(&gmtime) PFN_gmtime;
typedef decltype(&clock_gettime) PFN_clock_gettime;
typedef decltype(&gmtime_r) PFN_gmtime_r;
typedef decltype(&difftime) PFN_difftime;
typedef decltype(&pthread_cond_timedwait) PFN_pthread_cond_timedwait;
typedef decltype(&sem_timedwait) PFN_sem_timedwait;
typedef decltype(&mktime) PFN_mktime;

typedef decltype(time) FN_time;
typedef decltype(gettimeofday) FN_gettimeofday;
typedef decltype(localtime) FN_localtime;
typedef decltype(localtime_r) FN_localtime_r;
typedef decltype(gmtime) FN_gmtime;
typedef decltype(clock_gettime) FN_clock_gettime;
typedef decltype(gmtime_r) FN_gmtime_r;
typedef decltype(difftime) FN_difftime;
typedef decltype(pthread_cond_timedwait) FN_pthread_cond_timedwait;
typedef decltype(sem_timedwait) FN_sem_timedwait;
typedef decltype(mktime) FN_mktime;

PFN_time real_time = nullptr;
PFN_gettimeofday real_gettimeofday = nullptr;
PFN_localtime real_localtime = nullptr;
PFN_localtime_r real_localtime_r = nullptr;
PFN_gmtime real_gmtime = nullptr;
PFN_clock_gettime real_clock_gettime = nullptr;
PFN_gmtime_r real_gmtime_r = nullptr;
PFN_difftime real_difftime = nullptr;
PFN_pthread_cond_timedwait real_pthread_cond_timedwait = nullptr;
PFN_sem_timedwait real_sem_timedwait = nullptr;
PFN_mktime real_mktime = nullptr;

const int speedup = 3;
const int MILLION = 1000000;
const int BILLION = 1000000000;

time_t speedup_time_t(time_t t) {
  return t * speedup;
}

timespec speedup_timespec(timespec t) {
  t.tv_sec = t.tv_sec * speedup + t.tv_nsec * speedup / BILLION;
  t.tv_nsec = t.tv_nsec * speedup % BILLION;
  return t;
}

timeval speedup_timeval(timeval t) {
  t.tv_sec = t.tv_sec * speedup + t.tv_usec * speedup / MILLION;
  t.tv_usec = t.tv_usec * speedup % MILLION;
  return t;
}

time_t time(time_t* arg) {
  std::cout << "Intercepting: time" << std::endl;
  std::cout << "arg is: " << arg << std::endl;
  if (!real_time) {
    real_time = (PFN_time)dlsym(RTLD_NEXT, "time");
  }

  time_t out = real_time(arg);
  if(arg) {
    *arg = speedup_time_t(*arg);
  }
  return speedup_time_t(out);
}

int gettimeofday(struct timeval *tv, struct timezone *tz) {
  std::cout << "Intercepting: gettimeofday" << std::endl;
  if (!real_gettimeofday) {
    real_gettimeofday = (PFN_gettimeofday)dlsym(RTLD_NEXT, "gettimeofday");
  }

  int out = real_gettimeofday(tv, tz);
  *tv = speedup_timeval(*tv);
  return out;
}

tm* localtime(const time_t *timep) {
  std::cout << "Intercepting: localtime" << std::endl;
  if (!real_localtime) {
    real_localtime = (PFN_localtime)dlsym(RTLD_NEXT, "localtime");
  }

  time_t t = speedup_time_t(*timep);
  return real_localtime(&t);
}

tm* localtime_r(const time_t* timep, struct tm* result) {
  std::cout << "Intercepting: localtime_r" << std::endl;
  if (!real_localtime_r) {
    real_localtime_r = (PFN_localtime_r)dlsym(RTLD_NEXT, "localtime_r");
  }

  time_t t = speedup_time_t(*timep);
  return real_localtime_r(&t, result);
}

tm* gmtime(const time_t *timep) {
  std::cout << "Intercepting: gmtime" << std::endl;
  if (!real_gmtime) {
    real_gmtime = (PFN_gmtime)dlsym(RTLD_NEXT, "gmtime");
  }

  time_t t = speedup_time_t(*timep);
  return real_gmtime(&t);
}

tm* gmtime_r(const time_t* timep, struct tm* result) {
  std::cout << "Intercepting: gmtime_r" << std::endl;
  if (!real_gmtime_r) {
    real_gmtime_r = (PFN_gmtime_r)dlsym(RTLD_NEXT, "gmtime_r");
  }

  time_t t = speedup_time_t(*timep);
  return real_gmtime_r(&t, result);
}

int clock_gettime(clockid_t clk_id, struct timespec *tp) {
  std::cout << "Intercepting: clock_gettime" << std::endl;
  if (!real_clock_gettime) {
    real_clock_gettime = (PFN_clock_gettime)dlsym(RTLD_NEXT, "clock_gettime");
  }

  int out = real_clock_gettime(clk_id, tp);
  *tp = speedup_timespec(*tp);
  return out;
}

double difftime(time_t t1, time_t t0) {
  std::cout << "Intercepting: difftime" << std::endl;
  if (!real_difftime) {
    real_difftime = (PFN_difftime)dlsym(RTLD_NEXT, "difftime");
  }

  return speedup * real_difftime(t1, t0);
}

int pthread_cond_timedwait(pthread_cond_t *cond, pthread_mutex_t *mutex, const struct timespec *abstime) {
  std::cout << "Calling Original: pthread_cond_timewait" << std::endl;
  if (!real_pthread_cond_timedwait) {
    real_pthread_cond_timedwait = (PFN_pthread_cond_timedwait)dlsym(RTLD_NEXT, "pthread_cond_timedwait");
  }

  return real_pthread_cond_timedwait(cond, mutex, abstime);
}

int sem_timedwait(sem_t *sem, const struct timespec *abs_timeout) {
  std::cout << "Calling Original: sem_timedwait" << std::endl;
  if (!real_sem_timedwait) {
    real_sem_timedwait = (PFN_sem_timedwait)dlsym(RTLD_NEXT, "sem_timedwait");
  }

  return real_sem_timedwait(sem, abs_timeout);
}

time_t mktime(struct tm *tm) {
  std::cout << "Intercepting: mktime" << std::endl;
  if (!real_mktime) {
    real_mktime = (PFN_mktime)dlsym(RTLD_NEXT, "mktime");
  }

  time_t out = real_mktime(tm);
  return speedup_time_t(out);
}

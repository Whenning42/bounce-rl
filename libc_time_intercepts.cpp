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
//
// Not intercepted functions
// utime

#define PFN_TYPEDEF(func) typedef decltype(&func) PFN_##func
#define LAZY_LOAD_REAL(func) if(!real_##func) { \
    real_##func = (PFN_##func)dlsym(RTLD_NEXT, #func); \
  }

PFN_TYPEDEF(time);
PFN_TYPEDEF(gettimeofday);
PFN_TYPEDEF(localtime);
PFN_TYPEDEF(localtime_r);
PFN_TYPEDEF(gmtime);
PFN_TYPEDEF(clock_gettime);
PFN_TYPEDEF(gmtime_r);
PFN_TYPEDEF(difftime);
PFN_TYPEDEF(pthread_cond_timedwait);
PFN_TYPEDEF(sem_timedwait);
PFN_TYPEDEF(mktime);

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

const int speedup = 2;
const int MILLION = 1e6;
const int BILLION = 1e9;

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
  LAZY_LOAD_REAL(time);
  time_t out = real_time(arg);
  if(arg) {
    *arg = speedup_time_t(*arg);
  }
  return speedup_time_t(out);
}

int gettimeofday(struct timeval *tv, struct timezone *tz) {
  LAZY_LOAD_REAL(gettimeofday);
  int out = real_gettimeofday(tv, tz);
  *tv = speedup_timeval(*tv);
  return out;
}

tm* localtime(const time_t *timep) {
  LAZY_LOAD_REAL(localtime);
  time_t t = speedup_time_t(*timep);
  return real_localtime(&t);
}

tm* localtime_r(const time_t* timep, struct tm* result) {
  LAZY_LOAD_REAL(localtime_r);
  time_t t = speedup_time_t(*timep);
  return real_localtime_r(&t, result);
}

tm* gmtime(const time_t *timep) {
  LAZY_LOAD_REAL(gmtime);
  time_t t = speedup_time_t(*timep);
  return real_gmtime(&t);
}

tm* gmtime_r(const time_t* timep, struct tm* result) {
  LAZY_LOAD_REAL(gmtime_r);
  time_t t = speedup_time_t(*timep);
  return real_gmtime_r(&t, result);
}

int clock_gettime(clockid_t clk_id, struct timespec *tp) {
  LAZY_LOAD_REAL(clock_gettime);
  int out = real_clock_gettime(clk_id, tp);
  *tp = speedup_timespec(*tp);
  return out;
}

double difftime(time_t t1, time_t t0) {
  LAZY_LOAD_REAL(difftime);
  return speedup * real_difftime(t1, t0);
}

int pthread_cond_timedwait(pthread_cond_t *cond, pthread_mutex_t *mutex, const struct timespec *abstime) {
  LAZY_LOAD_REAL(pthread_cond_timedwait);
  return real_pthread_cond_timedwait(cond, mutex, abstime);
}

int sem_timedwait(sem_t *sem, const struct timespec *abs_timeout) {
  LAZY_LOAD_REAL(sem_timedwait);
  return real_sem_timedwait(sem, abs_timeout);
}

time_t mktime(struct tm *tm) {
  LAZY_LOAD_REAL(mktime);
  time_t out = real_mktime(tm);
  return speedup_time_t(out);
}

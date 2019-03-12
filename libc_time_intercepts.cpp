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

#define FPN_TYPEDEF(func) typedef decltype(&func) PFN_##func
FPN_TYPEDEF(time);
FPN_TYPEDEF(gettimeofday);
FPN_TYPEDEF(localtime);
FPN_TYPEDEF(localtime_r);
FPN_TYPEDEF(gmtime);
FPN_TYPEDEF(clock_gettime);
FPN_TYPEDEF(gmtime_r);
FPN_TYPEDEF(difftime);
FPN_TYPEDEF(pthread_cond_timedwait);
FPN_TYPEDEF(sem_timedwait);
FPN_TYPEDEF(mktime);
/*typedef decltype(&time) PFN_time;
typedef decltype(&gettimeofday) PFN_gettimeofday;
typedef decltype(&localtime) PFN_localtime;
typedef decltype(&localtime_r) PFN_localtime_r;
typedef decltype(&gmtime) PFN_gmtime;
typedef decltype(&clock_gettime) PFN_clock_gettime;
typedef decltype(&gmtime_r) PFN_gmtime_r;
typedef decltype(&difftime) PFN_difftime;
typedef decltype(&pthread_cond_timedwait) PFN_pthread_cond_timedwait;
typedef decltype(&sem_timedwait) PFN_sem_timedwait;
typedef decltype(&mktime) PFN_mktime;*/

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

const int speedup = 1000;
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
  if (!real_gettimeofday) {
    real_gettimeofday = (PFN_gettimeofday)dlsym(RTLD_NEXT, "gettimeofday");
  }

  int out = real_gettimeofday(tv, tz);
  *tv = speedup_timeval(*tv);
  return out;
}

tm* localtime(const time_t *timep) {
  if (!real_localtime) {
    real_localtime = (PFN_localtime)dlsym(RTLD_NEXT, "localtime");
  }

  time_t t = speedup_time_t(*timep);
  return real_localtime(&t);
}

tm* localtime_r(const time_t* timep, struct tm* result) {
  if (!real_localtime_r) {
    real_localtime_r = (PFN_localtime_r)dlsym(RTLD_NEXT, "localtime_r");
  }

  time_t t = speedup_time_t(*timep);
  return real_localtime_r(&t, result);
}

tm* gmtime(const time_t *timep) {
  if (!real_gmtime) {
    real_gmtime = (PFN_gmtime)dlsym(RTLD_NEXT, "gmtime");
  }

  time_t t = speedup_time_t(*timep);
  return real_gmtime(&t);
}

tm* gmtime_r(const time_t* timep, struct tm* result) {
  if (!real_gmtime_r) {
    real_gmtime_r = (PFN_gmtime_r)dlsym(RTLD_NEXT, "gmtime_r");
  }

  time_t t = speedup_time_t(*timep);
  return real_gmtime_r(&t, result);
}

int clock_gettime(clockid_t clk_id, struct timespec *tp) {
  if (!real_clock_gettime) {
    real_clock_gettime = (PFN_clock_gettime)dlsym(RTLD_NEXT, "clock_gettime");
  }

  int out = real_clock_gettime(clk_id, tp);
  *tp = speedup_timespec(*tp);
  return out;
}

double difftime(time_t t1, time_t t0) {
  if (!real_difftime) {
    real_difftime = (PFN_difftime)dlsym(RTLD_NEXT, "difftime");
  }

  return speedup * real_difftime(t1, t0);
}

int pthread_cond_timedwait(pthread_cond_t *cond, pthread_mutex_t *mutex, const struct timespec *abstime) {
  if (!real_pthread_cond_timedwait) {
    real_pthread_cond_timedwait = (PFN_pthread_cond_timedwait)dlsym(RTLD_NEXT, "pthread_cond_timedwait");
  }

  return real_pthread_cond_timedwait(cond, mutex, abstime);
}

int sem_timedwait(sem_t *sem, const struct timespec *abs_timeout) {
  if (!real_sem_timedwait) {
    real_sem_timedwait = (PFN_sem_timedwait)dlsym(RTLD_NEXT, "sem_timedwait");
  }

  return real_sem_timedwait(sem, abs_timeout);
}

time_t mktime(struct tm *tm) {
  if (!real_mktime) {
    real_mktime = (PFN_mktime)dlsym(RTLD_NEXT, "mktime");
  }

  time_t out = real_mktime(tm);
  return speedup_time_t(out);
}

// Belongs elsewhere
typedef unsigned long int XID;
typedef XID GLXDrawable;
#include <X11/Xlib.h>
#include <stdio.h>

extern "C" void glxSwapBuffers(Display* dpy, GLXDrawable drawable);
FPN_TYPEDEF(glxSwapBuffers);

extern "C" void glxSwapBuffers(Display* dpy, GLXDrawable drawable) {
  printf("Swapping buffers for display %p!\n", dpy);
  //PFN_glxSwapBuffers real_glxSwapBuffers = (PFN_glxSwapBuffers)dlsym(RTLD_NEXT, "glxSwapBuffers");
  //real_glxSwapBuffers(dpy, drawable);
}

typedef unsigned char GLubyte;
extern "C" void (*glXGetProcAddress(const GLubyte* procName)) () {
  printf("Getting address for function: %s\n", procName);
  return nullptr;
}

extern "C" void (*glXGetProcAddressARB(const GLubyte* procName)) () {
  printf("Getting address for function: %s\n", procName);
  return nullptr;
}

//void *dlopen(const char *filename, int flag);
extern "C" void *dlsym(void *handle, const char *symbol);
FPN_TYPEDEF(dlsym);

extern "C" void * __libc_dlopen_mode(const char * filename, int flag);
extern "C" void * __libc_dlsym(void * handle, const char * symbol);

// Function body taken from apitrace
extern "C" void *dlsym(void *handle, const char *symbol) {
  static PFN_dlsym dlsym_ptr = nullptr;
  if (!dlsym_ptr) {
    void *libdl_handle = __libc_dlopen_mode("libdl.so.2", RTLD_LOCAL | RTLD_NOW);
    if (libdl_handle) {
      dlsym_ptr = (PFN_dlsym)__libc_dlsym(libdl_handle, "dlsym");
    }
    if (!dlsym_ptr) {
      printf("Failed to look up real dlsym\n");
      return NULL;
    }
  }

  printf("dlsym symbol: %s\n", symbol);
  return dlsym_ptr(handle, symbol);
}

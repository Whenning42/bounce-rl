// Using this file with LD_PRELOAD will show which dlls and symbols are loaded by a program.

#include <stdio.h>
#include <dlfcn.h>

#include <unordered_map>
#include <string>

#define PFN_TYPEDEF(func) typedef decltype(&func) PFN_##func

extern "C" void * __libc_dlopen_mode(const char * filename, int flag);
extern "C" void * __libc_dlsym(void * handle, const char * symbol);

std::unordered_map<void*, std::string> opened_dls;

extern "C" void *dlopen(const char* file, int mode) {
  PFN_TYPEDEF(dlopen);
  static PFN_dlopen dlopen_ptr = nullptr;
  if (!dlopen_ptr) {
    void *libdl_handle = __libc_dlopen_mode("libdl.so.2", RTLD_LOCAL | RTLD_NOW);
    if (libdl_handle) {
      dlopen_ptr = (PFN_dlopen)__libc_dlsym(libdl_handle, "dlopen");
    }
    if (!dlopen_ptr) {
      printf("Failed to look up real dlopen\n");
      return NULL;
    }
  }

  void* handle = dlopen_ptr(file, mode);
  std::string filename;
  if (file) {
    filename = file;
  } else {
    filename = "";
  }
  opened_dls[handle] = filename;
  return handle;
}

// This function comes from apitrace
extern "C" void *dlsym(void *handle, const char *symbol) {
  PFN_TYPEDEF(dlsym);
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

  printf("from file: %s dlsym symbol: %s\n", opened_dls[handle].c_str(), symbol);
  return dlsym_ptr(handle, symbol);
}


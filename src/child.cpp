#include <stdio.h>
#include <unistd.h>
#include <time.h>

int main(int argc, char** argv) {
  setlinebuf(stdout);
  while (true) {
    printf("tick\n");
    time_t time_v = time(nullptr);
    sleep(1);
  }
}

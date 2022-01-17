#include <stdio.h>
#include <unistd.h>

int main(int argc, char** argv) {
  setlinebuf(stdout);
  while (true) {
    printf("tick\n");
    sleep(1);
  }
}

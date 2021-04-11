#include <string>
#include <time.h>

clock_t last = 0;
std::string last_label = "";
// Statically store last time, get current time, calculate diff.
void Time(std::string label) {
  if (last_label != "") {
    clock_t cur = clock();
    printf("%-30s %lfs\n", (last_label + " time:").c_str(), (double)(cur - last) / CLOCKS_PER_SEC);
  }
  last = clock();
  last_label = label;
}

void TimeClose() {
  Time("");
}


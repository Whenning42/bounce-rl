#include "fast_map.h"
#include "util.h"

#include <unordered_map>

// TODO add google's dense_hash_map to the mix.

int main(int argc, char** argv) {
  FastMap<Uint32Hash> fast_map(1024, 4);
  std::unordered_map<uint32_t, uint32_t, Uint32Hash> unord_map;
  uint32_t n = 0;
  for (int i = 0; i < 256; ++i) {
    n = (n + 177) % 350;
    assert(fast_map.insert(n, i) != -1);
    unord_map[n] = i;
  }

  n = 0;
  int s = 0;
  Time("Fast map benchmark");
  for (int i = 0; i < 100 * 1000 * 1000; ++i) {
    n = (n + 55) % 350;
    int v = fast_map.lookup(n);
    if (v >= 0) {
      s += v;
    }
  }
  printf("%d\n", s);

  n = 0;
  s = 0;
  Time("Unordered map benchmark");
  for (int i = 0; i < 100 * 1000 * 1000; ++i) {
    n = (n + 55) % 350;
    auto it = unord_map.find(n);
    if (it != unord_map.end()) {
      s += it->second;
    }
  }
  printf("%d\n", s);
  TimeClose();
}


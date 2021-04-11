#include <cstdint>
#include <cassert>
#include <stdlib.h>

struct Uint32Hash {
  uint32_t operator() (uint32_t v) const {
    return (v + 1) * 0xA54FF531;
  }
};

// A dense fixed size hashmap.
// Line:  24   8
//        Key  Value
template <typename Hash>
class FastMap {
 public:
  FastMap(int buckets, int slots): buckets(buckets), slots(slots) {
    buffer = (uint32_t*)malloc(buckets * slots * sizeof(buffer[0]));
  }
  ~FastMap() { free(buffer); }

  // Returns the number of items in this corresponding bucket.
  // returns -1 if the corresponding bucket was full and the value wasn't inserted.
  int insert(uint32_t key, uint32_t value) {
    assert(value < 256);
    uint32_t h = hash(key);
    uint32_t* bucket = buffer + (h % buckets) * slots;
    uint32_t* slot = bucket;
    for (int i = 0; i < slots; ++i) {
      if (*slot == 0) {
        *slot = (h << 8) | value;
        return slot - bucket + 1;
      }
    }
    return -1;
  }

  // Look up the key for this value.
  int lookup(uint32_t key) {
    uint32_t h = hash(key);
    uint32_t* bucket = buffer + (h % buckets) * slots;
    // Unrolled bucket lookups.
    if ((h << 8) == (bucket[0] & 0xffffff00)) {
      return bucket[0] & 0xff;
    }
    if ((h << 8) == (bucket[1] & 0xffffff00)) {
      return bucket[1] & 0xff;
    }
    if ((h << 8) == (bucket[2] & 0xffffff00)) {
      return bucket[2] & 0xff;
    }
    if ((h << 8) == (bucket[3] & 0xffffff00)) {
      return bucket[3] & 0xff;
    }
    return -1;
  }

 private:
  const Hash hash = Hash();
  uint32_t* buffer = nullptr;
  const int buckets;
  const int slots;
};

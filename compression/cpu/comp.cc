#include <vector>
#include <stdio.h>
#include <time.h>
#include <string>
#include <unordered_map>
#include <queue>
#include <cassert>

#include "lodepng.h"

// using Color = std::tuple<int, int, int>;
using Color = uint32_t;
using ColorFrequency = std::pair<Color, int>;
using CColorFrequency = std::pair<const Color, int>;

const std::string IMG = "../memories/hd_images/106.png";

struct ColorHash {
  std::size_t operator()(const Color& color) const {
    // std::hash isn't helpful here so we roll our own hash.
    // The magic number here is just a large prime between 2^31 and 2^32.
    return color * 0xA54FF531;
  }
};

struct MoreFrequent {
  bool operator() (const ColorFrequency& f_0, const ColorFrequency& f_1) {
    return f_0.second < f_1.second;
  }
};

class BaseArena {
  public:
    static void Reserve(size_t bytes) {
      assert(memory == nullptr);
      memory = (uint8_t*)malloc(bytes);
      reserved = bytes;
      used = 0;
      allocs = 0;
    };

    // Deallocates all memory.
    void deallocate_impl(uint8_t* p, size_t n) {
      if (used != 0) {
        // printf("Deallocating all!\n");
        used = 0;
        allocs = 0;
      }
    }

    uint8_t* allocate_impl(size_t n, int alignment) {
      assert(memory != nullptr);
      allocs++;
      uint8_t* alloc = memory + used;
      if ((size_t)alloc % alignment != 0) {
        alloc += alignment - ((size_t)alloc % alignment);
      }
      used = alloc - memory + n;
      assert(used <= reserved);
      // printf("Alloc: %ldB w/ align: %d gives p: %p"
      //        " used: %dB allocs: %d\n", n, alignment, alloc, used, allocs);
      return alloc;
    }

  private:
    static uint8_t* memory;
    static int32_t reserved;
    static int32_t used;
    static int32_t allocs;
};
uint8_t* BaseArena::memory = nullptr;
int32_t BaseArena::reserved = 0;
int32_t BaseArena::used = 0;
int32_t BaseArena::allocs = 0;
template <typename T>
class Arena : public BaseArena {
  public:
    using value_type = T;

    T* allocate(size_t n) {
      return (T*)allocate_impl(sizeof(T) * n, alignof(T));
    }

    void deallocate(T* p, size_t n) {
      deallocate_impl((uint8_t*)p, sizeof(T) * n);
    }

    Arena() = default;
    template <class U> constexpr Arena (const Arena <U>&) noexcept {}
};

template <typename T>
bool operator==(const Arena<T>& a1, const Arena<T>& a2) {
  return true;
}

int rle_size = 0;
void WriteRunLength(int i, std::vector<uint32_t, Arena<uint32_t>>* buffer) {
  // Leading bit prefix = 0.
  buffer->push_back(i % 128);
  if (i > 128) {
    buffer->push_back(i >> 7);
  }
  rle_size += 4;
}

#include <iostream>
template <typename T>
void MapStats(const T& map) {
  size_t collisions = 0, empty = 0;
  for (auto bucket = map.bucket_count(); bucket--;) {
      if (map.bucket_size(bucket) == 0)
          empty++;
      else
          collisions += map.bucket_size(bucket) - 1;
  }
  std::cout << "a = " << map.max_load_factor() << ' ' << map.load_factor() << ' '
      << ' ' << map.bucket_count() << ' ' << collisions << ' ' << empty << '\n';
}

int compressed_color_size = 0;
int raw_color_size = 0;
void WriteColorCode(const Color& color, const std::unordered_map<Color, int, ColorHash, std::equal_to<Color>, Arena<CColorFrequency>>& color_codes, std::vector<uint32_t, Arena<uint32_t>>* buffer) {
  constexpr int leading_prefix = 1 << 7;
  constexpr int continue_prefix = 3 << 6;
  const auto it = color_codes.find(color);
  if (it != color_codes.end()) {
    int color_code = it->second;
    compressed_color_size++;
    if (color_code <= 63) {
      buffer->push_back(color_code | leading_prefix);
    }
    if (color_code > 63) {
      buffer->push_back(color_code & 0x3f | continue_prefix);
      buffer->push_back(color_code >> 6);
      compressed_color_size++;
    }
    // int v = color_code % 63 | leading_prefix;
    // if (color_code > 63) {
    //   v |= 1 << 6;
    // }
    // buffer->push_back(v);
    // compressed_color_size++;
    // color_code /= 63;
    // while (color_code > 0) {
    //   v = color_code % 128;
    //   color_code /= 128;
    //   if (color_code > 0) {
    //     v |= 1 << 7;
    //   }
    //   buffer->push_back(v);
    //   compressed_color_size++;
    // }
  } else {
    buffer->push_back(color);
    raw_color_size += 4;
  }
}

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

// For each pixel either:
//    Increment RLE counter.
// Or write last run-length if > 0 and write new color.

// Code:
// b0: run-length or color
//   run-length: b1-7, (b8-15), ..., var int run-length
//   color: b1-7/255 compressed or full color
//     compressed: b1-7/255, (b8-15) color code
//     full color: 255, b8-31 color
const int C = 4;
const int W = 1920;
const int H = 1080;
int main(int argc, char** argv) {
  const int COUNT_EVERY = 16;
  const int MAX_COMPRESSED_COLORS = 63 * 256;
  const int MAX_COLORS = 8000; // 4000 or 8000

  // Reserve 16MB in our global arena.
  BaseArena::Reserve(16000000);

  uint8_t* image;
  unsigned w, h;
   Time("Loading");
  lodepng_decode_file(&image, &w, &h, IMG.c_str(), LCT_RGBA, 8);

  // RGBA Byte order.
  // uint32_t reads give ABGR.
  Time("Cold read time");
  int s = 0;
  for (int y = 0; y < H; ++y) {
    for (int x = 0; x < W; ++x) {
      s += *(uint32_t*)(image + (y * H + x) * C);
    }
  }
  printf("Ignore: %d\n", s);

  Time("Encode time");
  unsigned char* out;
  size_t outsize;
  lodepng_encode_memory(&out, &outsize, image, w, h, LCT_RGBA, 8);

  for (int i = 0; i < 10; ++i) {
    Time("Counting frequencies");
    std::unordered_map<Color, int, ColorHash, std::equal_to<Color>, Arena<CColorFrequency>> color_frequencies;
    color_frequencies.reserve(MAX_COLORS);
    Color last = 0;
    int last_run = 0;
    int n = 0;
    // Compute color frequencies.
    for (int y = 0; y < H; ++y) {
      for (int x = 0; x < W; ++x) {
        // uint8_t* p = image + (y * 960 + x) * C;
        // Color cur = {p[0], p[1], p[2]};
        Color cur = *(uint32_t*)(image + (y * H + x) * C);
        if (cur != last && n % COUNT_EVERY == 0) {
          color_frequencies[cur] += 1;
          // printf("BucketCt: %d, %d Size: %d, %d\n",
          //     color_frequencies.bucket_count(),
          //     color_frequencies.max_bucket_count(),
          //     color_frequencies.size(),
          //     color_frequencies.max_size());
          last = cur;
        }
        n++;
      }
    }
    // MapStats(color_frequencies);
    // return 0;

    // Build the priority queue's vec ahead of time to access reserve call.
    Time("Building palette");
    std::vector<ColorFrequency, Arena<ColorFrequency>> color_frequency_vec;
    color_frequency_vec.reserve(MAX_COLORS);
    for (const auto& color_freq : color_frequencies) {
      color_frequency_vec.push_back(color_freq);
    }
    std::priority_queue<ColorFrequency, std::vector<ColorFrequency, Arena<ColorFrequency>>, MoreFrequent>
     most_frequent(MoreFrequent(), std::move(color_frequency_vec));
    std::unordered_map<Color, int, ColorHash, std::equal_to<Color>, Arena<CColorFrequency>> color_codes;
    color_codes.reserve(MAX_COLORS);

    int code = 0;
    while (!most_frequent.empty()) {
      const auto& [color, frequency] = most_frequent.top();
      color_codes[color] = code;
      code++;

      // 'color' and 'frequency' are invalidated on pop.
      most_frequent.pop();
      if (code > MAX_COMPRESSED_COLORS) {
        break;
      }
    }

    Time("Encoding image");
    last = 0;
    // Encode image.
    // std::vector<uint8_t, Arena<uint8_t>> buffer;
    std::vector<uint32_t, Arena<uint32_t>> buffer;
    buffer.reserve(2000000);
    int run_length = 0;
    for (int y = 0; y < H; ++y) {
      for (int x = 0; x < W; ++x) {
        Color cur = *(uint32_t*)(image + (y * W + x) * C);
        if (cur == last) {
          run_length++;
        } else {
          WriteRunLength(run_length, &buffer);
          WriteColorCode(cur, color_codes, &buffer);
          last = cur;
          run_length = 1;
        }
      }
    }
    TimeClose();
    printf("Encoded size: %luKB\n", sizeof(buffer[0]) * buffer.size() / 1000 + color_frequencies.size() * 3 / 1000);
  }

  printf("rle: %d, compressed_color: %d, raw_color: %d\n", rle_size, compressed_color_size, raw_color_size);
}

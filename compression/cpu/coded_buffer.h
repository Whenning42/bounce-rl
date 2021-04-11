// Writes encoded data to an opaque buffer.
// Goals:
//  - Provide a simple interface.
//  - Allow for improved memory alignment.
//  - Improve performance benchmarking of our write implementation.
//
//  RLE:   1 or 2 bytes
//  Color: 1 or 3 bytes
//
//  Four possible implementations:
//   - Direct byte writing or uint32_t bit word coalescing.
//   - A single packed buffer or parallel buffers of uniform sizes with
//       bitmasks providing the read order.

// Direct or Coalesced
// Packed or parallel
// Code used

#include <cstdint>

#include <stdio.h>

template <typename Writer>
class Coder {
 public:
   Coder(Writer* writer): writer(*writer) {};

   void WriteRunLength(uint32_t run_length) {
     if (run_length < 64) {
       writer.WriteRL1(run_length);
     }
     if (run_length >= 64) {
       run_length = run_length & 0xff80 << 1 | 1 << 7 | run_length & 0x7f;
       writer.WriteRL2(run_length);
     }
   }
  void WriteColor(uint32_t color, bool is_byte) {
    if (is_byte) {
      writer.WriteColor1(color);
    }
    if (!is_byte) {
      writer.WriteColor3(color);
    }
  }

 private:
   Writer& writer;
};

// This helps us figure out how long encoding takes in our benchmarks.
class NopWriter {
 public:
  void WriteRL1(uint32_t run_length) { v += run_length; }
  void WriteRL2(uint32_t run_length) { v += 2 * run_length; }
  void WriteColor1(uint32_t color) { v += color; }
  void WriteColor3(uint32_t color) { v += 3 * color; }
  uint32_t v = 0;
};

// Direct, Packed.
class ByteWriter {
 public:
  ByteWriter(std::size_t bytes);
  ~ByteWriter();

  // The number suffix here tells how many of the lower bits we write.
  void WriteRL1(uint32_t run_length);
  void WriteRL2(uint32_t run_length);
  void WriteColor1(uint32_t color);
  void WriteColor3(uint32_t color);

  uint8_t* buffer = nullptr;
  uint8_t* tail = nullptr;
};

class CoalescingWriter {
 public:
  CoalescingWriter(std::size_t bytes);
  ~CoalescingWriter();

  void WriteRL1(uint32_t run_length);
  void WriteRL2(uint32_t run_length);
  void WriteColor1(uint32_t color);
  void WriteColor3(uint32_t color);

  void Pump() {
    while (tail_l >= 4) {
      *tail++ = tail_v & 0xffffffff;
      tail_v = tail_v >> 32;
      tail_l -= 4;
    }
  }

  uint32_t* buffer = nullptr;
  uint32_t* tail = nullptr;
  uint64_t tail_v = 0;
  uint32_t tail_l = 0;
};

// Try both direct and coalesced
class ParallelWriter {
 public:
  ParallelWriter(std::size_t bytes);
  ~ParallelWriter();

  void WriteRL1(uint32_t run_length);
  void WriteRL2(uint32_t run_length);
  void WriteColor1(uint32_t color);
  void WriteColor3(uint32_t color);

  void Pump1() {
    if (tail1_l >= 8) {
      *tail1++ = tail1_v;
      tail1_v = 0;
      tail1_l = 0;
    }
  }
  void Pump2() {
    if (tail2_l >= 8) {
      *tail2++ = tail2_v;
      tail2_v = 0;
      tail2_l = 0;
    }
  }
  void Pump3() {
    if (tail3_l >= 6) {
      *tail3++ = tail3_v;

      tail3_l = 0;
    }
  }

  uint64_t* buffer1 = nullptr;
  uint64_t* tail1 = nullptr;
  uint64_t tail1_v = 0;
  uint64_t tail1_l = 0;

  uint64_t* buffer2 = nullptr;
  uint64_t* tail2 = nullptr;
  uint64_t tail2_v = 0;
  uint64_t tail2_l = 0;

  uint64_t* buffer3 = nullptr;
  uint64_t* tail3 = nullptr;
  uint64_t tail3_v = 0;
  uint64_t tail3_l = 0;
};

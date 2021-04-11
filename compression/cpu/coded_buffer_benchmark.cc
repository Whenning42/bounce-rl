#include "coded_buffer.h"
#include "util.h"

#include <stdio.h>

int main(int argc, char** argv) {
  uint32_t n = 0;
//  {
//    NopWriter w;
//    Coder<NopWriter> coder(&w);
//    Time("Benchmark Nop");
//    for (uint32_t i = 0; i < 200 * 1000 * 1000; ++i) {
//      n = (n + 15) % 256;
//      coder.WriteRunLength(n);
//      coder.WriteColor(n, n < 128);
//    };
//    printf("%d\n", w.v);
//  }
//  {
//    ByteWriter w(2000 * 1000 * 1000);
//    Coder<ByteWriter> coder(&w);
//    Time("Benchmark Byte Writer");
//    for (uint32_t i = 0; i < 200 * 1000 * 1000; ++i) {
//      n = (n + 15) % 256;
//      coder.WriteRunLength(n);
//      coder.WriteColor(n, n < 128);
//    };
//    printf("%d\n", w.buffer[2000]);
//  }
  {
    CoalescingWriter w(2000 * 1000 * 1000);
    Coder<CoalescingWriter> coder(&w);
    Time("Benchmark Coalescing Writer");
    for (uint32_t i = 0; i < 200 * 1000 * 1000; ++i) {
      n = (n + 15) % 256;
      coder.WriteRunLength(n);
      coder.WriteColor(n, n < 128);
    };
    printf("%d\n", w.buffer[2000]);
  }
//  {
//    ParallelWriter w(2000 * 1000 * 1000);
//    Coder<ParallelWriter> coder(&w);
//    Time("Benchmark Parallel Writer");
//    for (uint32_t i = 0; i < 200 * 1000 * 1000; ++i) {
//      n = (n + 15) % 256;
//      coder.WriteRunLength(n);
//      coder.WriteColor(n, n < 128);
//    };
//    printf("%d\n", w.buffer1[2000]);
//    printf("%d\n", w.buffer2[2000]);
//    printf("%d\n", w.buffer3[2000]);
//  }
  TimeClose();
}

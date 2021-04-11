// In  uint image[];
// Out uint encoded[];

// Include FastMap
// Include coded buffer

// Generated C++ header
#include <stdint.h>
typedef uint32_t uint;
struct point {
  uint x;
  uint y;
};
point gl_GlobalInvocationID;
uint* image;
uint* encoded;
// + built-ins
//

void exec() {
  uint id = gl_GlobalInvocationID.x + 32 * gl_GlobalInvocationID.y;
  if (id != 0) return;
//  encoded[id] = image[id];

  const uint in_block_size = 50;
  const uint out_block_size = 20;

  uint in_pos = id * in_block_size;
  uint out_pos = id * out_block_size;

  uint in_end = (id + 1) * in_block_size;

  uint last = 0;
  uint rl = 0;
  for (; in_pos < in_end; in_pos++) {
    uint v = image[in_pos];
    if (v != last) {
      encoded[out_pos] = rl + 100;
      encoded[out_pos + 1] = v + 200;
      rl = 0;
      last = v;
      out_pos += 2;
    }
    rl++;
  }
}

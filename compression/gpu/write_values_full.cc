#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <cassert>

// Includes
// - Run length encoded colors.
// - Dictionary compressed colors.
// - A packed buffer to store compressed data.

uint32_t* in_buffer;
uint32_t* out_buffer;
uint32_t* map_buffer;

const uint32_t IN_BLOCK_LEN = 100;
const uint32_t IN_BLOCK_BYTES = IN_BLOCK_LEN * 4;

const uint32_t OUT_LENGTH_BYTES = 4;
const uint32_t FLAG_BUFFER_BYTES = IN_BLOCK_LEN / 32 + 1;
const uint32_t DATA_BUFFER_BYTES = IN_BLOCK_LEN * 4;
const uint32_t OUT_BLOCK_BYTES = OUT_LENGTH_BYTES + FLAG_BUFFER_BYTES + DATA_BUFFER_BYTES;

const uint32_t FLAG_OFFSET = 4;
const uint32_t DATA_OFFSET = FLAG_OFFSET + FLAG_BUFFER_BYTES;

// BUCKETS must be greater than or equal to 256 in order for the
// 8 bit bucket + 24-bit upper key to produce correct lookups.
uint32_t BUCKETS = 256;
uint32_t SLOTS = 4;

// Map Buffer                24    8
//   buf[0] Bucket[0]  UpperKey  Val
//   buf[1]
//   buf[2]
//   buf[3]
//   buf[4] Bucket[1]

// Returns either the value for the given key, or the given key unchanged if no value is found.
// One should take care that all keys are >= 256 if they want to know if the value was found in the map or not.
// ~ 20 instr.
uint32_t ReadMap(uint32_t k) {
  assert(SLOTS == 4);
  assert(BUCKETS >= 256);
  uint32_t h = (k + 1) * 0xA54FF531;
  uint32_t lower_key = h % BUCKETS;
  uint32_t upper_key = h / 256;
  uint32_t bucket_off = SLOTS * lower_key;
  if (map_buffer[bucket_off] >> 8 == upper_key) k = map_buffer[bucket_off] & 0xff;
  if (map_buffer[bucket_off + 1] >> 8 == upper_key) k = map_buffer[bucket_off + 1] & 0xff;
  if (map_buffer[bucket_off + 2] >> 8 == upper_key) k = map_buffer[bucket_off + 2] & 0xff;
  if (map_buffer[bucket_off + 3] >> 8 == upper_key) k = map_buffer[bucket_off + 3] & 0xff;
  return k;
}

// Succeeds or dies.
void WriteMap(uint32_t k, uint32_t v) {
  assert(SLOTS == 4);
  assert(BUCKETS >= 256);
  assert(v < 256);
  uint32_t h = (k + 1) * 0xA54FF531;
  uint32_t lower_key = h % BUCKETS;
  uint32_t upper_key = h / 256;
  uint32_t bucket_off = SLOTS * lower_key;

  uint32_t word = upper_key << 8 | v;

  for (int i = 0; i < SLOTS; ++i) {
    if (map_buffer[bucket_off + i] == 0) {
      map_buffer[bucket_off + i] = word;
      return;
    }
  }

  // Overfilled a bucket.
  assert(false);
}

// IN_BLOCK
// uint32 image pixels

// OUT_BLOCK
// Labels: size, flags buffer,      data buffer
// Size:   4      IN_BLOCK / 32 + 1  IN_BLOCK / 4

// Generated memory safe packed buffers?
// struct Encoder (size_t n) {
//   uint32_t length;
//   BitBuffer(n) flags;
//   uint32_t[n] data_buffer;
// }
//
// Encoder.offset(length);
// Encoder.offset(flags);
// Encoder.offset(data_buffer);

void Exec(int thread) {
  uint32_t read_pos = thread * IN_BLOCK_BYTES / 4;

  uint32_t len_pos = thread * OUT_BLOCK_BYTES / 4;
  uint32_t flag_pos = len_pos + FLAG_OFFSET;
  uint32_t data_pos = len_pos + DATA_OFFSET;
  const uint32_t start_data_pos = data_pos;

  uint32_t last = in_buffer[read_pos];
  uint32_t rl = 0;

  // Write state:
  uint32_t f = 0;
  uint32_t fl = 0;
  uint32_t low = 0;
  uint32_t high = 0;
  uint32_t low_p = 0;
  for (; read_pos < (thread + 1) * IN_BLOCK_LEN; read_pos++) {
    uint32_t p = in_buffer[read_pos];
    if (p != last || rl == 255) {
      uint32_t v = ReadMap(last);
      uint32_t w = (v << 8) + rl;

      // Write logic:
      f = f << 1;
      fl += 1;
      uint32_t l = 16;
      if (v > 256) {
        f |= 1;
        l = 32;
      }
      if (fl == 32) {
        out_buffer[flag_pos] = f;
        flag_pos++;
        f = 0;
        fl = 0;
      }

      low |= w << low_p;
      if (l + low_p - 32 > 0) {
        high |= w >> (l - low_p);
      }
      low_p += l;

      if (low_p >= 32) {
        out_buffer[data_pos] = low;
        data_pos++;
        low = high;
        low_p -= 32;
      }
      data_pos++;
      rl = 0;
      last = p;
    }
    rl++;
  }
  uint32_t v = ReadMap(last);
  uint32_t w = (v << 8) + rl;

  // Write logic:
  f = f << 1;
  fl += 1;
  uint32_t l = 16;
  if (v > 256) {
    f |= 1;
    l = 32;
  }
  if (fl > 0) {
    out_buffer[flag_pos] = f;
    flag_pos++;
    f = 0;
    fl = 0;
  }

  low |= w << low_p;
  if (l + low_p - 32 > 0) {
    high |= w >> (l - low_p);
  }
  low_p += l;

  while (low_p >= 32) {
    out_buffer[data_pos] = low;
    data_pos++;
    low = high;
    low_p -= 32;
  }

  out_buffer[len_pos] = data_pos - start_data_pos;
}

int main(int argc, char** argv) {
  // Compress
  const int THREADS = 12;
  const int IN_BUFFER_BYTES = IN_BLOCK_BYTES * THREADS;
  in_buffer = (uint32_t*)malloc(IN_BUFFER_BYTES);
  out_buffer = (uint32_t*)calloc(OUT_BLOCK_BYTES * THREADS, 1);
  map_buffer = (uint32_t*)calloc(BUCKETS * SLOTS, 4);

  uint32_t* rev_map = (uint32_t*)calloc(256, 4);

  for (int i = 0; i < IN_BLOCK_LEN * THREADS; ++i) {
    in_buffer[i] = 400 + i / 5;
  }

  // Assign 0, 3, 6, 9 as 0, 1, 2, 3 in the map.
  for (int i = 0; i < 30; ++i) {
    WriteMap(400 + 3 * i, i);
    rev_map[i] = 400 + 3 * i;
  }
  for (int i = 0; i < 90; ++i) {
    printf("Map[%d] = %d\n", 400 + i, ReadMap(400 + i));
  }

  for (int t = 0; t < THREADS; ++t) {
    Exec(t);
  }

  // Decompress
  uint32_t* decomp_buffer = (uint32_t*)calloc(IN_BUFFER_BYTES, 1);
  for (int thread = 0; thread < THREADS; ++thread) {
    uint32_t write_pos = thread * IN_BLOCK_BYTES / 4;

    uint32_t len_pos = thread * OUT_BLOCK_BYTES / 4;
    uint32_t flag_pos = len_pos + FLAG_OFFSET;

    uint32_t data_pos = len_pos + DATA_OFFSET;
    const uint32_t start_pos = data_pos;

    for (; data_pos - start_pos < out_buffer[len_pos]; ++data_pos) {
      uint32_t data = out_buffer[data_pos];
      uint32_t rl = data & 0xff;
      uint32_t p = (data & 0xffffff00) >> 8;
      if (p < 256) {
        p = rev_map[p];
      }
      for (int i = 0; i < rl; ++i) {
        decomp_buffer[write_pos] = p;
        write_pos++;
      }
    }
  }

  // Print
  // for (int i = 0; i < IN_BLOCK_BYTES * THREADS / 4; ++i) {
  //   printf("in_buffer[%d] = %x, decomp[%d], %x\n", i, in_buffer[i],
  //                                                  i, decomp_buffer[i]);
  // }
  bool all_match = true;
  for (int i = 0; i < IN_BLOCK_LEN * THREADS; ++i) {
    bool match = in_buffer[i] == decomp_buffer[i];
    all_match &= match;
    if (!match) {
      printf("Diff in_buf[%d]: %d, decomp_buf[%d]: %d\n", i, in_buffer[i], i, decomp_buffer[i]);
    }
  }
  printf("Roundtrip was lossless: %d\n", all_match);

  for (int i = 0; i < OUT_BLOCK_BYTES * THREADS / 4; ++i) {
    printf("out_buffer[%d] = %x\n", i, out_buffer[i]);
  }

  free(in_buffer);
  free(out_buffer);
  free(decomp_buffer);
}

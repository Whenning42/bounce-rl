#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

uint32_t* in_buffer;
uint32_t* out_buffer;

uint32_t IN_BLOCK_LEN = 100;
uint32_t IN_BLOCK_BYTES = IN_BLOCK_LEN * 4;

uint32_t OUT_LENGTH_BYTES = 4;
uint32_t FLAG_BUFFER_BYTES = IN_BLOCK_LEN / 32 + 1;
uint32_t DATA_BUFFER_BYTES = IN_BLOCK_LEN * 4;

uint32_t OUT_BLOCK_BYTES = OUT_LENGTH_BYTES + FLAG_BUFFER_BYTES + DATA_BUFFER_BYTES;

uint32_t FLAG_OFFSET = 4;
uint32_t DATA_OFFSET = FLAG_OFFSET + FLAG_BUFFER_BYTES;

// IN_BLOCK
// uint32 image pixels

// OUT_BLOCK
// Labels: int32, flags buffer,      data buffer
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
  for (; read_pos < (thread + 1) * IN_BLOCK_LEN; read_pos++) {
    uint32_t p = in_buffer[read_pos];
    if (p != last || rl == 255) {
      { // TODO: Remap p
      }

      // Write rl + p combo.
      uint32_t to_write = rl + (last << 8);
      // flags are none.
      out_buffer[data_pos] = to_write;
      data_pos++;

      //
      rl = 0;
      last = p;
    }
    rl++;
  }
  // Write rl + p combo.
  uint32_t to_write = rl + (last << 8);
  // flags are none.
  out_buffer[data_pos] = to_write;
  data_pos++;

  out_buffer[len_pos] = data_pos - start_data_pos;


  // Bit packing logic.
  // bool is_long = run_length > 255;
  // bool raw_color = color > 255;

  // flag_word = flag_word << 2 | is_long << 1 | raw_color;
  // flag_word_len += 2;

  // data_word = data_word << 8 | run_length % 256;
  // data_word_len += 1;
  // if (is_long) {
  //   data_word = data_word << 8 | run_length / 256;
  //   data_word_len += 1;
  // }

  // if (raw_color) {
  //   data_word = data_word << 8 | color;
  // } else {
  //   data_word = data_word << 24 | color;
  // }
}

int main(int argc, char** argv) {
  // Compress
  const int THREADS = 2;
  const int IN_BUFFER_BYTES = IN_BLOCK_BYTES * THREADS;
  in_buffer = (uint32_t*)malloc(IN_BUFFER_BYTES);
  out_buffer = (uint32_t*)calloc(OUT_BLOCK_BYTES * THREADS, 1);

  for (int i = 0; i < IN_BLOCK_LEN * THREADS; ++i) {
    in_buffer[i] = i / 5;
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
  bool match = true;
  for (int i = 0; i < IN_BLOCK_LEN * THREADS; ++i) {
    match &= in_buffer[i] == decomp_buffer[i];
  }
  printf("Roundtrip was lossless: %d\n", match);

  for (int i = 0; i < OUT_BLOCK_BYTES * THREADS / 4; ++i) {
    printf("out_buffer[%d] = %x\n", i, out_buffer[i]);
  }

  free(in_buffer);
  free(out_buffer);
  free(decomp_buffer);
}

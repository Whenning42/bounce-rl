#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main(int argc, char** argv) {
  const int ITER = 40;
  uint32_t* enc = (uint32_t*)calloc(400, 4);
  uint32_t* raw = (uint32_t*)calloc(600, 4);
  uint32_t* dec = (uint32_t*)calloc(600, 4);

  uint32_t low = 0;
  uint32_t high = 0;
  uint32_t pos = ITER / 32 + 2;
  uint32_t low_p = 0;

  uint32_t f = 0;
  uint32_t fl = 0;
  uint32_t flag_pos = 0;

  // Compressed byte writer.
  // If v < 256 writes:
  //  i, v
  // else:
  //  i, v0, v1, 0
  for (int i = 0; i < ITER; ++i) {
    uint32_t rl = i;
    uint32_t v = (i * 75) % 512;

    uint32_t l = 16;
    f = f << 1;
    fl += 1;
    if (v > 256) {
      l = 32;
      f |= 1;
    }
    if (fl == 32) {
      printf("Pushing flags: 0x%x\n", f);
      enc[flag_pos] = f;
      flag_pos++;
      f = 0;
      fl = 0;
    }

    uint32_t w = (v << 8) + rl;
    printf("To pack Word: 0x%x, Val: 0x%x, i: 0x%x, length: %d\n", w, v, i, l);
    raw[i] = w;

    // low        high
    //   low_p
    //
    // last = low_p + l
    // mid = 32
    // start = low_p
    //
    // Write low and high words.
    low |= w << low_p;
    if (l + low_p - 32 > 0) {
      high |= w >> (l - low_p);
    }
    low_p += l;

    // Commit
    if (low_p >= 32) {
      enc[pos] = low;
      pos += 1;
      low = high;
      low_p -= 32;
    }
  }

  // Note: We're still dropping the last RLE chunk.
  while (fl != 32) {
    f = f << 1;
    fl++;
  }
  enc[flag_pos] = f;

  flag_pos = 0;
  f = enc[0];
  printf("Loaded flags: 0x%x\n", f);
  pos = ITER / 32 + 2;
  low_p = 0;

  fl = 31;
  for (int i = 0; i < ITER; ++i) {
    // Overflow :(
    if (fl > 31) {
      fl = 31;
      flag_pos++;
      f = enc[flag_pos];
      printf("Found the flag: 0x%x\n", f);
    }
    bool is_long = f & (0x1 << fl);
    fl--;

    uint32_t low = enc[pos];
    uint32_t high = enc[pos + 1];
    uint32_t word;
    // Decompression happens on CPU ahead of train time so we can branch here and spare
    // extra cycles.
    if (!is_long) {
      // Read 16 bits
      // low          high
      //   low_p
      // 16 - low_p   low_p - 16
      if (low_p > 16) {
        word = ((high << (16 - low_p)) + low >> low_p) & 0xffff;
      } else {
        word = (low >> low_p) & 0xffff;
      }
      low_p += 16;
    } else {
      // Read 32 bits
      // low          high
      //   low_p
      // 32 - low_p   low_p
      //
      if (low_p > 0) {
        word = (high << (32 - low_p)) + low >> low_p;
        printf("High Contrib: 0x%x, Low Contrib: 0x%x, Sum: 0x%x\n", high << (32 - low_p), low >> low_p, (high << (32 - low_p)) + low >> low_p);
      } else {
        word = low;
      }
      low_p += 32;
    }
    if (low_p >= 32) {
      pos += 1;
      low_p -= 32;
    }

    printf("Unpacked Word: 0x%x, length: %d\n", word, 16 * is_long + 16);
    // uint32_t rl = word & 0x0000ff;
    // uint32_t v =  word & 0xffff00;
    dec[i] = word;
  }

  for (int i = 0; i < 100; ++i) {
    printf("enc[%d] = %x\n", i, enc[i]);
  }
  for (int i = 0; i < 100; ++i) {
    printf("raw[%d] = %x, dec[%d] = %x\n", i, raw[i], i, dec[i]);
  }
}

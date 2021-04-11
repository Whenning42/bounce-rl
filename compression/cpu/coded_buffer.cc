#include "coded_buffer.h"
#include <stdlib.h>

////// Byte Writer //////
//
ByteWriter::ByteWriter(std::size_t bytes) {
  buffer = (uint8_t*)malloc(bytes);
  tail = buffer;
}

ByteWriter::~ByteWriter() {
  free(buffer);
}

// We're using little-endianess here.
void ByteWriter::WriteRL1(uint32_t run_length) {
  // Is 0xff necessary?
  *tail++ = run_length & 0xff;
}

void ByteWriter::WriteRL2(uint32_t run_length) {
  *tail++ = run_length & 0xff;
  *tail++ = (run_length >> 8) & 0xff;
}

void ByteWriter::WriteColor1(uint32_t color) {
  *tail++ = color & 0xff;
}

void ByteWriter::WriteColor3(uint32_t color) {
  *tail++ = color & 0xff;
  *tail++ = (color >> 8) & 0xff;
  *tail++ = (color >> 16) & 0xff;
}

////// Coalescing Writer //////
//
CoalescingWriter::CoalescingWriter(std::size_t bytes) {
  buffer = (uint32_t*)malloc(bytes);
  tail = buffer;
}

CoalescingWriter::~CoalescingWriter() {
  free(buffer);
}

// We're using little-endianess here.
void CoalescingWriter::WriteRL1(uint32_t run_length) {
  // Is 0xff necessary?
  tail_v = tail_v << 8 | run_length & 0xff;
  tail_l++;
  // Pump();
}

void CoalescingWriter::WriteRL2(uint32_t run_length) {
  tail_v = tail_v << 16 | run_length & 0xffff;
  tail_l += 2;
  // Pump();
}

void CoalescingWriter::WriteColor1(uint32_t color) {
  tail_v = tail_v << 8 | color & 0xff;
  tail_l++;
  Pump();
}

void CoalescingWriter::WriteColor3(uint32_t color) {
  tail_v = tail_v << 24 | color & 0xffffff;
  tail_l += 3;
  Pump();
}

////// Parallel Writer //////
//
ParallelWriter::ParallelWriter(std::size_t bytes) {
  buffer1 = (uint64_t*)malloc(bytes);
  buffer2 = (uint64_t*)malloc(bytes);
  buffer3 = (uint64_t*)malloc(bytes);

  tail1 = buffer1;
  tail2 = buffer2;
  tail3 = buffer3;
}

ParallelWriter::~ParallelWriter() {
  free(buffer1);
  free(buffer2);
  free(buffer3);
}

// We're using little-endianess here.
void ParallelWriter::WriteRL1(uint32_t run_length) {
  // Is 0xff necessary?
  tail1_v = tail1_v << 8 | run_length & 0xff;
  tail1_l++;
  Pump1();
}

void ParallelWriter::WriteRL2(uint32_t run_length) {
  tail2_v = tail2_v << 16 | run_length & 0xffff;
  tail2_l += 2;
  Pump2();
}

void ParallelWriter::WriteColor1(uint32_t color) {
  tail1_v = tail1_v << 8 | color & 0xff;
  tail1_l++;
  Pump1();
}

void ParallelWriter::WriteColor3(uint32_t color) {
  tail3_v = tail3_v << 24 | color & 0xffffff;
  tail3_l += 3;
  Pump3();
}

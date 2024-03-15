import time

import csv_logger


class Profiler:
    def __init__(self, path=None, no_op=False):
        self.no_op = no_op
        if no_op:
            return

        self.stack = []
        self.tag_names = []
        self.first = None
        self.timings = []

        self.outfile = csv_logger.CsvLogger(path)

        # Parameters defining the structure of the profiler
        # Setting any of these to True is unsupported, but
        # could be implemented to represent different allowed
        # profile graphs.
        self.allow_untracked_root = False
        self.allow_self_nested_tag = False
        self.allow_multiple_tag_uses = False

    def _get_tag(self, tag_name):
        if tag_name not in self.tag_names:
            self.tag_names.append(tag_name)
            self.timings.append(0)
        return self.tag_names.index(tag_name)

    def _push(self, tag_val):
        if not self.allow_self_nested_tag and tag_val in self.stack:
            assert False
        self.stack.append((tag_val, time.monotonic_ns() // 1000))

    def _pop(self, tag_val):
        assert len(self.stack) > 0
        assert self.stack[-1][0] == tag_val
        start_time = self.stack.pop()[1]
        duration_ns = time.monotonic_ns() // 1000 - start_time
        assert self.timings[tag_val] == 0
        self.timings[tag_val] = duration_ns

    def begin(self, start_tag, end=None):
        if self.no_op:
            return
        start_tag = self._get_tag(start_tag)

        # Handle end cases, either requested end or finished cycle
        if end is not None and self.first is not None:
            end = self._get_tag(end)
            self._pop(end)
        elif start_tag == self.first:
            while len(self.stack) > 0:
                self._pop(self.stack[-1][0])

        if self.first is None:
            self.first = start_tag
        # Completed a profile frame. Log and reset timings.
        elif start_tag == self.first:
            named_timings = dict(zip(self.tag_names, self.timings))
            self.outfile.write_line(named_timings)
            self.timings = [
                0,
            ] * len(self.tag_names)

        self._push(start_tag)

    def end(self, end_tag):
        if self.no_op:
            return

        end_tag = self._get_tag(end_tag)
        self._pop(end_tag)

        if not self.allow_untracked_root and len(self.stack) == 0:
            assert False

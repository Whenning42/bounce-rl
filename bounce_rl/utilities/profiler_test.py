import csv
import os
import time

import csv_logger
from bounce_rl.profiler import Profiler

filename = "./tmp_test_profile.csv"


def profile_frame_0():
    p = Profiler(path=filename)
    # Frame timings used in this test are as follows:
    """
    a
     a1
     Untracked
     a2
     a3
    b
    """

    # Run for a single frame.
    p.begin("a")
    time.sleep(0.1)
    p.begin("a1")
    time.sleep(0.1)
    p.end("a1")
    time.sleep(0.1)
    p.begin("a2")
    time.sleep(0.1)
    p.begin("a3", end="a2")
    time.sleep(0.1)
    p.end("a3")
    p.begin("b", end="a")
    time.sleep(0.1)

    # Finish the frame by starting the start marker again.
    p.begin("a")


def profile_frame_1():
    p = Profiler(path=filename)
    # Frame timings used in this test are as follows:
    """
    a
     b
      c
    """

    # Run for a single frame.
    p.begin("a")
    time.sleep(0.1)
    p.begin("b")
    time.sleep(0.1)
    p.begin("c")
    time.sleep(0.1)

    # Finish the frame by starting the start marker again.
    p.begin("a")


def expect_near(a, b):
    assert abs(a - b) < 0.01, f"a: {a}, b: {b}"


if __name__ == "__main__":
    try:
        os.remove(filename)
    except OSError:
        pass
    profile_frame_0()

    # Load the profile file
    f = csv_logger.CsvFile(filename)
    reader = csv.DictReader(f.file)
    rows = []
    for row in reader:
        rows.append(row)
    assert len(rows) == 1
    timings = rows[0]

    # Verify the timings are roughly equal to:
    expect_near(float(timings["a"]) / 1e6, 0.5)
    expect_near(float(timings["a1"]) / 1e6, 0.1)
    expect_near(float(timings["a2"]) / 1e6, 0.1)
    expect_near(float(timings["a3"]) / 1e6, 0.1)
    expect_near(float(timings["b"]) / 1e6, 0.1)

    try:
        os.remove(filename)
    except OSError:
        pass
    profile_frame_1()

    # Load the profile file
    f = csv_logger.CsvFile(filename)
    reader = csv.DictReader(f.file)
    rows = []
    for row in reader:
        rows.append(row)
    assert len(rows) == 1
    timings = rows[0]

    # Verify the timings are roughly equal to:
    expect_near(float(timings["a"]) / 1e6, 0.3)
    expect_near(float(timings["b"]) / 1e6, 0.2)
    expect_near(float(timings["c"]) / 1e6, 0.1)

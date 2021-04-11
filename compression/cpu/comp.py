from PIL import Image
import numpy as np
from collections import defaultdict
from humanize import naturalsize

IMAGE = "../memories/hd_images/106.png"

image = Image.open(IMAGE)
image = np.array(image)

def CompEst(img):
    shape = img.shape

    colors = defaultdict(int)
    colors_wasnt = defaultdict(int)
    run_counts = []

    print(shape)
    k = 1
    last = (0, 0, 0) * k
    was_not_last = 0
    was_last = 0

    last_was_size = 0
    last_wasnt_size = 0
    last_was_run = 0
    num_runs = 0
    for y in range(shape[0]):
        for x in range(0, shape[1], k):
            color = ()
            for i in range(k):
                color += tuple(img[y, x + i])
            if color == last:
                was_last += 1
    #            last_was_size += 1
                last_was_run += 1
            else:
                was_not_last += 1
    #            last_wasnt_size += 25
                colors_wasnt[color] += 1
                if last_was_run > 0:
                    run_counts.append(last_was_run)
                    last_was_size += 1 + last_was_run // 128
                    last_was_run = 0
                    num_runs += 1
            colors[color] += 1
            last = color
            x += 1

    print("was and wasn't same counts:", was_last // 1000, was_not_last // 1000)
    print("Last was size:", naturalsize(last_was_size // 8))
    print("Last wasn't size:", naturalsize(last_wasnt_size // 8))
    print("Num runs:", num_runs)

    counts = []
    for color, count in sorted(colors.items(), key=lambda x: -x[1]):
        counts.append(count)
    counts_wasnt = []
    for color, count in sorted(colors_wasnt.items(), key=lambda x: -x[1]):
        counts_wasnt.append(count)
    run_counts = sorted(run_counts, key=lambda x: -x)

    print(len(counts))
    l = len(counts)
    for p in [.05, .25, .5, .75, .95]:
        i = int(p * l)
        print(i, counts[int(p * l)])

    words = [[], []]
    for color, count in colors_wasnt.items():
        found_colors = set()
        for i in range(k):
            this_color = color[3*i : 3*(i+1)]
            found_colors.add(this_color)
        words[len(found_colors) - 1].append(color)
    print("WL1", words[0])
    print("\n\n\nWL2", words[1])
    print("Len words 2: ", len(words[1]))

    compress_set = 63
    print("Naive: ", naturalsize(shape[0] * shape[1] * shape[2]))
    print("1 byte palette: ", naturalsize(sum(counts[:255]) + 4 * sum(counts[255:])))
    print("Same pixel RLE plus byte color coding", \
      naturalsize(last_was_size + sum(counts_wasnt[:compress_set]) + 2 * sum(counts_wasnt[compress_set:]) + 3 * len(words[0]) + 6 * len(words[1])))
    print("rle:", last_was_size, " compressed_color:", sum(counts_wasnt[:63]) + 2 * sum(counts_wasnt[63:]), " raw_color:", 3 * len(counts_wasnt))

    print("Prefix sums:")
    for i in range(12):
        print("Sum of first ", 2 ** i, " counts: ", sum(counts[ : 2 ** i]), " counts_wasnt:", sum(counts_wasnt[ : 2 ** i]), "run_counts:", sum(run_counts[ : 2 ** i]))
    #    print("Last count was:", counts[2**i], " count wasnt:", counts_wasnt[2**i])
    for i in range(12):
        print("At index: ", 2 ** i, " counts: ", counts[ 2 ** i], " counts_wasnt:", counts_wasnt[ 2 ** i], "run_counts:", run_counts[ 2 ** i])

# CompEst(image[:270])
# CompEst(image[270:])
CompEst(image)

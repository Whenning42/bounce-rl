import os
import csv
import shutil
import weakref

DELIM = ","

class CsvLogger:
    def __init__(self, file):
        self.header_file = file + "_header"
        self.data_file = file

    def write_line(self, data):
        # Merge the keys into the header file.
        merged = {}
        try:
            with open(self.header_file, "r") as f:
                if os.path.exists(self.header_file):
                    l = f.readline()
                    keys = list(map(str.strip, l.split(",")))
                    keys = list(filter(None, keys))
                    for k in keys:
                        merged[k] = None
        except FileNotFoundError:
            pass

        for k, v in data.items():
            merged[k] = v

        tmp_path = self.header_file + "_tmp"
        f2 = open(tmp_path, "w")
        f2.write(DELIM.join(merged.keys()))
        f2.close()
        os.rename(tmp_path, self.header_file)

        # Write the data to the data file
        f = open(self.data_file, "a", newline='')
        writer = csv.writer(f)
        writer.writerow(merged.values())
        f.close()

class CsvFile:
    def __init__(self, file):
        self.header_file = file + "_header"
        self.data_file = file

        self.tmp_file = file + "_tmpcat"
        with open(self.tmp_file,'wb') as write_file:
            for f in [self.header_file, self.data_file]:
                with open(f,'rb') as read_file:
                    shutil.copyfileobj(read_file, write_file)
                    write_file.write(b"\n")

        self.file = open(self.tmp_file, 'r')
        self._finalizer = weakref.finalize(self, os.remove, self.tmp_file)

    def filename(self):
        return self.tmp_file

    def close(self):
        self._finalizer()

def EmptyToNone(d):
    for k, v in d.items():
        if v == "":
            d[k] = None
    return d


if __name__ == "__main__":
    # Test
    logger = CsvLogger("tmp_data.csv")
    logger.write_line({"k0": 0})
    logger.write_line({"k1": 1})

    cat = CsvFile("tmp_data.csv")
    reader = csv.DictReader(cat.file)
    reader = map(EmptyToNone, reader)
    v_0 = next(reader)
    assert v_0 == {"k0": "0", "k1": None}, v_0
    v_1 = next(reader)
    assert v_1 == {"k0": None, "k1": "1"}, v_1

    cat.close()
    assert not os.path.exists(cat.filename())

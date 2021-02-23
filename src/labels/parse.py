import csv

filename = "compound_labels.csv"

with open(filename, "r") as f:
    reader = csv.DictReader(f)
    for line in reader:
        print(line["filename"], line["region_shape_attributes"], line["region_attributes"])

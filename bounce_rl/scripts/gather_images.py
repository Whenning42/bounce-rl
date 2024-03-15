import csv
import glob
import csv_logger
import subprocess
import numpy as np
import tqdm
import shutil

i = 0

subprocess.run("mkdir gathered", shell=True)
subprocess.run("mkdir gathered/images", shell=True)
subprocess.run("mkdir gathered/actions", shell=True)
subprocess.run("rm gathered/train_mask.json", shell=True)
subprocess.run("echo { >> gathered/train_mask.json", shell=True)

mask_file = open("gathered/train_mask.json", 'a')
for run in range(2, 10):
    directory = f"user_demo_{run:02d}"
    images = directory + "/images/*"
    step_path = directory + "/steps.csv"
    step_file = csv_logger.CsvFile(step_path)
    steps = csv.DictReader(step_file.file)
    for row in tqdm.tqdm(list(steps)):
        im_path = row["pixels_path"]
        im_path = directory + "/images/" + im_path
        new_im_path = f"gathered/images/{i:08d}.png"
        shutil.copy(im_path, new_im_path)

        act = row["action"]
        act = np.array([act])
        np.save(f"gathered/actions/{i:08d}.npy", act)

        # The "perturbed" flag gets logged backwards
        should_train = row["perturbed"] == "True"
        if should_train == True:
            should_train_jstr = "true"
        else:
            should_train_jstr = "false"
        mask_file.write(f'  "{i}": {should_train_jstr},\n')
        i += 1
mask_file.write("}\n")

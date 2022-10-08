import csv_logger
from pathlib import Path
import pandas as pd
import numpy as np
import tqdm
import glob
from PIL import Image

def LoadDemo(directory):
    input_file = csv_logger.CsvFile(directory + "/input.csv")
    step_file = csv_logger.CsvFile(directory + "/steps.csv")
    inputs = pd.read_csv(input_file.filename())
    # Select our three action axes and the time dimension.
    # The time dimension is used for averaging actions over
    # the duration of a timestep, and is dropped after that.
    inputs = pd.DataFrame({c: inputs[c] for c in ["ls_x", "lt", "rt", "time"]})
    steps = pd.read_csv(step_file.filename())
    image_dir = directory + "/images"

    num_steps = len(steps.index)
    num_actions = len(steps.index) - 1

    image_files = sorted(glob.glob(image_dir + "/*.png"))
    im = np.asarray(Image.open(image_files[0]))
    images = np.empty((num_steps,) + im.shape)
    for i, file in enumerate(tqdm.tqdm(sorted(glob.glob(image_dir + "/*.png")))):
        images[i] = np.asarray(Image.open(file))

    action_axes = len(inputs.columns) - 1
    actions = np.empty((num_actions, action_axes))
    for i in tqdm.tqdm(range(len(steps.index) - 1)):
        start = steps.iloc[i]["time"]
        end = steps.iloc[i+1]["time"]

        left = inputs["time"].searchsorted(start)
        right = inputs["time"].searchsorted(end, side="right")
        s = inputs[left:right+1].copy()
        s["l"] = (s["time"].shift(-1) - s["time"]).fillna(0)
        n = s.to_numpy()
        weighted = np.expand_dims(n[:, -1], -1) * n[:, :-2]
        action = weighted.sum(axis = 0) / n[:, -1].sum()
        actions[i] = action

    rewards = steps["train_reward"].to_numpy()
    infos = []
    for i in tqdm.tqdm(range(len(steps.index))):
        infos.append({"perturbed": steps.iloc[i]["perturbed"]})
    dones = np.full((num_steps), False)
    return actions, rewards, images, dones, infos

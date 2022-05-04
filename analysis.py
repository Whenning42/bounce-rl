from copy import copy
from scipy import stats
import csv_logger
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import tqdm

STEP_FILE = "/home/william/Workspaces/GameHarness/out/run/n_steps_4800_seed_0/0/steps.csv"
EPISODE_FILE = "/home/william/Workspaces/GameHarness/out/run/n_steps_4800_seed_0/0/episodes.csv"

# Requires df have 'ep' and 'train_reward' columns populated.
# Time discounted rewards may be incorrect if indicies in df are non sequential.
def PopulateTimeDiscountedRewards(df, gamma = .99, expected_reward = -1, rew_col = "train_reward"):
    # Using np for per-row calculations is ~100x faster.
    end_of_episode_reward = expected_reward * 1 / (1 - gamma)

    rows = df.loc[:, ("ep", rew_col)].to_numpy()
    last_ep = -1
    g = -1
    for i in tqdm.tqdm(reversed(range(rows.shape[0]))):
        ep = rows[i, 0]
        if ep != last_ep:
            g = end_of_episode_reward
            last_ep = ep
        else:
            g = g * gamma + rows[i, 1]
        rows[i, 1] = g
    df["g"] = rows[:, 1]

# For each set of consecutive penalized steps, remove the penalty value from 
# train reward and insert an equal number of new -1 penalty frames at the start
# of the set.
# May be incorrect if df index is not a dense range.
# df is unchanged and the result is returned as a value
def BuildAlternateReward(df):
    # Columns are:
    #  0, original index
    #  1, new reward
    old_data = df.loc[:, ("train_reward", "is_penalized")].to_numpy()
    new_data = np.zeros((2 * len(df.index), 3))
    new_i = 0
    penalized_section = []

    assert df.index.min() == 0
    alternate_i = 0

    in_segment = False
    section_start = -1
    for i in tqdm.tqdm(range(df.index.max() + 1)):
        p = old_data[i, 1]
        if p and not in_segment:
            # Entered a penalty section
            in_segment = True
            section_start = i
        elif not p and in_segment:
            # Exited a penalty section
            in_segment = False
            length = i - section_start
            for j in range(length):
                new_data[new_i] = (-1, -1, i)
                new_i += 1
            for row in penalized_section:
                new_data[new_i] = row
                new_i += 1
            penalized_section = []

        if p:
            # Undo the penalty
            penalized_section.append((i, old_data[i, 0] + 1, i))
        else:
            new_data[new_i] = (i, old_data[i, 0], i)
        new_i += 1
    new_data = new_data[:new_i]
    return pd.DataFrame({"orig_index": new_data[:, 0], \
                         "spot": new_data[:, 2],
                         "reward": new_data[:, 1]})

step_loader = csv_logger.CsvFile(STEP_FILE)
episode_loader = csv_logger.CsvFile(EPISODE_FILE)

steps = pd.read_csv(step_loader.file)
episodes = pd.read_csv(episode_loader.file)

print(matplotlib.get_backend())
# steps["train_reward"].hist()
# plt.plot(steps.index, steps["train_reward"], 'ko')

steps["ep"] = np.floor(steps.index / 480)
PopulateTimeDiscountedRewards(steps)
ep_stats = steps.groupby("ep").mean()
print(ep_stats)

non_trivial = steps.loc[steps["train_reward"] != -1]
non_stopped = steps.loc[steps["vel"] != 0]

# Draws a log plot of the reward distribution of the agent over time.
# Set zero points to dark instead of white.
hist = non_trivial
cmap = copy(plt.cm.plasma)
cmap.set_bad(cmap(0))
# plt.hist2d(hist.index, hist["train_reward"], bins = [200, 50], norm = matplotlib.colors.LogNorm(vmin=1), cmap = cmap)

# Draws a linear plot of the velocity distribution of the agent over time
df = non_stopped
df = df[df["vel"] < 80]
df = df[df["vel"] > -60]
# fig, ax = plt.subplots()
# ax.plot(ep_stats.index, ep_stats["vel"])
# t_ax = ax.twinx()
# t_ax.plot(ep_stats.index, ep_stats["train_reward"], 'r')
# plt.show()

# Show reward-to-go distribution over time
# PopulateTimeDiscountedRewards(steps)
plt.hist2d(steps.index, steps["g"], bins = [200, 50], range=((0, 730000), (-130, -70)), norm = matplotlib.colors.LogNorm(vmin=1), cmap = cmap)
plt.ylim(-130, -70)
plt.title("Original reward-to-go distribution")

alt = BuildAlternateReward(steps)
alt["ep"] = np.floor(alt["spot"] / 480)
PopulateTimeDiscountedRewards(alt, rew_col = "reward")
alt = alt.loc[alt["orig_index"] > 0].reset_index()

plt.figure()
plt.hist2d(alt.index, alt["g"], bins = [200, 50], range=((0, 730000), (-130, -70)), norm = matplotlib.colors.LogNorm(vmin=1), cmap = cmap)
plt.ylim(-130, -70)
plt.title("New reward-to-go distribution")
plt.show()

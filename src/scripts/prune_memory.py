import os
import re

# List all files
# Get keys from files
# Use policy to get keep set of files
# Use keep set to generate delete set
# Ask for confirmation and delete unwanted files

# In our case, policy is N % 100,000 = 0 or file's key is greatest

if __name__ == "__main__":
    pattern = r"rl_model_(\d*)_steps\.zip"
    transform = lambda m: int(m)
    def policy(file_set):
        max_k = -1e9
        min_k = 1e12
        for k, file in file_set.items():
            max_k = max(k, max_k)
            min_k = min(k, min_k)

        keep_set = set()
        for k, file in file_set.items():
            if k % 100000 == 0 or k == max_k or k == min_k:
                keep_set.add(file)
        return keep_set

    files = os.listdir(".")
    relevant_files = {}
    for f in files:
        m = re.search(pattern, f)
        if m is not None:
            key = transform(m.group(1))
            if key in relevant_files:
                assert(False)
            relevant_files[key] = f

    keep_set = policy(relevant_files)
    delete_set = set()
    for k, file in relevant_files.items():
        if file not in keep_set:
            delete_set.add(file)

    print("Requesting keep of files: ", sorted(keep_set))
    print("Requesting delete of files: ", sorted(delete_set))
    conf = input("Confirm deletion [y/N]: ")
    if conf == "y" or conf == "Y":
        for f in delete_set:
            os.remove(f)

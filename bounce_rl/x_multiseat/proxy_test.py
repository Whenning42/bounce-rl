import os
import subprocess

p = subprocess.Popen(["python", "src/x_multiseat/proxy.py"])

env = dict(os.environ)
env["DISPLAY"] = ":1"

for i in range(10000):
    print(f"{i}")
    subprocess.run(
        ["python", "src/x_multiseat/proxy_test_child.py"],
        stderr=subprocess.STDOUT,
        env=env,
    )

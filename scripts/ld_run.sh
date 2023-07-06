# Runs the given command with the correct ld library path configured
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:./:./build/lib PYTHONPATH=../stable-baselines3:$PYTHONPATH "$@"

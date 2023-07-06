# Runs the given command with the correct ld library path configured
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:./ PYTHONPATH=../stable-baselines3:$PYTHONPATH "$@"

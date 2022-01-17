# GameHarness

This is my long term project to explore developing Machine Learning agents to successfully play a variety of video games. It's inspired by OpenAI's Dota bot and Universe project and DeepMind's StarCraft bot.

This repo contains the following subprojects:
- A library for recording and controlling Linux applications. The source for this is spread throughout this project's directories, but the main file is "harness.py" in the root directory.

# To launch a Steam game with the time control .so

Add this line to the steam game launch options

```
LD_PRELOAD=/home/william/Workspaces/GameHarness/build/time_control.so %command%
```

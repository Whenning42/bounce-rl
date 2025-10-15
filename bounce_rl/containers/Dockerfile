FROM ubuntu:20.04

RUN apt-get update && apt-get upgrade -y && \
       apt-get install -y x11-apps

RUN mkdir /home/william

RUN echo "STEAM_COMPAT_DATA_PATH=/home/william/test_steam/steamapps/compatdata/881100 \
          STEAM_COMPAT_CLIENT_INSTALL_PATH=/home/william/test_steam \
          '/home/william/test_steam/steamapps/common/SteamLinuxRuntime_sniper'/_v2-entry-point \
          --verb=waitforexitandrun -- \
          '/home/william/test_steam/steamapps/common/Proton 8.0'/proton waitforexitandrun  \
          '/home/william/test_steam/steamapps/common/Noita/noita.exe'" > run_noita.sh; \
         chmod +x run_noita.sh

RUN apt-get install -y mesa-utils

# RUN apt-get install -y libgl1-nvidia-glvnd-glx
RUN apt-get install -y libglvnd0 libglx0
RUN apt-get install vulkan-tools

RUN set -x && \
    dpkg --add-architecture i386 && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends \
      libgl1:i386

RUN echo "cd /home/william/test_steam/steamapps/common/Noita/; /run_noita.sh" > run.sh && \
         chmod +x run.sh

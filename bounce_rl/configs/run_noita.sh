#!/bin/bash

set -eu

function log {
    echo $(date --rfc-3339=seconds) RUN_NOITA: $@
}                                                                                                                                                            

export GAME_COMPAT_DATA="$HOME/.steam/steam/steamapps/compatdata/881100/"
export RUN_COMPAT_DATA="$ENV_PREFIX/compatdata"
export PROTON_ROOT="$ENV_PREFIX/compatdata/pfx"

log "Setting up Noita game files at: $PROTON_ROOT"
rm -rf $PROTON_ROOT
mkdir -p $(dirname $PROTON_ROOT)
cp -r $GAME_COMPAT_DATA $RUN_COMPAT_DATA 

mkdir -p $PROTON_ROOT/drive_c/users/steamuser/AppData/LocalLow/Nolla_Games_Noita/save_shared
rm -rf $PROTON_ROOT/drive_c/users/steamuser/AppData/LocalLow/Nolla_Games_Noita/save0*
cp -f bounce_rl/environments/noita/mod/golden_config.xml \
  $PROTON_ROOT/drive_c/users/steamuser/AppData/LocalLow/Nolla_Games_Noita/save_shared/config.xml
cp -r bounce_rl/environments/noita/initial_save00 \
      $PROTON_ROOT/drive_c/users/steamuser/AppData/LocalLow/Nolla_Games_Noita/save00
ln -fs $(pwd)/bounce_rl/environments/noita/mod $HOME/.steam/steam/steamapps/common/Noita/mods/rl_mod

# Set steam environment variables
export STEAM_COMPAT_DATA_PATH="$RUN_COMPAT_DATA"
export STEAM_COMPAT_CLIENT_INSTALL_PATH=$HOME/.local/share/Steam
export STEAM_COMPAT_LIBRARY_PATHS=$HOME/.local/share/Steam/steamapps
export STEAM_RUNTIME_LIBRARY_PATH=$HOME/.local/share/Steam/ubuntu12_32/steam-runtime/pinned_libs_32:/home/william/.local/share/Steam/ubuntu12_32/steam-runtime/pinned_libs_64:/usr/lib/libfakeroot:/usr/lib32:/usr/lib/perf:/usr/lib:/home/william/.local/share/Steam/ubuntu12_32/steam-runtime/lib/i386-linux-gnu:/home/william/.local/share/Steam/ubuntu12_32/steam-runtime/usr/lib/i386-linux-gnu:/home/william/.local/share/Steam/ubuntu12_32/steam-runtime/lib/x86_64-linux-gnu:/home/william/.local/share/Steam/ubuntu12_32/steam-runtime/usr/lib/x86_64-linux-gnu:/home/william/.local/share/Steam/ubuntu12_32/steam-runtime/lib:/home/william/.local/share/Steam/ubuntu12_32/steam-runtime/usr/lib
# TODO: Shader cache?


# Launch the game
log "Running on display: $DISPLAY"
log "Running offset: $PID_OFFSET"
for i in $(seq 1 $PID_OFFSET); do
    touch "/tmp/noop.txt"
done

# Working Directory
cd $HOME/.steam/steam/steamapps/common/Noita

# Command
$HOME/.local/share/Steam/steamapps/common/SteamLinuxRuntime_sniper/run-in-sniper -- "$HOME/.local/share/Steam/steamapps/common/Proton 8.0/proton" run $HOME/.steam/steam/steamapps/common/Noita/noita.exe &
trap "kill $(jobs -p)" EXIT
wait

log "Exiting from run_noita.sh"

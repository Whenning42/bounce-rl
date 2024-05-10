#!/bin/bash
# Generated with `lutris -b run_noita.sh noita` on a working
# lutris Noita install.

set -eu

export MAIN_SAVE="$HOME/.steam/steam/steamapps/compatdata/881100/"
mkdir -p $MAIN_SAVE

# Environment variables
export STEAM_COMPAT_APP_ID=777
export STEAM_COMPAT_DATA_PATH="$WINEPREFIX"
export STEAM_COMPAT_CLIENT_INSTALL_PATH=$HOME/.local/share/Steam
export STEAM_COMPAT_LIBRARY_PATHS=$HOME/.local/share/Steam/steamapps
export STEAM_RUNTIME_LIBRARY_PATH=$HOME/.local/share/Steam/ubuntu12_32/steam-runtime/pinned_libs_32:/home/william/.local/share/Steam/ubuntu12_32/steam-runtime/pinned_libs_64:/usr/lib/libfakeroot:/usr/lib32:/usr/lib/perf:/usr/lib:/home/william/.local/share/Steam/ubuntu12_32/steam-runtime/lib/i386-linux-gnu:/home/william/.local/share/Steam/ubuntu12_32/steam-runtime/usr/lib/i386-linux-gnu:/home/william/.local/share/Steam/ubuntu12_32/steam-runtime/lib/x86_64-linux-gnu:/home/william/.local/share/Steam/ubuntu12_32/steam-runtime/usr/lib/x86_64-linux-gnu:/home/william/.local/share/Steam/ubuntu12_32/steam-runtime/lib:/home/william/.local/share/Steam/ubuntu12_32/steam-runtime/usr/lib

export WINEPREFIX=$WINEPREFIX/pfx

# TODO: Shader cache?

function log {
    echo $(date --rfc-3339=seconds) RUN_NOITA: $@
}                                                                                                                                                            
# Restore the games state and config from the main save and the golden config
# respectively.
if [[ "$WINEPREFIX" == "$MAIN_SAVE" ]]; then
    :
else
    log "Setting up prefix: $WINEPREFIX"
    mkdir -p $(dirname $WINEPREFIX)
    rm -rf $WINEPREFIX
    cp -r $MAIN_SAVE $WINEPREFIX
fi

mkdir -p $WINEPREFIX/drive_c/users/steamuser/AppData/LocalLow/Nolla_Games_Noita/save_shared
rm -rf $WINEPREFIX/drive_c/users/steamuser/AppData/LocalLow/Nolla_Games_Noita/save0*
cp -f bounce_rl/environments/noita/mod/golden_config.xml \
  $WINEPREFIX/drive_c/users/steamuser/AppData/LocalLow/Nolla_Games_Noita/save_shared/config.xml
# Copy a minimal save file into the environment to disable the intro screen.
cp -r bounce_rl/environments/noita/initial_save00 \
      $WINEPREFIX/drive_c/users/steamuser/AppData/LocalLow/Nolla_Games_Noita/save00
ln -s $(pwd)/bounce_rl/environments/noita/mod $HOME/.steam/steam/steamapps/common/Noita/mods/rl_mod


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

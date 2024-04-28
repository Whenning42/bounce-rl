#!/bin/bash
# Generated with `lutris -b run_noita.sh noita` on a working
# lutris Noita install.

set -eu

export MAIN_SAVE='/home/william/.wine'

# Environment variables
export DISABLE_LAYER_AMD_SWITCHABLE_GRAPHICS_1="1"
export __GL_SHADER_DISK_CACHE="1"
export __GL_SHADER_DISK_CACHE_PATH="/home/william/.steam/steam/steamapps/common/Noita"
export LD_LIBRARY_PATH="/home/william/.local/share/Steam/steamapps/common/Proton 8.0/dist/lib:/home/william/.local/share/Steam/steamapps/common/Proton 8.0/dist/lib64:/usr/lib:/usr/lib32:/usr/lib/libfakeroot:/usr/lib64:/home/william/.local/share/lutris/runtime/Ubuntu-18.04-i686:/home/william/.local/share/lutris/runtime/steam/i386/lib/i386-linux-gnu:/home/william/.local/share/lutris/runtime/steam/i386/lib:/home/william/.local/share/lutris/runtime/steam/i386/usr/lib/i386-linux-gnu:/home/william/.local/share/lutris/runtime/steam/i386/usr/lib:/home/william/.local/share/lutris/runtime/Ubuntu-18.04-x86_64:/home/william/.local/share/lutris/runtime/steam/amd64/lib/x86_64-linux-gnu:/home/william/.local/share/lutris/runtime/steam/amd64/lib:/home/william/.local/share/lutris/runtime/steam/amd64/usr/lib/x86_64-linux-gnu:/home/william/.local/share/lutris/runtime/steam/amd64/usr/lib"
export WINEDEBUG="-all"
export DXVK_LOG_LEVEL="none"
export WINEARCH="win64"
export WINE="/home/william/.local/share/Steam/steamapps/common/Proton 8.0/dist/bin/wine"
export WINE_MONO_CACHE_DIR="/home/william/.local/share/lutris/runners/wine/Proton 8.0/mono"
export WINE_GECKO_CACHE_DIR="/home/william/.local/share/lutris/runners/wine/Proton 8.0/gecko"
export WINEESYNC="0"
export WINEFSYNC="1"
export WINE_FULLSCREEN_FSR="1"
export DXVK_NVAPIHACK="0"
export DXVK_ENABLE_NVAPI="1"
export PROTON_BATTLEYE_RUNTIME="/home/william/.local/share/lutris/runtime/battleye_runtime"
export PROTON_EAC_RUNTIME="/home/william/.local/share/lutris/runtime/eac_runtime"
export WINEDLLOVERRIDES="d3d10core,d3d11,d3d12,d3d12core,d3d9,d3dcompiler_33,d3dcompiler_34,d3dcompiler_35,d3dcompiler_36,d3dcompiler_37,d3dcompiler_38,d3dcompiler_39,d3dcompiler_40,d3dcompiler_41,d3dcompiler_42,d3dcompiler_43,d3dcompiler_46,d3dcompiler_47,d3dx10,d3dx10_33,d3dx10_34,d3dx10_35,d3dx10_36,d3dx10_37,d3dx10_38,d3dx10_39,d3dx10_40,d3dx10_41,d3dx10_42,d3dx10_43,d3dx11_42,d3dx11_43,d3dx9_24,d3dx9_25,d3dx9_26,d3dx9_27,d3dx9_28,d3dx9_29,d3dx9_30,d3dx9_31,d3dx9_32,d3dx9_33,d3dx9_34,d3dx9_35,d3dx9_36,d3dx9_37,d3dx9_38,d3dx9_39,d3dx9_40,d3dx9_41,d3dx9_42,d3dx9_43,dxgi,nvapi,nvapi64=n;winemenubuilder="
export STEAM_COMPAT_CLIENT_INSTALL_PATH="/home/william/.local/share/Steam/"
export STEAM_COMPAT_DATA_PATH="/home/william/.wine"
export STEAM_COMPAT_APP_ID="0"
export SteamAppId="0"
export SteamGameId="lutris-game"
export WINE_LARGE_ADDRESS_AWARE="1"
export TERM="xterm"

function log {                                                                                                                                                
    echo $(date --rfc-3339=seconds) RUN_NOITA: $@                                                                                                                        
}                                                                                                                                                             

log "Running on display: $DISPLAY"
log "Running offset: $PID_OFFSET"
for i in $(seq 1 $PID_OFFSET); do
    touch "/tmp/noop.txt"
done

# Restore the games state and config from the main save and the golden config
# respectively.
if [[ "$WINEPREFIX" == "$MAIN_SAVE" ]]; then
    :
else
    log "Setting up prefix: $WINEPREFIX"
    rm -rf $WINEPREFIX
    mkdir -p $WINEPREFIX
    cp -r $MAIN_SAVE/* $WINEPREFIX
fi

rm -rf $WINEPREFIX/drive_c/users/steamuser/AppData/LocalLow/Nolla_Games_Noita/save0*
cp bounce_rl/environments/noita/mod/golden_config.xml \
  $WINEPREFIX/drive_c/users/steamuser/AppData/LocalLow/Nolla_Games_Noita/save_shared/config.xml
# Copy a minimal save file into the environment to disable the intro screen.
cp -r bounce_rl/environments/noita/initial_save00 \
      $WINEPREFIX/drive_c/users/steamuser/AppData/LocalLow/Nolla_Games_Noita/save00

# Working Directory
cd /home/william/.steam/steam/steamapps/common/Noita

# Command
'/home/william/.local/share/Steam/steamapps/common/Proton 8.0/dist/bin/wine' /home/william/.steam/steam/steamapps/common/Noita/noita.exe &
trap "kill $(jobs -p)" EXIT
wait

log "Exiting from run_noita.sh"


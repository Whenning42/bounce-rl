sudo rm -rf '~/test_steam'
rsync -a --exclude='/steamapps/common/' ~/.local/share/Steam/ ~/test_steam/
mkdir ~/test_steam/steamapps/common
cp -r ~/.local/share/Steam/steamapps/common/Noita ~/test_steam/steamapps/common
cp -r ~/.local/share/Steam/steamapps/common/SteamLinuxRuntime_sniper ~/test_steam/steamapps/common
cp -r ~/.local/share/Steam/steamapps/common/Proton\ 8.0 ~/test_steam/steamapps/common
sudo chown -R root ~/test_steam

# These are program configs and are independent of which agent we wish to run.
# NOTE: We probably don't want fps in these run configs.
app_configs = \
    [{
        "conf_title": "Skyrogue",
        #Skyrogue tries launches steam if the working directory isn't the game's directory.,
        "directory": "/home/william/.local/share/Steam/steamapps/common/Sky Rogue",
        "command": "./skyrogue.x86",
        "window_title": "Sky Rogue",
        "x_res": 640,
        "y_res": 480,
    }, {
        "conf_title": "Minecraft",
        "directory": "./",
        # minecraft_command.txt comes from
        # $ ps -eo args | grep inecraft; killall minecraft-launcher
        "command": open("minecraft_command.txt").read(),
        # One's version may differ here.
        "window_title": "Minecraft 1.16.5",
        # Pass in bmp to disable compression
        "extension": ".bmp",
        "x_res": 1280,
        "y_res": 720   ,
    }, {
        "conf_title": "Firefox",
        "directory": "./",
        "command": "firefox",
        "window_title": "Mozilla Firefox",
        "x_res": 960,
        "y_res": 540,
    }, {
        "conf_title": "Art of Rally",
        "directory": "/home/william/.local/share/Steam/steamapps/common/artofrally",
        "command": "steam steam://rungameid/550320",
        "window_title": "art of rally",
        "x_res": 1920,
        "y_res": 1080,
    }]

def LoadAppConfig(config_title):
    for app_conf in app_configs:
        if app_conf["conf_title"] == config_title:
            return app_conf
    return None

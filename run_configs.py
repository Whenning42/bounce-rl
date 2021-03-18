# These are program configs and are independent of which agent we wish to run.
configs = \
    [{
        "conf_title": "Skyrogue",
        #Skyrogue tries launches steam if the working directory isn't the game's directory.,
        "directory": "/home/william/.local/share/Steam/steamapps/common/Sky Rogue",
        "command": "./skyrogue.x86",
        "window_title": "Sky Rogue",
        "fps": 60,
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
        "fps": 30,
        "x_res": 960,
        "y_res": 540,
    }, {
        "conf_title": "Firefox",
        "directory": "./",
        "command": "firefox",
        "window_title": "Mozilla Firefox",
        "fps": 24,
        "x_res": 960,
        "y_res": 540,
    }]

# We might want to add field name validation.

def LoadConfig(config_title):
    for conf in configs:
        if conf["conf_title"] == config_title:
            return conf
    return None

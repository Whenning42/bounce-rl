# A script to mute programs running with pulse audio

IDX=$(pacmd list-sink-inputs | awk '
    $1 == "index:" {idx = $2}
    $1 == "application.process.binary" && $3 == "\"skyrogue.x86\"" {print idx; exit}
')
pacmd set-sink-input-mute "$IDX" 1

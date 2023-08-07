dofile( "data/scripts/lib/coroutines.lua" )

--[[
rl_mod is a Noita mod that logs game state to files for direct use, or
for use with the Noita Gym environment.

Note: Even though this project is Linux only, this mod is running under Wine.
This means lua os.execute calls don't work as expected.

Logged files are:
  /tmp/.../noita_stats.txt - Contains: biome, hp, max_hp, gold, x, y logged at the configured rate
  /tmp/.../noita_notifications.txt - Updated each time the player dies
]]

-- TODO: Make the config loadable from the pipe directory. This would allow configuration from
-- the Gym env.

math.randomseed(os.time())
PIPE_DIR = "/tmp/rl_env"
STATS_EVERY_N_FRAMES = 60
print(" ======== Piping output to: " .. PIPE_DIR .. " ========")

function GetPlayer()
    local players = EntityGetWithTag("player_unit")
    if #players == 0 then return end
    return players[1]
end

function GetPlayerOrCameraPos()
    local player = GetPlayer()
    local x, y = EntityGetTransform(player)
    if x == nil then
        return GameGetCameraPos()
    end
    return x, y
end

function LogStats()
    local player = GetPlayer()
    if player == nil then print("Nil player") return end

    -- Get Health
    local damage_comp = EntityGetFirstComponent(player, "DamageModelComponent")
    if damage_comp == nil then print("Nil damage") return end
    local hp = 25 * ComponentGetValue(damage_comp, "hp")
    local max_hp = 25 * ComponentGetValue(damage_comp, "max_hp")

    -- Get Biome
    local x, y = GetPlayerOrCameraPos()
    local biome = BiomeMapGetName(x, y)

    -- Get Gold
    local wallet = EntityGetFirstComponent(player, "WalletComponent")
    if wallet == nil then print("Nil wallet") return end
    local gold = ComponentGetValue(wallet, "money") + ComponentGetValue(wallet, "money_spent")

    -- Write to file
    local file = io.open(PIPE_DIR .. "/noita_stats.csv", "a")
    file:write(string.format("%s\t%d\t%d\t%d\t%d\t%d\n", biome, hp, max_hp, gold, x, y))
    file:close()
end

function OnWorldPostUpdate()
    local frame = GameGetFrameNum()
    if frame % STATS_EVERY_N_FRAMES == 0 then
        print("====== Stat log ======")
        LogStats()
    end
end

function OnPlayerDied(player)
    -- Log player death signal. The Gym env will recieve the signal and end the run.
    local file = io.open(PIPE_DIR .. "/noita_notifications.txt", "a")
    file:write("died\n")
    file:close()
end

local file = io.open(PIPE_DIR .. "/noita_stats.csv", "a")
file:write("biome, hp, max_hp, gold, x, y\n")
file:close()
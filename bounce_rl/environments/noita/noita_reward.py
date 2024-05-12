from typing import Any, Dict


class NoitaReward:
    """Reward function for Noita.

    The reward function is weighted sum of the following:
    - Changes in hp
    - Changes in max hp
    - Gained gold
    - Newly entered blocks (100x100 px regions of the map)
    - Polymorphed penalty
    """

    def __init__(self):
        self.BLOCK_SIZE = 100
        self.BLOCK_K = 1
        self.LOST_HP_K = 1
        self.GAINED_HP_K = 10
        self.DMAX_HP_K = 5
        self.GAINED_GOLD_K = 0.5
        self.SPENT_GOLD_k = 0.05
        self.POLYMORPHED_K = 3

        self.positions = {}
        self.last_info = None

        """
        TODO: Consider adding exploration state to the environment's state to make
              the environment's state more observable. This could be done with an
              overlay over the game's pixels. Below are some params for calculating
              the grid.

                SCREEN_WIDTH_COORD = 440
                SCREEN_HEIGHT_COORD = 248
                SCREEN_WIDTH_PIX = 640
                SCREEN_HEIGHT_PIX = 360

                x_orig = info['x'] - SCREEN_WIDTH_COORD / 2
                y_orig = info['y'] + 
        """

    def update(self, info: Dict[str, Any]):
        block_x, block_y = info["x"] // self.BLOCK_SIZE, info["y"] // self.BLOCK_SIZE
        if self.last_info is None:
            self.positions[(block_x, block_y)] = 1
            self.last_info = info
            return 0

        reward = 0
        d_hp = info["hp"] - self.last_info["hp"]
        lost_hp, gained_hp = max(0, -d_hp), max(0, d_hp)
        reward += -lost_hp * self.LOST_HP_K + gained_hp * self.GAINED_HP_K

        d_max_hp = info["max_hp"] - self.last_info["max_hp"]
        lost_max_hp, gained_max_hp = max(0, -d_max_hp), max(0, d_max_hp)
        reward += -lost_max_hp * self.DMAX_HP_K + gained_max_hp * self.DMAX_HP_K

        d_gold = info["gold"] - self.last_info["gold"]
        spent_gold, gained_gold = max(0, -d_gold), max(0, d_gold)
        reward += spent_gold * self.SPENT_GOLD_k + gained_gold * self.GAINED_GOLD_K

        reward -= info["polymorphed"] * self.POLYMORPHED_K

        if (block_x, block_y) not in self.positions:
            reward += self.BLOCK_K
            self.positions[(block_x, block_y)] = 1

        self.last_info = info
        return reward

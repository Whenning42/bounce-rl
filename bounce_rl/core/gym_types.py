# Type definitions for Gym-compatible interfaces in BounceRL.

from typing import Any

import numpy as np

GymAction = np.ndarray
GymObservation = np.ndarray

# Info dictionary returned in step tuples
GymInfo = dict[str, Any]

# Step tuple returned by step() and finalize_step()
# (observation, reward, terminated, truncated, info)
GymStepTuple = tuple[GymObservation, float, bool, bool, GymInfo]

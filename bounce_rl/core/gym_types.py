# Type definitions for Gym-compatible interfaces in BounceRL.

from typing import Any, Sequence

import numpy as np

# Note, we define GymAction here not to represent the type of any
# gym action, but specifically just the type of the gym actions
# our environment uses, which is a sequence of key actions, mouse actions
# and mouse positions.
GymAction = Sequence[np.ndarray]
GymObservation = np.ndarray

# Info dictionary returned in step tuples
GymInfo = dict[str, Any]

# Step tuple returned by step() and finalize_step()
# (observation, reward, terminated, truncated, info)
GymStepTuple = tuple[GymObservation, float, bool, bool, GymInfo]

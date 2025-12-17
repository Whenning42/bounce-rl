import numpy as np


class TemplateMatcher:
    def __init__(self, images: np.ndarray):
        self.target = np.mean(images, axis=0)
        close = np.abs(self.target - images) < 3
        self.target_mask = np.all(close, axis=0)

    def matches(self, image: np.ndarray) -> bool:
        close = np.abs(self.target - image) < 3
        print(close.shape, self.target_mask.shape)
        match = np.all(
            np.stack([close, self.target_mask], axis=0),
            axis=0,
        )
        return np.sum(match) > 0.9 * np.sum(self.target_mask)

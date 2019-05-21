import keras
import numpy as np
import util
import matplotlib.pyplot as plt

util.fix_rtx_bug()

import pygame
import os
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0,480)


class Display(object):
    def __init__(self, shape):
        self.d = pygame.display.set_mode(shape)

    def display(self, im):
        im = np.swapaxes(im, 0, 1)
        im = (im * 127.5) + 127.5
        image = np.zeros((im.shape[0], im.shape[1], 3))
        image[:, :, 0] = im
        image[:, :, 1] = im
        image[:, :, 2] = im
        im = image

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        surface = pygame.surfarray.make_surface(im.astype('uint8'))
        self.d.blit(surface, (0, 0))
        pygame.display.update()

class autoencoder_loss(object):
    def __init__(self, autoencoder_path):
        self.autoencoder = keras.models.load_model(autoencoder_path, custom_objects={"keras": keras})
        self.grayscale = np.zeros([480, 640, 1], dtype='float32')
        self.downsampled = np.zeros([240, 320, 1], dtype='float32')
        self.display = Display((320, 240))

    def get_reward(self, state):
        state = self.process_state(state)
        self.display.display(self.autoencoder.predict(state)[0, :, :, 0])
        # self.display.display(state[0, :, :, 0])
        return self.autoencoder.evaluate(state, state, verbose = 0)

    def process_state(self, state):
        # From PIL source code: L = R * 299/1000 + G * 587/1000 + B * 114/1000
        self.grayscale[:, :, 0] = state[:, :, 0] * 299.0/1000 + state[:, :, 1] * 587.0/1000 + state[:, :, 2] * 114.0/1000 
        self.downsampled[:, :, :] = self.grayscale[0::2, 0::2, :]
        self.downsampled = (self.downsampled - 127.5) / 127.5
        return np.array([self.downsampled], dtype='float32')

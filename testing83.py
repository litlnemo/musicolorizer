"""
Your project must have a main function and three or more additional functions. At least three of those additional functions must be accompanied by tests that can be executed with pytest.
Your main function must be in a file called project.py, which should be in the “root” (i.e., top-level folder) of your project.
Your 3 required custom functions other than main must also be in project.py and defined at the same indentation level as main (i.e., not nested under any classes or functions)
"""

import librosa
import numpy as np
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

# set ffmpeg backend
environ["AUDIOTYPE"] = "ffmpeg"
n_fft = 2048 * 4
hop_length = 512

class ColorBar:
    #defining vertical bars in visualizer
    def __init__(self, x, y, freq, color, width=50, min_height=10, max_height=1000, min_decibel=-80, max_decibel=0):
        self.x, self.y, self.freq = x, y, freq
        self.color = color
        self.width, self.min_height, self.max_height = width, min_height, max_height
        self.height = min_height
        self.min_decibel, self.max_decibel = min_decibel, max_decibel

    def update(self, decibel):
        # Static height
        self.height = self.max_height 

        # Gradient effect based on decibel
        gradient_start = np.array([0, 0, 10])  # Start color (e.g., dark blue)
        gradient_end = np.array([0, 0, 255])  # End color (e.g., blue)
        gradient_ratio = limitation(0, 1, (decibel - self.min_decibel) / (self.max_decibel - self.min_decibel))
        self.color = tuple((1 - gradient_ratio) * gradient_start + gradient_ratio * gradient_end)

    def render(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, screen.get_height() - self.height, self.width, self.height))
        
def limitation(min_value, max_value, value):

    if value < min_value:
        return min_value

    if value > max_value:
        return max_value

    return value

def get_decibel(target_time, freq):
    return spectrogram[int(freq * frequencies_index_ratio)][int(target_time * time_index_ratio)]

def main():

    # get song title
    songfile = "winter.wav"

    # Loading audio -- sr=None overrides the default sample rate and uses the file's sample rate
    time_series, sample_rate = librosa.load(songfile, sr=None)

    # amp values using short-time Fourier analysis
    stft = np.abs(librosa.stft(time_series, hop_length=512, n_fft=n_fft))   
    # n_fft = 2048 * 4
    global spectrogram
    spectrogram = librosa.amplitude_to_db(stft, ref=np.max)
    frequencies = librosa.core.fft_frequencies(n_fft=n_fft)

    # time and freq indexes
    times = librosa.core.frames_to_time(np.arange(spectrogram.shape[1]), sr=sample_rate, hop_length=512, n_fft=n_fft)
    global time_index_ratio, frequencies_index_ratio
    time_index_ratio = len(times)/times[len(times) - 1]
    frequencies_index_ratio = len(frequencies)/frequencies[len(frequencies)-1]
    
    #initialize pygame
    pygame.init()

    #define screen size
    info = pygame.display.Info()
    screen_size = int(info.current_w / 2)
    screen_height = info.current_h - 100  # Use current display height
    screen = pygame.display.set_mode([screen_size, screen_height])
    pygame.display.set_caption("Musicolorizer")

    #create colorbars
    bars = []
    frequencies = np.arange(100, 5000, 100)
    r = len(frequencies)
    width_of_bar = screen_size/r
    x = (screen_size - width_of_bar * r) / 2

    for c in frequencies:
        bars.append(ColorBar(x, screen_height, c, (255, 0, 0), max_height=screen_height, width=width_of_bar))
        x += width_of_bar

    t = pygame.time.get_ticks()
    getTicksLastFrame = t

    #load and play
    pygame.mixer.music.load(songfile)
    pygame.mixer.music.play(0)

    # Run until the user asks to quit.
    running = True
    while running:

        t = pygame.time.get_ticks()
        deltaTime = (t - getTicksLastFrame) / 1000.0
        getTicksLastFrame = t

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))

        for b in bars:
            b.update(get_decibel(pygame.mixer.music.get_pos()/1000.0, b.freq))
            b.render(screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
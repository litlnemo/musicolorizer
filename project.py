"""
Sources used to figure out how to use pygame, librosa,  etc. to make a visualizer:
https://medium.com/analytics-vidhya/how-to-create-a-music-visualizer-7fad401f5a69
https://www.pygame.org/docs/
https://librosa.org/doc/latest/
https://www.reddit.com/r/VideoEditing/comments/ssci0l/comment/hwxw2fd/
https://medium.com/@chaosqueenbee/audio-visualizer-6571b9085f0e -- most helpful, her visualizer inspired the look of mine
"""
import librosa
import numpy as np
import random
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

n_fft = 2048 * 4
hop_length = 512

# Keyword-to-color
colormap = {
    'blue': [(0, 0, 50), (0, 0, 255)],  # Blues
    'sad': [(0, 0, 0), (0, 0, 255)],
    'winter': [(0, 0, 0), (0, 0, 255)],
    'happy': [(10, 10, 0), (255, 255, 0)],  # Yellows
    'love': [(10, 0, 0), (255, 105, 180)],  # Pinks
    'red': [(0, 0, 0), (255, 0, 0)],  # Reds
    'green': [(0, 10, 0), (0, 255, 0)],  # Lime Green
    'spring': [(10, 10, 0), (100, 255, 0)],
    'daydreams': [(0, 0, 0), (200, 80, 255)],  # Magenta
}

def get_colorway(title, colormap):
    title_lower = title.lower()

    # Find the first matching keyword
    for key, colors in colormap.items():
        if key in title_lower:
            return colors

    # Random colorway if no keywords match
    return [random_color(), random_color()]

def random_color():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

class ColorBar:
    # Defining vertical bars in visualizer
    def __init__(self, x, y, freq, colorway, width=50, min_height=10, max_height=1000, min_decibel=-80, max_decibel=0):
        self.x, self.y, self.freq = x, y, freq
        self.colorway = colorway  # Store the colorway
        self.width, self.min_height, self.max_height = width, min_height, max_height
        self.height = min_height
        self.min_decibel, self.max_decibel = min_decibel, max_decibel

    def update(self, decibel):
        # Static height
        self.height = self.max_height

        # Gradient effect based on decibel
        gradient_start = np.array(self.colorway[0])  # Start color
        gradient_end = np.array(self.colorway[1])    # End color
        gradient_ratio = limitation(0, 1, (decibel - self.min_decibel) / (self.max_decibel - self.min_decibel))
        self.color = tuple((1 - gradient_ratio) * gradient_start + gradient_ratio * gradient_end)

    def render(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, screen.get_height() - self.height, self.width, self.height))

def limitation(min_value, max_value, value):
    return max(min_value, min(max_value, value))

def get_decibel(target_time, freq):
    return spectrogram[int(freq * frequencies_index_ratio)][int(target_time * time_index_ratio)]

def main():
    # Get song title
    songfile = input("Choose a song: ")

    # set colorway for song title
    colorway = get_colorway(songfile, colormap)

    # Loading audio -- sr=None overrides the default sample rate and uses the file's sample rate
    time_series, sample_rate = librosa.load(songfile, sr=None)

    # Amplitude values using short-time Fourier analysis
    stft = np.abs(librosa.stft(time_series, hop_length=512, n_fft=n_fft))
    global spectrogram
    spectrogram = librosa.amplitude_to_db(stft, ref=np.max)
    frequencies = librosa.mel_frequencies()

    # Time and frequency indexes
    times = librosa.frames_to_time(np.arange(spectrogram.shape[1]), sr=sample_rate, hop_length=512, n_fft=n_fft)
    global time_index_ratio, frequencies_index_ratio
    time_index_ratio = len(times) / times[len(times) - 1]
    frequencies_index_ratio = len(frequencies) / frequencies[len(frequencies) - 1]

    # Initialize pygame
    pygame.init()

    # Define screen size
    info = pygame.display.Info()
    screen_size = int(info.current_w / 2)
    screen_height = info.current_h - 100
    screen = pygame.display.set_mode([screen_size, screen_height])
    pygame.display.set_caption("Musicolorizer")

    # Create color bars
    bars = []
    frequencies = np.arange(100, 5000, 100)
    r = len(frequencies)
    width_of_bar = int(screen_size / r)
    x = int((screen_size - width_of_bar * r) / 2)

    for c in frequencies:
        bars.append(ColorBar(x, screen_height, c, colorway, max_height=screen_height, width=width_of_bar))
        x += width_of_bar

    # Load and play
    pygame.mixer.music.load(songfile)
    pygame.mixer.music.play(0)

    # Run until the user asks to quit
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))

        for b in bars:
            b.update(get_decibel(pygame.mixer.music.get_pos() / 1000.0, b.freq))
            b.render(screen)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()

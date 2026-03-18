"""
Sources used to figure out how to use pygame, librosa,  etc. to make a visualizer:
https://medium.com/analytics-vidhya/how-to-create-a-music-visualizer-7fad401f5a69
https://www.pygame.org/docs/
https://librosa.org/doc/latest/
https://www.reddit.com/r/VideoEditing/comments/ssci0l/comment/hwxw2fd/
https://medium.com/@chaosqueenbee/audio-visualizer-6571b9085f0e -- most helpful, her visualizer inspired the look of mine
"""
import librosa
import os
import numpy as np
import random
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
from colormap import colormap

n_fft = 2048 * 4
hop_length = 512

# colormap was here

def get_title_from_path(filepath):
    """Extract a clean title from a file path by stripping directory and extension."""
    basename = os.path.basename(filepath)
    title, _ = os.path.splitext(basename)
    return title


def get_colorway(title, colormap):
    """Return a list of colorways matched by keywords in the title.
    If no keywords match, return a single random colorway."""
    title_lower = title.lower()
    matched = [colors for key, colors in colormap.items() if key in title_lower]

    if not matched:
        return [[random_color(), random_color()]]

    return matched

def pick_color_for_bar(matched_colorways):
    """Randomly pick one colorway from the list of matched colorways for a single bar."""
    return random.choice(matched_colorways)

def random_color():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

class ColorBar:
    # Defining vertical bars in visualizer
    def __init__(self, x, y, freq, colorway, shape='rectangle', width=50, min_height=10, max_height=1000, min_decibel=-80, max_decibel=0):
        self.x, self.y, self.freq = x, y, freq
        self.colorway = colorway  # Store the colorway
        self.shape = shape # store the shape
        self.width, self.min_height, self.max_height = width, min_height, max_height
        self.height = min_height
        self.min_decibel, self.max_decibel = min_decibel, max_decibel

    def update(self, decibel):
        if self.shape in ('rounded', 'triangle'):
            # Variable height based on decibel level
            height_ratio = limitation(0, 1, (decibel - self.min_decibel) / (self.max_decibel - self.min_decibel))
            self.height = int(self.min_height + height_ratio * (self.max_height - self.min_height))
        else:
            # Static height for all other shapes
            self.height = self.max_height
        # Gradient effect based on decibel (runs for all shapes)
        gradient_start = np.array(self.colorway[0])
        gradient_end = np.array(self.colorway[1])
        gradient_ratio = limitation(0, 1, (decibel - self.min_decibel) / (self.max_decibel - self.min_decibel))
        self.color = tuple((1 - gradient_ratio) * gradient_start + gradient_ratio * gradient_end)

    def render(self, screen):
        if self.shape == 'rectangle':
            pygame.draw.rect(screen, self.color, (self.x, screen.get_height() - self.height, self.width, self.height))
        elif self.shape == 'rounded':
            pygame.draw.rect(screen, self.color, (self.x, screen.get_height() - self.height, self.width, self.height), border_radius=self.width // 2)
        elif self.shape == 'triangle':
            top_x = self.x + self.width // 2
            top_y = screen.get_height() - self.height
            bottom_left = (self.x, screen.get_height())
            bottom_right = (self.x + self.width, screen.get_height())
            top = (top_x, top_y)
            pygame.draw.polygon(screen, self.color, [bottom_left, bottom_right, top])
        elif self.shape == 'tapered':
            narrow_width = self.width // 3
            offset = (self.width - narrow_width) // 2
            bottom_left = (self.x + offset, screen.get_height())
            bottom_right = (self.x + offset + narrow_width, screen.get_height())
            top_left = (self.x, screen.get_height() - self.height)
            top_right = (self.x + self.width, screen.get_height() - self.height)
            pygame.draw.polygon(screen, self.color, [bottom_left, bottom_right, top_right, top_left])
        elif self.shape == 'wavy':
            points = []
            segments = 8  # number of segments along the height
            segment_height = self.height // segments
            wobble = self.width // 4  # how much the edges can wobble

            # Build left edge going upward
            for i in range(segments + 1):
                y = screen.get_height() - (i * segment_height)
                x = self.x + random.randint(-wobble, wobble)
                points.append((x, y))

            # Build right edge going downward
            for i in range(segments, -1, -1):
                y = screen.get_height() - (i * segment_height)
                x = self.x + self.width + random.randint(-wobble, wobble)
                points.append((x, y))

            pygame.draw.polygon(screen, self.color, points)

def limitation(min_value, max_value, value):
    return max(min_value, min(max_value, value))

def get_decibel(target_time, freq):
    return spectrogram[int(freq * frequencies_index_ratio)][int(target_time * time_index_ratio)]

def main():
    # Get song file and title
    songfile = input("Choose a song: ")
    title = get_title_from_path(songfile)
    colorway = get_colorway(title, colormap)

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

    SHAPES = ['rectangle', 'rounded', 'triangle', 'tapered', 'wavy']
    # SHAPES = ['tapered', 'rounded']
    shape = random.choice(SHAPES)

    # Create color bars
    bars = []
    frequencies = np.arange(100, 5000, 100)
    r = len(frequencies)
    width_of_bar = int(screen_size / r)   
    x = int((screen_size - width_of_bar * r) / 2)

    for c in frequencies:
        bars.append(ColorBar(x, screen_height, c, pick_color_for_bar(colorway), shape=shape, max_height=screen_height, width=width_of_bar))
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

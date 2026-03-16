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
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

n_fft = 2048 * 4
hop_length = 512

# Keyword-to-color
colormap = {
    # Original entries
    'blue':      [(0, 0, 50),   (0, 0, 255)],    # deep navy → bright blue
    'sad':       [(0, 0, 0),    (0, 0, 255)],    # black → bright blue
    'winter':    [(0, 0, 0),    (0, 0, 255)],    # black → bright blue
    'happy':     [(10, 10, 0),  (255, 255, 0)],  # near black → bright yellow
    'love':      [(10, 0, 0),   (255, 105, 180)],# near black → hot pink
    'red':       [(0, 0, 0),    (255, 0, 0)],    # black → bright red
    'green':     [(0, 10, 0),   (0, 255, 0)],    # near black → lime green
    'spring':    [(10, 10, 0),  (100, 255, 0)],  # near black → yellow-green
    'daydreams': [(0, 0, 0),    (200, 80, 255)], # black → purple-magenta
    # Literal color words
    'gold':      [(50, 40, 0),  (255, 215, 0)],  # dark gold → bright yellow-gold
    'silver':    [(30, 30, 30), (192, 192, 192)],# dark grey → silver
    'purple':    [(0, 0, 30),   (120, 0, 255)],  # deep blue-black → blue-purple
    'violet':    [(30, 0, 20),  (238, 130, 238)],# deep red-purple → soft violet-pink
    'orange':    [(50, 15, 0),  (255, 140, 0)],  # dark orange → vivid orange
    'pink':      [(40, 0, 20),  (255, 182, 193)],# deep rose → light pink
    'black':     [(0, 0, 0),    (80, 80, 80)],   # black → dark grey
    'white':     [(40, 40, 40), (255, 255, 255)],# dark grey → pure white
    'gray':      [(20, 20, 20), (180, 180, 180)],# near black → medium grey
    'grey':      [(20, 20, 20), (180, 180, 180)],# near black → medium grey
    # Interpretive/emotional
    'money':     [(0, 25, 10),  (100, 150, 85)], # dark green → muted dollar-bill green
    'storm':     [(10, 15, 30), (180, 210, 255)],# dark blue-grey → electric blue-white
    'snow':      [(20, 25, 40), (220, 235, 245)],# dark grey-blue → icy white
    'ocean':     [(0, 10, 40),  (0, 200, 180)],  # deep navy → teal-cyan
    'sea':       [(0, 10, 40),  (0, 200, 180)],  # deep navy → teal-cyan
    'forest':    [(0, 15, 5),   (55, 100, 50)],  # near black → muted pine/evergreen green
    'smoke':     [(20, 20, 25), (170, 175, 185)],# dark grey → pale blue-grey
    'anger':     [(10, 0, 0),   (255, 20, 0)],   # near black → intense red-orange
    'angry':     [(10, 0, 0),   (255, 20, 0)],   # near black → intense red-orange
    'lonely':    [(15, 20, 30), (100, 110, 130)],# dark blue-grey → muted slate
    'joy':       [(60, 20, 0),  (255, 220, 30)], # deep orange → bright warm yellow
    'magic':     [(10, 0, 15),  (255, 0, 200)],  # purple-black → bright magenta
    'cold':      [(0, 5, 30),   (180, 215, 240)],# dark navy → icy pale blue
    'blood':     [(20, 0, 0),   (200, 0, 0)],    # very dark red → bright red
    'rose':      [(40, 5, 10),  (255, 160, 180)],# dark red → soft pink
    'shadow':    [(0, 0, 0),    (90, 85, 100)],  # black → dark cool grey with purple tint
    'electric':  [(0, 5, 30),   (80, 240, 255)], # dark blue → bright cyan
    'hope':      [(60, 35, 0),  (255, 190, 80)], # dark amber → warm gold
    'dark':      [(5, 5, 5),    (55, 45, 60)],   # near black → very dark purple-grey
    'darkness':  [(5, 5, 5),    (55, 45, 60)],   # near black → very dark purple-grey
    'fire':      [(60, 5, 0),   (255, 120, 0)],  # dark red → bright orange
    'flame':     [(60, 5, 0),   (255, 120, 0)],  # dark red → bright orange
    'dream':     [(30, 10, 40), (200, 170, 255)],# deep purple → soft lavender
    'ghost':     [(10, 20, 20), (200, 220, 215)],# dark grey-green → pale cool white
    'haunted':   [(10, 20, 20), (200, 220, 215)],# dark grey-green → pale cool white
    'rain':      [(15, 20, 35), (140, 170, 200)],# dark grey-blue → muted steel blue
    'sun':       [(60, 30, 0),  (255, 230, 50)], # dark orange → bright warm yellow
    'sunshine':  [(60, 30, 0),  (255, 230, 50)], # dark orange → bright warm yellow
    'night':     [(5, 5, 20),   (40, 20, 80)],   # near black → deep indigo
}

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

    # Create color bars
    bars = []
    frequencies = np.arange(100, 5000, 100)
    r = len(frequencies)
    width_of_bar = int(screen_size / r)   
    x = int((screen_size - width_of_bar * r) / 2)

    for c in frequencies:
        bars.append(ColorBar(x, screen_height, c, pick_color_for_bar(colorway), max_height=screen_height, width=width_of_bar))
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

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
import mutagen
from colormap import colormap, shapemap

n_fft = 2048 * 4
hop_length = 512

# How the "Artist — Title" text in the bottom-left corner behaves:
#   'always' - visible for the whole song
#   'fade'   - shown at the start of the song, then fades out for good
#   'cycle'  - shown at the start, fades out, then comes back now and then
TITLE_MODE = 'cycle'
TITLE_SHOW_SECONDS = 5     # how long the text stays at full strength
TITLE_FADE_SECONDS = 1     # how long each fade out (or back in) takes
TITLE_HIDDEN_SECONDS = 20  # in 'cycle' mode, how long it stays hidden between appearances

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

SHAPES = ['rectangle', 'rounded', 'triangle', 'tapered', 'wavy']

def get_shape(title):
    """Return the bar shape matched by keywords in the title.
    If keywords for several shapes match, the first shape in shapemap wins.
    If nothing matches, return a random shape."""
    title_lower = title.lower()
    for shape, keywords in shapemap.items():
        if any(keyword in title_lower for keyword in keywords):
            return shape
    return random.choice(SHAPES)

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
    # Clamp both indexes so the last frame (or a pos of -1 after the song ends) can't overrun the spectrogram
    freq_index = limitation(0, spectrogram.shape[0] - 1, int(freq * frequencies_index_ratio))
    time_index = limitation(0, spectrogram.shape[1] - 1, int(target_time * time_index_ratio))
    return spectrogram[freq_index][time_index]


# ---------- Playlists ----------

AUDIO_EXTENSIONS = ('.mp3', '.wav', '.flac')

# Posted by the pygame mixer when a song finishes playing
SONG_END = pygame.USEREVENT + 1

# What happened to a song: it played to the end, the user skipped it,
# the user quit, or it couldn't be loaded at all
ENDED, NEXT, QUIT, UNPLAYABLE = 'ended', 'next', 'quit', 'unplayable'


def clean_path(path):
    """Strip whitespace and any surrounding quotes (e.g. from drag-and-drop) from a typed path."""
    path = path.strip()
    if len(path) >= 2 and path[0] == path[-1] and path[0] in ('"', "'"):
        path = path[1:-1].strip()
    return path


def is_audio_file(path):
    """True if the path has a supported audio extension (case-insensitive)."""
    return path.lower().endswith(AUDIO_EXTENSIONS)


def scan_folder(folder):
    """Return every supported audio file directly inside a folder, sorted alphabetically by filename."""
    names = [name for name in os.listdir(folder)
             if is_audio_file(name) and os.path.isfile(os.path.join(folder, name))]
    names.sort(key=str.lower)
    return [os.path.join(folder, name) for name in names]


def build_playlist(user_input):
    """Turn what the user typed into a list of song paths.
    Accepts a single audio file, several paths separated by commas, or a folder."""
    whole = clean_path(user_input)
    if not whole:
        return []
    # A folder plays everything in it
    if os.path.isdir(whole):
        return scan_folder(whole)
    # A single existing file is taken as-is, even if its name contains a comma
    if os.path.isfile(whole):
        return [whole]
    # Otherwise, treat it as a comma-separated list
    return [path for path in (clean_path(part) for part in user_input.split(',')) if path]


def next_action(event):
    """Decide what an event means for playback: QUIT, NEXT, ENDED, or None (keep playing)."""
    if event.type == pygame.QUIT:
        return QUIT
    if event.type == SONG_END:
        return ENDED
    if event.type == pygame.KEYDOWN:
        if event.key in (pygame.K_q, pygame.K_ESCAPE):
            return QUIT
        if event.key in (pygame.K_n, pygame.K_RIGHT):
            return NEXT
    return None


def analyze_song(songfile):
    """Load a song with librosa and store its spectrogram for get_decibel.
    Returns True on success, or prints a message and returns False if it can't be read."""
    global spectrogram, time_index_ratio, frequencies_index_ratio
    try:
        # sr=None overrides the default sample rate and uses the file's sample rate
        time_series, sample_rate = librosa.load(songfile, sr=None)
    except Exception as error:
        print(f"Couldn't read {songfile} ({error}). Skipping it.")
        return False

    # Amplitude values using short-time Fourier analysis
    stft = np.abs(librosa.stft(time_series, hop_length=hop_length, n_fft=n_fft))
    spectrogram = librosa.amplitude_to_db(stft, ref=np.max)
    frequencies = librosa.mel_frequencies()

    # Time and frequency indexes
    times = librosa.frames_to_time(np.arange(spectrogram.shape[1]), sr=sample_rate, hop_length=hop_length, n_fft=n_fft)
    if len(times) < 2 or times[-1] <= 0:
        print(f"{songfile} is too short to visualize. Skipping it.")
        return False
    time_index_ratio = len(times) / times[len(times) - 1]
    frequencies_index_ratio = len(frequencies) / frequencies[len(frequencies) - 1]
    return True


def build_bars(colorway, shape, screen_size, screen_height):
    """Create one row of color bars across the screen, all in the given shape."""
    bars = []
    frequencies = np.arange(100, 5000, 100)
    r = len(frequencies)
    width_of_bar = int(screen_size / r)
    x = int((screen_size - width_of_bar * r) / 2)

    for c in frequencies:
        bars.append(ColorBar(x, screen_height, c, pick_color_for_bar(colorway), shape=shape, max_height=screen_height, width=width_of_bar))
        x += width_of_bar
    return bars


def show_loading(screen, title):
    """Show the song title on a black screen while the song is being analyzed."""
    pygame.display.set_caption(f"Musicolorizer — loading {title}")
    screen.fill((0, 0, 0))
    try:
        font = pygame.font.Font(None, 36)
        text = font.render(f"Loading {title}…", True, (200, 200, 200))
        screen.blit(text, text.get_rect(center=screen.get_rect().center))
    except pygame.error:
        pass  # No font support: a black screen is fine
    pygame.display.flip()
    pygame.event.pump()


# ---------- Now playing: artist and title in the corner ----------

TITLE_MODES = ('always', 'fade', 'cycle')


def tag_text(tags, keys):
    """The first non-empty text found under any of the keys, or None.
    Handles both mutagen's simple tags (a list of strings) and raw ID3 frames (which have .text)."""
    for key in keys:
        value = tags.get(key)
        if value is None:
            continue
        if hasattr(value, 'text'):
            value = value.text
        if isinstance(value, str):
            value = [value]
        parts = [str(part).strip() for part in value if str(part).strip()]
        if parts:
            return ", ".join(parts)
    return None


def read_tags(songfile):
    """Return (artist, title) from the file's tags. Either is None if missing or unreadable."""
    try:
        audio = mutagen.File(songfile, easy=True)
    except Exception:
        return None, None
    if audio is None or not audio.tags:
        return None, None
    # MP3 and FLAC give simple 'artist'/'title' keys; WAV gives raw ID3 frames (TPE1/TIT2)
    artist = tag_text(audio.tags, ('artist', 'TPE1'))
    title = tag_text(audio.tags, ('title', 'TIT2'))
    return artist, title


def get_display_info(songfile):
    """The text to show for a song: "Artist — Title" if there's an artist tag, otherwise just the title.
    The title comes from the tags if present, else from the filename (as before)."""
    artist, title = read_tags(songfile)
    title = title or get_title_from_path(songfile)
    return f"{artist} — {title}" if artist else title


def title_alpha(elapsed, mode=None):
    """How visible the corner text is (0.0 hidden to 1.0 full) at a given number of seconds into the song."""
    mode = TITLE_MODE if mode is None else mode
    if mode not in TITLE_MODES:
        raise ValueError(f"TITLE_MODE must be one of {TITLE_MODES}, not {mode!r}")
    if mode == 'always':
        return 1.0

    show, fade, hidden = TITLE_SHOW_SECONDS, TITLE_FADE_SECONDS, TITLE_HIDDEN_SECONDS
    t = max(0.0, elapsed)
    if mode == 'cycle':
        # One cycle: show, fade out, hidden, fade back in; then it repeats
        t %= show + fade + hidden + fade
        if t >= show + fade + hidden:
            return (t - show - fade - hidden) / fade  # fading back in
    if t < show:
        return 1.0
    if t < show + fade:
        return 1.0 - (t - show) / fade  # fading out
    return 0.0


def shorten_to_width(font, text, max_width):
    """Cut text down with '...' until it fits in max_width pixels."""
    if font.size(text)[0] <= max_width:
        return text
    while len(text) > 1 and font.size(text + "...")[0] > max_width:
        text = text[:-1]
    return text.rstrip() + "..."


TITLE_MARGIN = 16
TITLE_OUTLINE = 2


def make_title_image(text, max_width):
    """Render the corner text once per song: light text with a dark outline so it reads over any bars.
    Returns None if pygame can't draw text."""
    try:
        font = pygame.font.Font(None, 36)
    except pygame.error:
        return None
    text = shorten_to_width(font, text, max(1, max_width - 2 * TITLE_OUTLINE))
    light = font.render(text, True, (235, 235, 235))
    dark = font.render(text, True, (0, 0, 0))
    o = TITLE_OUTLINE
    image = pygame.Surface((light.get_width() + 2 * o, light.get_height() + 2 * o), pygame.SRCALPHA)
    for dx in (-o, 0, o):
        for dy in (-o, 0, o):
            if dx or dy:
                image.blit(dark, (o + dx, o + dy))
    image.blit(light, (o, o))
    return image


def draw_title(screen, image, alpha):
    """Draw the corner text in the bottom-left corner at the given strength (0.0-1.0)."""
    if image is None or alpha <= 0:
        return
    image.set_alpha(int(round(255 * min(1.0, alpha))))
    screen.blit(image, (TITLE_MARGIN, screen.get_height() - image.get_height() - TITLE_MARGIN))


def play_song(screen, songfile):
    """Analyze and visualize one song until it ends, is skipped, or the user quits.
    Returns ENDED, NEXT, QUIT, or UNPLAYABLE."""
    if not os.path.isfile(songfile):
        print(f"Can't find {songfile}. Skipping it.")
        return UNPLAYABLE

    # Each song gets its own title-based colorway and shape (random shape if no keyword matches)
    title = get_title_from_path(songfile)
    colorway = get_colorway(title, colormap)
    shape = get_shape(title)
    # What's shown in the corner and the caption (artist/title tags if the file has them);
    # colors and shape above still come from the filename title
    display = get_display_info(songfile)

    show_loading(screen, title)
    if not analyze_song(songfile):
        return UNPLAYABLE

    bars = build_bars(colorway, shape, screen.get_width(), screen.get_height())

    # Load and play
    try:
        pygame.mixer.music.load(songfile)
    except pygame.error as error:
        print(f"Couldn't play {songfile} ({error}). Skipping it.")
        return UNPLAYABLE
    pygame.event.clear(SONG_END)  # drop any end event left over from the previous song
    pygame.mixer.music.play(0)
    pygame.display.set_caption(f"Musicolorizer — {display}")
    title_image = make_title_image(display, screen.get_width() - 2 * TITLE_MARGIN)

    # Run until the song ends, the user skips, or the user quits
    while True:
        for event in pygame.event.get():
            action = next_action(event)
            if action:
                pygame.mixer.music.stop()
                pygame.event.clear(SONG_END)  # stopping can post an end event; don't let it skip the next song
                return action

        screen.fill((0, 0, 0))

        for b in bars:
            b.update(get_decibel(pygame.mixer.music.get_pos() / 1000.0, b.freq))
            b.render(screen)

        # The corner text goes on top of the bars. Its timer is the song's play position,
        # so it starts over for each song and doesn't advance if playback is paused.
        draw_title(screen, title_image, title_alpha(max(0, pygame.mixer.music.get_pos()) / 1000.0))

        pygame.display.flip()


def run_playlist(screen, playlist):
    """Play each song in order. Returns how many songs actually played."""
    played = 0
    for songfile in playlist:
        result = play_song(screen, songfile)
        if result == UNPLAYABLE:
            continue
        played += 1
        if result == QUIT:
            break
    return played


def main():
    # Get a song, several comma-separated songs, or a folder
    playlist = build_playlist(input("Choose a song: "))
    if not playlist:
        print("No songs to play. Enter an audio file, several files separated by commas, or a folder.")
        return

    # Report missing files up front, and don't open a window if nothing is left
    found = []
    for songfile in playlist:
        if os.path.isfile(songfile):
            found.append(songfile)
        else:
            print(f"Can't find {songfile}. Skipping it.")
    if not found:
        print("None of those songs could be found, so there's nothing to play.")
        return

    # Initialize pygame
    pygame.init()

    # Define screen size
    info = pygame.display.Info()
    screen_size = int(info.current_w / 2)
    screen_height = info.current_h - 100
    screen = pygame.display.set_mode([screen_size, screen_height])
    pygame.display.set_caption("Musicolorizer")
    pygame.mixer.music.set_endevent(SONG_END)

    played = run_playlist(screen, found)

    pygame.quit()
    if played == 0:
        print("None of those songs could be played.")

if __name__ == "__main__":
    main()

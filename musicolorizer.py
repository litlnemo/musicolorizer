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
import sys
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
# The user went back a track (on the first song, that restarts it)
PREVIOUS = 'previous'
# The user pressed Previous partway into a song, so it starts over instead
RESTART = 'restart'
# Like most players: Previous more than this many seconds into a song restarts it
PREVIOUS_RESTART_SECONDS = 3
# Pausing doesn't end a song; play_song handles it and keeps going
PAUSE = 'pause'
# Neither does hiding or showing the playlist panel
TOGGLE_PANEL = 'toggle_panel'


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


def playlist_from_paths(paths):
    """Turn a list of chosen or typed paths into one playlist.
    Each path goes through build_playlist, so a folder plays every song in it
    (alphabetically) and a file plays as itself."""
    playlist = []
    for path in paths:
        playlist.extend(build_playlist(path))
    return playlist


def existing_songs(playlist):
    """Return the songs that exist, printing a message for each one that doesn't."""
    found = []
    for songfile in playlist:
        if os.path.isfile(songfile):
            found.append(songfile)
        else:
            print(f"Can't find {songfile}. Skipping it.")
    return found


# ---------- Song chooser ----------

AUDIO_FILETYPES = [("Audio files", "*.mp3 *.wav *.flac"), ("All files", "*")]

# Where the chooser remembers the last folder songs were picked from, so the next run starts there
LAST_FOLDER_FILE = os.path.join(os.path.expanduser("~"), ".musicolorizer_last_folder")


def load_last_folder():
    """The folder songs were last picked from, or None if there isn't one (or it no longer exists)."""
    try:
        with open(LAST_FOLDER_FILE, encoding="utf-8") as f:
            folder = f.read().strip()
    except OSError:
        return None
    return folder if folder and os.path.isdir(folder) else None


def save_last_folder(folder):
    """Remember a folder for next time. Failing to save is harmless, so errors are ignored."""
    try:
        with open(LAST_FOLDER_FILE, "w", encoding="utf-8") as f:
            f.write(folder)
    except OSError:
        pass


def start_folder():
    """Where the dialogs open: the last folder used, else ~/Music, else the home folder."""
    last = load_last_folder()
    if last:
        return last
    music = os.path.join(os.path.expanduser("~"), "Music")
    return music if os.path.isdir(music) else os.path.expanduser("~")


def folder_of_choice(paths):
    """The folder to remember after a pick: the chosen folder, or the folder holding the first chosen song."""
    if not paths:
        return None
    first = paths[0]
    return first if os.path.isdir(first) else os.path.dirname(os.path.abspath(first))


def mac_message(text):
    """The dialog's 'message' option, which only exists on macOS (elsewhere Tk rejects it)."""
    return {"message": text} if sys.platform == "darwin" else {}


class NativeChooser:
    """The real chooser: a small window asking "songs or a folder?", then the system's file dialog.
    Uses tkinter (standard library). Raises ImportError if tkinter isn't available."""

    def __init__(self):
        import tkinter
        from tkinter import filedialog
        self.tkinter, self.filedialog = tkinter, filedialog
        self.root = tkinter.Tk()
        self.root.withdraw()

    def ask_mode(self):
        """Ask whether to pick songs or a folder. Returns 'songs', 'folder', or None for Cancel."""
        tk, root = self.tkinter, self.root
        choice = {"mode": None}

        def pick(mode):
            choice["mode"] = mode
            root.quit()

        root.title("Musicolorizer")
        frame = tk.Frame(root, padx=24, pady=18)
        frame.pack()
        tk.Label(frame, text="What would you like to play?").pack(pady=(0, 14))
        row = tk.Frame(frame)
        row.pack()
        for text, mode in [("Pick songs…", "songs"), ("Pick a folder…", "folder"), ("Cancel", None)]:
            tk.Button(row, text=text, command=lambda m=mode: pick(m)).pack(side="left", padx=4)
        root.protocol("WM_DELETE_WINDOW", lambda: pick(None))
        root.bind("<Escape>", lambda event: pick(None))
        root.bind("<Return>", lambda event: pick("songs"))

        # Centre the window on the screen and bring it in front of the terminal
        root.update_idletasks()
        w, h = root.winfo_reqwidth(), root.winfo_reqheight()
        x = (root.winfo_screenwidth() - w) // 2
        y = (root.winfo_screenheight() - h) // 3
        root.geometry(f"+{x}+{y}")
        root.deiconify()
        root.lift()
        root.attributes("-topmost", True)
        root.focus_force()
        root.mainloop()

        root.attributes("-topmost", False)
        frame.destroy()
        root.withdraw()
        root.update()
        return choice["mode"]

    # The file dialogs are opened WITHOUT a parent window. On macOS, Tk turns a dialog
    # with a parent into a "sheet" stuck to that window; with the hidden root as parent,
    # the sheet ended up half off-screen and couldn't be moved. With no parent, macOS
    # shows a normal free-standing open panel that can be moved and resized.

    def ask_files(self, start_dir):
        return self.filedialog.askopenfilenames(
            title="Musicolorizer: choose songs", initialdir=start_dir, filetypes=AUDIO_FILETYPES,
            **mac_message("Choose one or more songs to play"))

    def ask_folder(self, start_dir):
        return self.filedialog.askdirectory(
            title="Musicolorizer: choose a folder", initialdir=start_dir, mustexist=True,
            **mac_message("Choose a folder; every song in it will play"))

    def close(self):
        try:
            self.root.destroy()
        except Exception:
            pass


def native_dialogs():
    """Create the real chooser. (Tests replace this with a fake so no window opens.)"""
    return NativeChooser()


def choose_songs(ask_mode, ask_files, ask_folder, start_dir):
    """Ask "songs or a folder?", then open that dialog at start_dir.
    Returns the chosen paths, or [] if the user cancelled at any step."""
    mode = ask_mode()
    if mode == "songs":
        files = ask_files(start_dir)
        return list(files) if files else []
    if mode == "folder":
        folder = ask_folder(start_dir)
        return [folder] if folder else []
    return []


def ask_for_songs():
    """Open the song chooser where the user last picked songs, and remember where they picked from this time.
    Falls back to the old typed prompt if no chooser can be shown."""
    try:
        chooser = native_dialogs()
    except Exception as error:  # tkinter missing, or no display for it
        print(f"Couldn't open the song chooser ({error}).")
        print("Tip: you can also run  python musicolorizer.py <song, songs, or folder>")
        typed = input("Choose a song: ")
        return [typed] if typed.strip() else []
    try:
        chosen = choose_songs(chooser.ask_mode, chooser.ask_files, chooser.ask_folder, start_folder())
    finally:
        chooser.close()
    if chosen:
        save_last_folder(folder_of_choice(chosen))
    return chosen


# ---------- Playback state ----------

class PlaybackState:
    """What the playlist panel shows: the songs, which one is current, which couldn't play, whether it's paused,
    and whether the panel itself is showing."""

    def __init__(self, songs):
        self.songs = list(songs)
        self.index = 0
        self.paused = False
        self.unplayable = set()
        # A new playlist always starts with the panel showing, so nobody gets stuck with it hidden.
        # start() leaves this alone, so a hidden panel stays hidden from one song to the next.
        self.panel_visible = True
        self._titles = None  # filled in the first time the panel asks for titles

    def start(self, index):
        """Make the song at index the current song. A new song always starts unpaused."""
        self.index = index
        self.paused = False

    def mark_unplayable(self, index):
        self.unplayable.add(index)

    def toggle_pause(self):
        """Flip between paused and playing. Returns True if now paused."""
        self.paused = not self.paused
        return self.paused

    def toggle_panel(self):
        """Hide the playlist panel if it's showing, or show it if it's hidden. Returns True if now showing."""
        self.panel_visible = not self.panel_visible
        return self.panel_visible

    @property
    def current_song(self):
        return self.songs[self.index] if self.songs else None

    @property
    def titles(self):
        """The panel row text for each song: the same "Artist — Title" as the corner title.
        Tags are read once and remembered, since the panel is drawn every frame."""
        if self._titles is None:
            self._titles = [get_display_info(song) for song in self.songs]
        return self._titles


# The playlist being played by run_playlist, so play_song can show it
now_playing = None


def visible_range(index, total, rows):
    """Which slice of a long playlist to show: keep the current song near the top, with a couple of earlier songs above it."""
    if total <= rows:
        return 0, total
    start = max(0, min(index - 2, total - rows))
    return start, start + rows


# ---------- On-screen controls ----------

PANEL_MARGIN = 12
PANEL_PADDING = 10
BUTTON_HEIGHT = 34
BUTTON_GAP = 8
ROW_HEIGHT = 24
MAX_ROWS = 8


def panel_width(screen_size):
    return max(60, min(380, screen_size[0] - 2 * PANEL_MARGIN))


def control_layout(screen_size):
    """Where the Previous, Pause, Skip and Quit buttons go, as {action: pygame.Rect}.
    All four share the panel's top row evenly; the panel never widens for them."""
    actions = (PREVIOUS, PAUSE, NEXT, QUIT)
    inner = panel_width(screen_size) - 2 * PANEL_PADDING
    button_width = max(1, (inner - (len(actions) - 1) * BUTTON_GAP) // len(actions))
    x = PANEL_MARGIN + PANEL_PADDING
    y = PANEL_MARGIN + PANEL_PADDING
    rects = {}
    for action in actions:
        rects[action] = pygame.Rect(x, y, button_width, BUTTON_HEIGHT)
        x += button_width + BUTTON_GAP
    return rects


CHIP_LABEL = "Show playlist (H)"
CHIP_WIDTH = 170


def chip_layout(screen_size):
    """Where the small "Show playlist (H)" chip goes while the panel is hidden: the panel's top-left corner."""
    return pygame.Rect(PANEL_MARGIN, PANEL_MARGIN, min(CHIP_WIDTH, panel_width(screen_size)), BUTTON_HEIGHT)


def draw_chip(screen, fonts, mouse_pos=(-1, -1)):
    """Draw the "Show playlist (H)" chip in place of the hidden panel. Returns {TOGGLE_PANEL: rect}."""
    rect = chip_layout(screen.get_size())
    chip = pygame.Surface(rect.size, pygame.SRCALPHA)
    fill = (95, 95, 95, 210) if rect.collidepoint(mouse_pos) else (0, 0, 0, 170)
    pygame.draw.rect(chip, fill, chip.get_rect(), border_radius=6)
    screen.blit(chip, rect.topleft)
    pygame.draw.rect(screen, (150, 150, 150), rect, width=1, border_radius=6)
    draw_text(screen, fonts, "button", CHIP_LABEL, (235, 235, 235), 0, 0, rect.width - 8, center_in=rect)
    return {TOGGLE_PANEL: rect}


def load_fonts():
    """Fonts for the panel, or None if pygame can't draw text."""
    try:
        # "control" is a little smaller than "button" (the Show playlist chip) so four buttons' labels fit in one row
        return {"button": pygame.font.Font(None, 24), "control": pygame.font.Font(None, 20), "row": pygame.font.Font(None, 24), "header": pygame.font.Font(None, 22)}
    except pygame.error:
        return None


def shorten_to_width(font, text, max_width):
    """Cut text down (used by the playlist panel and the corner title) with '...' until it fits in max_width pixels."""
    if font.size(text)[0] <= max_width:
        return text
    while len(text) > 1 and font.size(text + "...")[0] > max_width:
        text = text[:-1]
    return text.rstrip() + "..."


def draw_text(screen, fonts, kind, text, color, x, y, max_width, center_in=None):
    if not fonts:
        return
    font = fonts[kind]
    image = font.render(shorten_to_width(font, text, max_width), True, color)
    if center_in:
        screen.blit(image, image.get_rect(center=center_in.center))
    else:
        screen.blit(image, (x, y + (ROW_HEIGHT - image.get_height()) // 2))


def panel_header(state):
    """The line above the playlist rows: "Playlist: N of M", or "Now playing" when there's only one song
    (one song isn't a playlist). "   PAUSED" is added while paused."""
    if len(state.songs) == 1:
        header = "Now playing"
    else:
        header = f"Playlist: {state.index + 1} of {len(state.songs)}"
    return header + ("   PAUSED" if state.paused else "")


def draw_overlay(screen, state, fonts, mouse_pos=(-1, -1)):
    """Draw the playlist panel and control buttons over the bars. Returns {action: rect} for whatever
    is clickable right now: the Pause/Skip/Quit buttons, or just the "Show playlist" chip if the panel is hidden."""
    if not state.panel_visible:
        return draw_chip(screen, fonts, mouse_pos)

    buttons = control_layout(screen.get_size())
    width = panel_width(screen.get_size())
    start, end = visible_range(state.index, len(state.songs), MAX_ROWS)
    more = len(state.songs) - end
    rows = (end - start) + (1 if more else 0)
    height = 2 * PANEL_PADDING + BUTTON_HEIGHT + 8 + ROW_HEIGHT + rows * ROW_HEIGHT

    # Translucent background so the bars show through
    panel = pygame.Surface((width, height), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 170))
    screen.blit(panel, (PANEL_MARGIN, PANEL_MARGIN))

    # Buttons
    labels = {PREVIOUS: "Prev (<)", PAUSE: "Resume (P)" if state.paused else "Pause (P)", NEXT: "Skip (>)", QUIT: "Quit (Q)"}
    for action, rect in buttons.items():
        if action == PAUSE and state.paused:
            fill = (70, 110, 190)
        elif rect.collidepoint(mouse_pos):
            fill = (95, 95, 95)
        else:
            fill = (55, 55, 55)
        pygame.draw.rect(screen, fill, rect, border_radius=6)
        pygame.draw.rect(screen, (150, 150, 150), rect, width=1, border_radius=6)
        draw_text(screen, fonts, "control", labels[action], (235, 235, 235), 0, 0, rect.width - 8, center_in=rect)

    # Playlist header and rows
    x = PANEL_MARGIN + PANEL_PADDING
    text_width = width - 2 * PANEL_PADDING - 18
    y = PANEL_MARGIN + PANEL_PADDING + BUTTON_HEIGHT + 8
    draw_text(screen, fonts, "header", panel_header(state), (160, 160, 160), x, y, width - 2 * PANEL_PADDING)
    y += ROW_HEIGHT

    titles = state.titles
    for i in range(start, end):
        if i == state.index:
            pygame.draw.rect(screen, (60, 60, 75), (x - 4, y + 1, width - 2 * PANEL_PADDING + 8, ROW_HEIGHT - 2), border_radius=4)
            # A small "playing" triangle in front of the current song
            cy = y + ROW_HEIGHT // 2
            pygame.draw.polygon(screen, (255, 255, 255), [(x, cy - 6), (x, cy + 6), (x + 10, cy)])
            color = (255, 255, 255)
        elif i in state.unplayable:
            color = (110, 110, 110)
        else:
            color = (190, 190, 190)
        label = f"{i + 1}. {titles[i]}" + ("  (can't play)" if i in state.unplayable else "")
        draw_text(screen, fonts, "row", label, color, x + 18, y, text_width)
        y += ROW_HEIGHT
    if more:
        draw_text(screen, fonts, "row", f"... {more} more", (130, 130, 130), x + 18, y, text_width)

    return buttons


# ---------- Playback ----------

def next_action(event, buttons=None):
    """Decide what an event means for playback: QUIT, NEXT, PREVIOUS, PAUSE, TOGGLE_PANEL, ENDED, or None (keep playing).
    buttons is the {action: rect} map of what's clickable (from control_layout or draw_overlay), for mouse clicks."""
    if event.type == pygame.QUIT:
        return QUIT
    if event.type == SONG_END:
        return ENDED
    if event.type == pygame.KEYDOWN:
        if event.key in (pygame.K_q, pygame.K_ESCAPE):
            return QUIT
        # The buttons say < and >: the arrow keys and the < > keys (comma and period) all work, and N still skips
        if event.key in (pygame.K_n, pygame.K_RIGHT, pygame.K_PERIOD, pygame.K_GREATER) or getattr(event, "unicode", "") == ">":
            return NEXT
        if event.key in (pygame.K_LEFT, pygame.K_COMMA, pygame.K_LESS) or getattr(event, "unicode", "") == "<":
            return PREVIOUS
        if event.key == pygame.K_p:
            return PAUSE
        if event.key == pygame.K_h:
            return TOGGLE_PANEL
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and buttons:
        for action, rect in buttons.items():
            if rect.collidepoint(event.pos):
                return action
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


def get_match_title(songfile):
    """The title that colors and shape are matched against: the title tag if the file has one,
    otherwise the filename title. Just the title, never the artist."""
    _, title = read_tags(songfile)
    return title or get_title_from_path(songfile)


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
    Returns ENDED, NEXT, PREVIOUS, RESTART, QUIT, or UNPLAYABLE."""
    if not os.path.isfile(songfile):
        print(f"Can't find {songfile}. Skipping it.")
        return UNPLAYABLE

    # Show the playlist being played, or just this song if play_song was called on its own
    state = now_playing if now_playing is not None and now_playing.current_song == songfile else PlaybackState([songfile])

    # Each song gets its own title-based colorway and shape (random shape if no keyword matches),
    # matched against the title tag if the file has one, else the filename title
    match_title = get_match_title(songfile)
    colorway = get_colorway(match_title, colormap)
    shape = get_shape(match_title)
    # The loading screen still shows the filename title
    title = get_title_from_path(songfile)
    # What's shown in the corner and the caption (artist/title tags if the file has them)
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

    fonts = load_fonts()
    buttons = control_layout(screen.get_size())
    # Bars are drawn on their own layer, so while paused the last frame can be shown again unchanged
    bar_layer = pygame.Surface(screen.get_size())
    clock = pygame.time.Clock()

    # Run until the song ends, the user skips, or the user quits
    while True:
        for event in pygame.event.get():
            action = next_action(event, buttons)
            if action == PAUSE:
                if state.toggle_pause():
                    pygame.mixer.music.pause()
                else:
                    pygame.mixer.music.unpause()
            elif action == TOGGLE_PANEL:
                state.toggle_panel()
            elif action:
                if action == PREVIOUS:
                    # Read the position before stopping (it holds still while paused)
                    action = previous_or_restart(max(0, pygame.mixer.music.get_pos()) / 1000.0)
                pygame.mixer.music.stop()
                pygame.event.clear(SONG_END)  # stopping can post an end event; don't let it skip the next song
                state.paused = False
                return action

        # While paused, the music position stops too, so the bars hold still and pick up in sync on resume
        if not state.paused:
            bar_layer.fill((0, 0, 0))
            for b in bars:
                b.update(get_decibel(pygame.mixer.music.get_pos() / 1000.0, b.freq))
                b.render(bar_layer)

        screen.blit(bar_layer, (0, 0))
        # What's clickable depends on whether the panel is showing, so take it from what was just drawn
        buttons = draw_overlay(screen, state, fonts, pygame.mouse.get_pos())
        # The corner text goes on the screen (not the bar layer), on top of the bars and panel.
        # Its timer is the song's play position, so it starts over for each song and holds while paused.
        draw_title(screen, title_image, title_alpha(max(0, pygame.mixer.music.get_pos()) / 1000.0))

        pygame.display.flip()
        clock.tick(60)


def previous_or_restart(seconds_in):
    """What Previous means this far into a song: RESTART after the first few seconds, otherwise PREVIOUS."""
    return RESTART if seconds_in > PREVIOUS_RESTART_SECONDS else PREVIOUS


def previous_index(index, unplayable):
    """Where Previous goes from song index: the nearest earlier song that can play,
    or index itself (restart the current song) if there isn't one."""
    for earlier in range(index - 1, -1, -1):
        if earlier not in unplayable:
            return earlier
    return index


def run_playlist(screen, playlist):
    """Play the songs in order, going back a song on Previous. Returns how many times a song actually played
    (0 means none of them could play)."""
    global now_playing
    now_playing = PlaybackState(playlist)
    played = 0
    index = 0
    try:
        while index < len(playlist):
            # Coming forward again after going back: don't retry a song that already couldn't play
            if index in now_playing.unplayable:
                index += 1
                continue
            now_playing.start(index)
            result = play_song(screen, playlist[index])
            if result == UNPLAYABLE:
                now_playing.mark_unplayable(index)
                index += 1
                continue
            played += 1
            if result == QUIT:
                break
            if result == RESTART:
                pass  # same index: the song starts over
            elif result == PREVIOUS:
                index = previous_index(index, now_playing.unplayable)
            else:  # ENDED or NEXT
                index += 1
    finally:
        now_playing = None
    return played


def main(argv=None):
    # Songs from the command line, or from the song chooser if none were given
    args = sys.argv[1:] if argv is None else argv
    if args:
        playlist = playlist_from_paths(args)
        if not playlist:
            print("No songs to play. Give an audio file, several files, or a folder.")
            return
    else:
        playlist = playlist_from_paths(ask_for_songs())
        if not playlist:
            print("No songs chosen, so there's nothing to play.")
            return

    # Report missing files up front, and don't open a window if nothing is left
    found = existing_songs(playlist)
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

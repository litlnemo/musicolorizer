# MUSICOLORIZER

#### Description:
A music visualizer that chooses colors based on words in each song's title, so that the visualization will match the music's mood, or at least its name. For example, the song "Almost Blue" by Elvis Costello would be visualized in shades of blue, as in this picture:

![Mac window, labeled "Musicolorizer," filled with vertical bars in shades of blue.](https://github.com/user-attachments/assets/1f7eafd6-71cc-4c67-8fc4-ea6441d0c44d)

This is based on my final project for CS50Python through HarvardX in 2024. That was a rudimentary version of the Musicolorizer, but this repo contains the ongoing project I am working on improving.

## Setting it up
Install the libraries listed in `requirements.txt`:

```
pip install -r requirements.txt
```

(I use a conda environment named `musicolorizer` for this.)

The song chooser uses tkinter, which comes with most Python installs. On a Homebrew Python on macOS you may need `brew install python-tk`. Without it, the app falls back to typing a path at a prompt.

## Running it
Run `python musicolorizer.py` and a small window asks what you'd like to play:

- **Pick songs…** opens a file dialog where you can choose one song or several.
- **Pick a folder…** opens a folder dialog. Every .mp3, .wav and .flac file in that folder plays, in alphabetical order.
- **Cancel** quits. Cancelling inside either dialog quits too.

The dialogs open in the folder you last picked songs from, or your Music folder the first time. That folder is remembered in a small file, `~/.musicolorizer_last_folder`.

You can also skip the chooser by listing songs or a folder on the command line:

```
python musicolorizer.py "Almost Blue.mp3"
python musicolorizer.py song1.mp3 song2.wav
python musicolorizer.py ~/Music/Playlist
```

Songs that can't be found are listed before the window opens, and songs that can't be read are skipped (and marked "can't play" in the playlist).

### Controls
While music plays, a panel in the top-left corner shows the playlist with the current song highlighted, plus buttons for the controls. Its top line says which song is playing, as "Playlist: 3 of 12", or just "Now playing" when you picked a single song, and adds "PAUSED" while the music is paused. Use the buttons or the keyboard:

| Action | Button | Keys |
| --- | --- | --- |
| Previous song (or start this song over) | Prev (<) | Left Arrow or < |
| Pause / resume | Pause / Resume | P |
| Skip to the next song | Skip (>) | Right Arrow, > or N |
| Hide / show the playlist panel | Show playlist (H), while hidden | H |
| Change how the song name in the corner shows | Title: … (T), at the bottom of the panel | T |
| Scroll the playlist | Mouse wheel over the panel | Up / Down Arrow |
| Quit | Quit (Q) | Q, Esc, or close the window |

**Previous** works like most music players: in the first 3 seconds of a song it goes back to the song before (skipping any that couldn't play), and after that it starts the current song over. On the first song it always starts over. The 3 seconds is set by `PREVIOUS_RESTART_SECONDS` in `musicolorizer.py`.

Pressing **Previous** or **Skip** while paused starts that song playing.

**Clicking a song** in the playlist jumps to it, and the playlist carries on from there. Clicking the song that's playing starts it over, and clicking one marked "can't play" does nothing.

**Scrolling** shows songs further down a long playlist (the panel shows 8 at a time) without changing what's playing, so you can click any song. If the playing song moves out of view, the panel follows it again.

**Hiding the panel** gives the visualizer the whole window. While it's hidden, a small "Show playlist (H)" button sits in the top-left corner; click it or press H to bring the panel back. All the keys keep working while the panel is hidden, and a hidden panel stays hidden from song to song. Each new playlist starts with the panel showing.

### Song name in the corner
While a song plays, its name shows in the bottom-left corner, along with the artist when the file has an artist tag. Songs without tags show the title from the filename. The window title shows the same text.

How long the name stays on screen depends on the title mode. Press **T**, or click the **Title** button at the bottom of the playlist panel, to switch modes while a song plays: always, then fade, then cycle, then back to always. The button shows the current mode, and the new mode takes effect right away on the song that's playing and carries on to the next songs. T works while the panel is hidden, too.

The app starts in the mode set by `TITLE_MODE` near the top of `musicolorizer.py`:

| Mode | What happens |
| --- | --- |
| `'cycle'` (default) | Shows for 5 seconds, fades out, then comes back for 5 seconds every 27 seconds or so |
| `'fade'` | Shows for 5 seconds at the start of the song, then fades out for good |
| `'always'` | Stays on screen for the whole song |

The timings are set by `TITLE_SHOW_SECONDS`, `TITLE_FADE_SECONDS` and `TITLE_HIDDEN_SECONDS`, right below `TITLE_MODE`. The timer pauses when the music is paused and starts over with each song.

## Running the tests
```
pytest
```

The tests never open a real window or dialog: the song chooser is replaced with a fake, and pygame runs with SDL's "dummy" video and audio drivers. Audio for the playback tests comes from tiny WAV files the tests generate in a temporary folder, so you don't need any songs to run them.

## Project overview
This project is the beginning of (I hope!) a larger project for a context-aware music visualizer. Over the years, I've enjoyed using music visualizers built into software such as iTunes, but they've always been lacking something. A sad, mournful song might be visualized with happy, upbeat colors. A song with "blue" in the title might be visualized in red. It kind of drives me crazy. If a human was actively controlling the animation, they'd probably choose colors and shapes that work well with the music, but none of the visualizers I've used have had that capability.

Thus, the Musicolorizer. It is a simple visualizer that compares song titles to words in a predefined dictionary, and if it finds a match, it uses the colors defined for that dictionary match to visualize the music when it plays. If there are no matches, it generates random colors.

## How it works
### Libraries
The libraries used in this project include:
- librosa (music analysis)
- pygame (playing the music and drawing everything in the window: the bars, the playlist panel and controls, and the song name)
- numpy (mathy array stuff used to work with the spectrogram, short-time Fourier analysis, etc.)
- mutagen (reading artist and title tags from the audio files)
- tkinter (the song chooser window and file dialogs; it comes with most Python installs)
- random (generating random colorways, and random shapes for titles with no shape keyword)
- os and sys (file paths, folders, and songs given on the command line)

### Files
- `musicolorizer.py`: the program
- `colormap.py`: the keyword-to-color and keyword-to-shape maps
- `test_*.py`: the tests

## musicolorizer.py
### `n_fft` and `hop_length`
The program begins with two settings that define the slices of time that make up the song's spectrogram. `n_fft` is the *frame length*, the "number of samples in an analysis window (or frame)."[^1] `hop_length` is "The number of samples between successive frames, e.g., the columns of a spectrogram."[^1]

### Which title is matched
Colors and shapes are matched against the song's **title tag** if the file has one, otherwise against the title from the filename (`get_match_title`). Only the title is matched, never the artist.

### Colormap
The colormap (in `colormap.py`) is a dictionary listing keywords that may be found in song titles, and the colors that go along with them. Each colorway runs from a dark color for quiet sounds to a bright one for loud sounds. This is the current colormap:

| Keyword | Colors (quiet → loud) |
| --- | --- |
| blue | deep navy → bright blue |
| sad, winter | black → bright blue |
| happy | near black → bright yellow |
| love | near black → hot pink |
| red | black → bright red |
| green | near black → lime green |
| spring | near black → yellow-green |
| daydreams | black → purple-magenta |
| gold | dark gold → bright yellow-gold |
| silver | dark grey → silver |
| purple | deep blue-black → blue-purple |
| violet | deep red-purple → soft violet-pink |
| orange | dark orange → vivid orange |
| pink | deep rose → light pink |
| black | black → dark grey |
| white | dark grey → pure white |
| gray, grey | near black → medium grey |
| money | dark green → muted dollar-bill green |
| storm | dark blue-grey → electric blue-white |
| snow | dark grey-blue → icy white |
| ocean, sea | deep navy → teal-cyan |
| forest | near black → muted pine/evergreen green |
| smoke | dark grey → pale blue-grey |
| anger, angry | near black → intense red-orange |
| lonely | dark blue-grey → muted slate |
| joy | deep orange → bright warm yellow |
| magic | purple-black → bright magenta |
| cold | dark navy → icy pale blue |
| blood | very dark red → bright red |
| rose | dark red → soft pink |
| shadow | black → dark cool grey with purple tint |
| electric | dark blue → bright cyan |
| hope | dark amber → warm gold |
| dark, darkness | near black → very dark purple-grey |
| fire, flame | dark red → bright orange |
| dream | deep purple → soft lavender |
| ghost, haunted | dark grey-green → pale cool white |
| rain | dark grey-blue → muted steel blue |
| sun, sunshine | dark orange → bright warm yellow |
| night | near black → deep indigo |
| shine | dark amber → brilliant gold |
| bright | dark grey → dazzling white |
| glow | dark ember → warm orange-gold |
| wine | near-black burgundy → deep wine red |
| earth | dark soil brown → warm clay |
| wedding | dark mauve-grey → ivory white |
| marry | dark rose → soft blush pink |
| twilight | deep indigo → soft violet-pink |
| light | dark slate → bright white |
| sunset | dark plum-brown → fiery orange-pink |
| sunrise | dark indigo-brown → warm gold-pink |
| dusk | dark blue-grey → muted mauve |
| retro | dark plum-black → vivid magenta |
| moon | dark navy → pale silver-blue |
| desert | dark sand-brown → sun-bleached gold |
| summer | deep amber → sunny gold-orange |
| autumn | dark brown → burnt orange |
| star | near-black → warm white-gold |
| neon | black → hot pink |
| crimson | dark maroon → true crimson |
| lavender | dark grey-purple → soft lavender |
| dance | dark plum → bright fuchsia |
| ember | near-black red → glowing orange |
| coral | dark coral-red → bright coral pink-orange |
| mint | dark green-grey → fresh mint green |
| peach | dark warm brown → soft peach |
| velvet | near-black plum → rich purple-red |
| cherry | dark red → bright cherry red |
| disco | dark purple-black → sparkling magenta |
| aurora | dark teal-black → shimmering green-violet |

### `get_colorway`, `pick_color_for_bar`, `random_color`
These functions search the song's title (case-insensitively) for every colormap keyword that appears in it. If a title matches more than one keyword, each bar picks one of the matching colorways at random (`pick_color_for_bar`), so "Blue Love Song" mixes blue and pink bars. If nothing matches, the song gets a random colorway.

Keywords currently match anywhere inside the title, even inside other words (so "red" also matches "tired", and "Sunset" gets both the sun and sunset colorways). Matching whole words only is [issue #13](https://github.com/litlnemo/musicolorizer/issues/13).

### Shapes and `get_shape`
Song titles also choose the shape of the bars. The shape map (also in `colormap.py`) lists keywords for each shape:

| Shape | Keywords |
| --- | --- |
| triangle | sharp, knife, edge, blade, cut, pointed, spike, thorn, razor, jagged, arrow, fang, claw, diamond |
| wavy | wave, ocean, sea, river, rain, water, flow, stream, tide, surf, ripple, current, drift, float, sway, cascade, brook |
| rounded | soft, gentle, cloud, pillow, dream, round, smooth, mellow, tender, bubble, balloon, circle, orb, velvet, silk, lullaby |
| tapered | tall, rise, climb, mountain, tower, reach, soar, summit, peak, sky, spire, rocket, flight, wing |
| rectangle | block, square, city, straight, steady, brick, wall, solid, grid, house, street, stable |

`get_shape` uses the same case-insensitive matching as `get_colorway`. If a title matches keywords for more than one shape, the first shape in the table wins. If nothing matches, the song gets a random shape. Every bar in a song has the same shape.

### `ColorBar`
`ColorBar` is a class that defines the vertical colored bars in the visualizer, including their height, color (from the song's colorway) and shape. Each bar's color shifts along its colorway's gradient as its frequency gets louder or quieter. Rounded and triangle bars also grow and shrink with the volume; the other shapes stay the full height of the window. There are five shapes:

- **rectangle**: plain bars, drawn with `pygame.draw.rect()`[^5]
- **rounded**: bars with fully rounded ends, also drawn with `pygame.draw.rect()`
- **triangle**: a point at the top, drawn with `pygame.draw.polygon()`[^11]
- **tapered**: wide at the top and narrow at the bottom, also a polygon
- **wavy**: a polygon with wobbly edges that change every frame

### `limitation`
`limitation` is a function forcing the values of decibel to stay in a certain range, to be used when defining the gradient effect in the colorbars.

### `get_decibel`
This function gets the spectrogram information for a specific location in the track, to be used to generate a colorbar.

### `main`
The `main` function controls the overall operation of the program. It gets the songs from the command line, or from the song chooser if none were given (`ask_for_songs`). Then it turns them into a playlist (`playlist_from_paths`, which reads a folder's songs in alphabetical order) and reports any files it can't find (`existing_songs`). Display settings such as `pygame.display.Info()`[^6] and `pygame.display.set_mode()`[^7] are used to define and initialize the visualizer screen. Then `run_playlist` plays the songs.

### `run_playlist` and `PlaybackState`
`run_playlist` steps through the playlist by index, so it can go back as well as forward. After each song it moves on to the next one, goes back one (Previous), plays the same song again (Previous after the first 3 seconds), or stops (Quit). Songs that couldn't be read are skipped, and aren't tried again.

`PlaybackState` keeps track of what the playlist panel needs: the songs, which one is current, which couldn't play, whether the music is paused, whether the panel is showing, the corner-title mode, and where the playlist is scrolled to.

`run_playlist` also handles a click on a song in the panel: it jumps straight to that song and carries on from there.

### `play_song`
`play_song` handles one song from start to finish:

1. It picks the colorway (`get_colorway`) and shape (`get_shape`) from the song's title (see "Which title is matched" above). It also reads the artist and title tags for the song name shown in the corner (`get_display_info`).
2. While a loading screen shows, `analyze_song` loads the song with librosa. It uses `librosa.amplitude_to_db()` and `librosa.mel_frequencies()` to convert the spectrogram into a dB-scaled spectrogram[^2] and compute acoustic frequencies.[^3] `librosa.frames_to_time()` then converts frame counts into seconds.[^4]
3. Color bars are generated (`build_bars`), then `pygame.mixer.music.load()`[^8] and `pygame.mixer.music.play()`[^9] load and play the music.
4. Each frame, it handles the controls (`next_action` turns key presses and clicks into actions), updates and draws the bars, then draws the playlist panel (`draw_overlay`) and the song name (`draw_title`) on top. `pygame.display.flip()`[^10] is used to update the screen.

While paused, the bars hold still and the music position stops too, so everything picks up in sync on resume.

### The playlist panel
`draw_overlay` draws the panel: the header line (`panel_header`), the four buttons (laid out by `control_layout`), the playlist rows, and the Title button at the bottom (`title_mode_layout`). A long playlist shows 8 rows at a time (`panel_window`): it follows the current song until you scroll, and goes back to following it when the playing song moves out of view. When the panel is hidden it draws only the small "Show playlist (H)" button instead (`draw_chip`). Either way it returns what can be clicked right now: the buttons, and the playlist rows it just drew (none while the panel is hidden).

Drawing and clicking share the same layout functions, so a click always lands on what's drawn: `play_song` gives `next_action` the song rows that `draw_overlay` just drew, to tell which song was clicked, and the panel area from `panel_rect`, to tell whether the mouse wheel is over the panel.

## Examples
**Keyword: "love"**
![Mac window, labeled "Musicolorizer," filled with vertical bars in shades of pink and red.](https://github.com/user-attachments/assets/77680faa-1af0-4c89-ab7f-27b6495137f9)

**Keyword: "spring"**
![Mac window, labeled "Musicolorizer," filled with vertical bars in shades of yellow-green.](https://github.com/user-attachments/assets/a5d46632-e6c3-4595-b0c9-1123e18cb2f9)

**Keyword: none (random colors)**
![Mac window, labeled "Musicolorizer," filled with vertical bars in shades of pink.](https://github.com/user-attachments/assets/c864bf95-725c-4378-87c5-0d10f4e4c0a2)

**Keyword: none (random colors)**
![Mac window, labeled "Musicolorizer," filled with vertical bars in shades of blue.](https://github.com/user-attachments/assets/20585f03-24f3-40d6-8d97-e962be9b73fc)


## Design choices
Some choices were made out of frustration, some because I am still new to this and did not feel comfortable expanding further, and some because they were lower priority. When I finished the CS50P version, these were things I hadn't done yet. Since then, I've added:

- Playlists, not one song at a time
- Selecting songs, not typing them in
- More colorways in the colormap
- Combination colorways if a song has two dictionary words in the title
- A GUI: a song chooser, plus a playlist panel and controls while the music plays
- Pause, previous track, and a way to hide the playlist panel
- Varying the shapes, chosen by keywords in the title
- The artist and song name in the corner
- Matching colors and shapes against the title tag, not just the filename
- Clicking a song in the playlist to jump to it
- Scrolling a long playlist with the mouse wheel or the arrow keys
- Choosing the corner-title display mode from the window (the T key or the Title button)
- Thirty more colorways and more shape keywords

Still to do (see the [open issues](https://github.com/litlnemo/musicolorizer/issues)):

- Overlaying lyrics
- Apple Music integration, and an animated mode for streaming tracks that can't be analyzed
- Supporting .m4a files
- Matching whole words only in titles
- ...and more that I'm probably forgetting now!

Other choices were done because I wanted them!

- The bars being the full height of the window because I like the way it looks
- Songs without dictionary terms being random colors, not a single "undefined" colorway, which was boring


## Sources that helped me
I had extreme trouble figuring out librosa from the docs, which are highly technical and seem to target music engineers, which I am not. The docs were more helpful once I had a hint of where to start. Pygame wasn't quite as difficult but it was hard to know where to start with that, as well, since I wasn't building a game and lots of tutorials are focused on games.
These are used to figure out how to use pygame and librosa, and to explain many terms and how to make the libraries do what I needed to do:
- [How to create a music visualizer (Analytics Vidhya)](https://medium.com/analytics-vidhya/how-to-create-a-music-visualizer-7fad401f5a69)
- [pygame documentation](https://www.pygame.org/docs/)
- [librosa documentation](https://librosa.org/doc/latest/)
- [r/VideoEditing comment](https://www.reddit.com/r/VideoEditing/comments/ssci0l/comment/hwxw2fd/)
- [Audio Visualizer by chaosqueenbee](https://medium.com/@chaosqueenbee/audio-visualizer-6571b9085f0e) -- the most helpful -- clear explanations and her visualizer inspired the look of mine. I did use code snippets from her work.
- [Audio signal processing with spectrograms and librosa](https://khareanu1612.medium.com/audio-signal-processing-with-spectrograms-and-librosa-b66a0a6bc5cc)

## Footnotes
[^1]: <https://librosa.org/doc/main/glossary.html>
[^2]: <https://librosa.org/doc/main/generated/librosa.amplitude_to_db.html>
[^3]: <https://librosa.org/doc/main/generated/librosa.mel_frequencies.html>
[^4]: <https://librosa.org/doc/latest/generated/librosa.frames_to_time.html>
[^5]: <https://www.pygame.org/docs/ref/draw.html#pygame.draw.rect>
[^6]: <https://www.pygame.org/docs/ref/display.html#pygame.display.Info>
[^7]: <https://www.pygame.org/docs/ref/display.html#pygame.display.set_mode>
[^8]: <https://www.pygame.org/docs/ref/music.html#pygame.mixer.music.load>
[^9]: <https://www.pygame.org/docs/ref/music.html#pygame.mixer.music.play>
[^10]: <https://www.pygame.org/docs/ref/display.html#pygame.display.flip>
[^11]: <https://www.pygame.org/docs/ref/draw.html#pygame.draw.polygon>

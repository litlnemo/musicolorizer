# MUSICOLORIZER
## NOTE - This README isn't up to date at the moment. I've been making a lot of changes. Once things settle down I will update it. 

#### Description: 
A music visualizer that chooses colors based on words in each song's title, so that the visualization will match the music's mood, or at least its name. For example, the song "Almost Blue" by Elvis Costello would be visualized in shades of blue, as in this picture:

![Mac window, labeled "Musicolorizer," filled with vertical bars in shapes of blue.](https://github.com/user-attachments/assets/1f7eafd6-71cc-4c67-8fc4-ea6441d0c44d)

This is based on my final project for CS50Python through HarvardX in 2024. That was a rudimentary version of the Musicolorizer, but this repo contains the ongoing project I am working on improving.

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

While music plays, the window shows the playlist with the current song highlighted. Use the buttons or the keyboard:

| Action | Button | Keys |
| --- | --- | --- |
| Pause / resume | Pause / Resume | P |
| Skip to the next song | Skip | N or Right Arrow |
| Quit | Quit | Q, Esc, or close the window |

### Song name in the corner
While a song plays, its name shows in the bottom-left corner, along with the artist when the file has an artist tag. Songs without tags show the title from the filename. The window title shows the same text.

How long the name stays on screen is set by `TITLE_MODE` near the top of `musicolorizer.py`:

| `TITLE_MODE` | What happens |
| --- | --- |
| `'cycle'` (default) | Shows for 5 seconds, fades out, then comes back for 5 seconds every 27 seconds or so |
| `'fade'` | Shows for 5 seconds at the start of the song, then fades out for good |
| `'always'` | Stays on screen for the whole song |

The timings are set by `TITLE_SHOW_SECONDS`, `TITLE_FADE_SECONDS` and `TITLE_HIDDEN_SECONDS`, right below `TITLE_MODE`. The timer pauses when the music is paused and starts over with each song.

The chooser uses tkinter, which comes with most Python installs. On a Homebrew Python on macOS you may need `brew install python-tk`. Without it, the app falls back to typing a path at a prompt.

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

## musicolorizer.py
### `n_fft` and `hop_length`
The program begins with two settings that define the slices of time that make up the song's spectrogram. `n_fft` is the *frame length*, the "number of samples in an analysis window (or frame)."[^1] `hop_length` is "The number of samples between successive frames, e.g., the columns of a spectrogram."[^1]

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

### `get_colorway`, `pick_color_for_bar`, `random_color`
These functions process the song's title (case-insensitively) and search the colormap for every keyword that appears in it. If a title matches more than one keyword, each bar picks one of the matching colorways at random (`pick_color_for_bar`), so "Blue Love Song" mixes blue and pink bars. If nothing matches, the song gets a random colorway.

### Shapes and `get_shape`
Song titles also choose the shape of the bars. The shape map (also in `colormap.py`) lists keywords for each shape:

| Shape | Keywords |
| --- | --- |
| triangle | sharp, knife, edge, blade, cut, pointed |
| wavy | wave, ocean, sea, river, rain, water, flow |
| rounded | soft, gentle, cloud, pillow, dream, round |
| tapered | tall, rise, climb, mountain, tower, reach |
| rectangle | block, square, city, straight, steady |

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
The `main` function controls the overall operation of the program. It gets the songs from the command line, or from the song chooser if none were given (`ask_for_songs`). Then it turns them into a playlist (`playlist_from_paths`, which reads a folder's songs in alphabetical order) and reports any files it can't find. Display settings such as `pygame.display.Info()`[^6] and `pygame.display.set_mode()`[^7] are used to define and initialize the visualizer screen. Then `run_playlist` plays the songs in order.

### `play_song`
`play_song` handles one song from start to finish:

1. It takes the title from the filename and uses it to pick the colorway (`get_colorway`) and shape (`get_shape`). It also reads the artist and title tags for the song name shown in the corner (`get_display_info`).
2. While a loading screen shows, `analyze_song` loads the song with librosa. It uses `librosa.amplitude_to_db()` and `librosa.mel_frequencies()` to convert the spectrogram into a dB-scaled spectrogram[^2] and compute acoustic frequencies.[^3] `librosa.frames_to_time()` then converts frame counts into seconds.[^4]
3. Color bars are generated (`build_bars`), then `pygame.mixer.music.load()`[^8] and `pygame.mixer.music.play()`[^9] load and play the music.
4. Each frame, it handles the controls (pause, skip, quit), updates and draws the bars, then draws the playlist panel and the song name on top. `pygame.display.flip()`[^10] is used to update the screen.

When a song finishes or is skipped, the next song in the playlist starts; quitting stops the playlist. Files that can't be read are skipped with a message.

## Examples
**Keyword: "love"**
![Mac window, labeled "Musicolorizer," filled with vertical bars in shades of pink and red.](https://github.com/user-attachments/assets/77680faa-1af0-4c89-ab7f-27b6495137f9) 

**Keyword: "spring"**
![Mac window, labeled "Musicolorizer," filled with vertical bars in shades of yellow-green.](https://github.com/user-attachments/assets/a5d46632-e6c3-4595-b0c9-1123e18cb2f9)

**Keyword: none (random colors)**
![Mac window, labeled "Musicolorizer," filled with vertical bars in shades of pink.](https://github.com/user-attachments/assets/c864bf95-725c-4378-87c5-0d10f4e4c0a2)

**Keyword: none (random colors)**
![Mac window, labeled "Musicolorizer," filled with vertical bars in shapes of blue.](https://github.com/user-attachments/assets/20585f03-24f3-40d6-8d97-e962be9b73fc)


## Design choices
Some choices were made out of frustration, some because I am still new to this and did not feel comfortable expanding further, and some because they were lower priority. When I finished the CS50P version, these were things I hadn't done yet. Since then, I've added:

- Playlists, not one song at a time
- Selecting songs, not typing them in
- More colorways in the colormap
- Combination colorways if a song has two dictionary words in the title
- A GUI: a song chooser, plus a playlist panel and controls while the music plays
- Varying the shapes, chosen by keywords in the title
- The artist and song name in the corner

Still to do:

- Overlaying lyrics
- Turning it into some kind of plug-in that could be used with a music player?
- ...and more that I'm probably forgetting now!

Other choices were done because I wanted them!

- The bars being the full height of the window because I like the way it looks
- Songs without dictionary terms being random colors, not a single "undefined" colorway, which was boring


## Sources that helped me
I had extreme trouble figuring out librosa from the docs, which are highly technical and seem to target music engineers, which I am not. The docs were more helpful once I had a hint of where to start. Pygame wasn't quite as difficult but it was hard to know where to start with that, as well, since I wasn't building a game and lots of tutorials are focused on games.
These are used to figure out how to use pygame and librosa, and to explain many terms and how to make the libraries do what I needed to do:
- [https://medium.com/analytics-vidhya/how-to-create-a-music-visualizer-7fad401f5a69](url)
- [https://www.pygame.org/docs/](url)
- [https://librosa.org/doc/latest/](url)
- [https://www.reddit.com/r/VideoEditing/comments/ssci0l/comment/hwxw2fd/](url)
- [https://medium.com/@chaosqueenbee/audio-visualizer-6571b9085f0e](url) -- the most helpful -- clear explanations and her visualizer inspired the look of mine. I did use code snippets from her work.
- [https://khareanu1612.medium.com/audio-signal-processing-with-spectrograms-and-librosa-b66a0a6bc5cc](url)

## Footnotes
[^1]: [https://librosa.org/doc/main/glossary.html]
[^2]: [https://librosa.org/doc/main/generated/librosa.amplitude_to_db.html]
[^3]: [https://librosa.org/doc/main/generated/librosa.mel_frequencies.html]
[^4]: [https://librosa.org/doc/latest/generated/librosa.frames_to_time.html]
[^5]: [https://www.pygame.org/docs/ref/draw.html#pygame.draw.rect]
[^6]: [https://www.pygame.org/docs/ref/display.html#pygame.display.Info]
[^7]: [https://www.pygame.org/docs/ref/display.html#pygame.display.set_mode]
[^8]: [https://www.pygame.org/docs/ref/music.html#pygame.mixer.music.load]
[^9]: [https://www.pygame.org/docs/ref/music.html#pygame.mixer.music.play]
[^10]: [https://www.pygame.org/docs/ref/display.html#pygame.display.flip]
[^11]: [https://www.pygame.org/docs/ref/draw.html#pygame.draw.polygon]


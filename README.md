# MUSICOLORIZER
#### Video Demo:  <https://youtu.be/puraf7z56Hc>
#### Description: 
Final project for CS50Python through HarvardX. A music visualizer that chooses colors based on words in each song's title, so that the visualization will match the music's mood, or at least its name. For example, the song "Almost Blue" by Elvis Costello would be visualized in shades of blue, as in this picture:

![Mac window, labeled "Musicolorizer," filled with vertical bars in shapes of blue.](https://github.com/user-attachments/assets/1f7eafd6-71cc-4c67-8fc4-ea6441d0c44d)

## Project overview
This project is the beginning of (I hope!) a larger project for a context-aware music visualizer. Over the years, I've enjoyed using music visualizers built into software such as iTunes, but they've always been lacking something. A sad, mournful song might be visualized with happy, upbeat colors. A song with "blue" in the title might be visualized in red. It kind of drives me crazy. If a human was actively controlling the animation, they'd probably choose colors and shapes that work well with the music, but none of the visualizers I've used have had that capability.

Thus, the Musicolorizer. It is a simple visualizer that compares song titles to words in a predefined dictionary, and if it finds a match, it uses the colors defined for that dictionary match to visualize the music when it plays. If there are no matches, it generates random colors.

## How it works
### Libraries
The libraries used in this project include:
- librosa (music analysis)
- pygame (visual display)
- numpy (mathy array stuff used to work with the spectrogram, short-time Fourier analysis, etc.)
- random (generating random colorways)
- os environ (setting up the use of ffmpeg to work with sound files)

## project.py
### `n_fft` and `hop_length`
The program begins with two settings that define the slices of time that make up the song's spectrogram. `n_fft` is the *frame length*, the "number of samples in an analysis window (or frame)."[^1] `hop_length` is "The number of samples between successive frames, e.g., the columns of a spectrogram."[^1]

### Colormap
The colormap is a small dictionary listing certain keywords that may be found in song titles, and the colors that go along with them. In a fully-fledged visualizer, there would be many more of these, but for the purposes of this project, I just used a few that were in songs I had on hand. This is the current colormap:

| Keyword | Color |
| --- | --- |
| blue | blue |
| sad | blue |
| winter | blue |
| happy | yellow |
| love | pink, red |
| red | red |
| green | true green |
| spring | yellow-green |
| daydreams | purple/magenta |
    
### `get_colorway`, `random_color`
These functions are used to process the song's title (case-insensitively), search the colormap for matching colorways, and generate random colors if there is no match to the colormap dictionary.

### `ColorBar`
`ColorBar` is a class that defines the vertical colored bars in the visualizer including height and color (inherited from the colorway definition mentioned earlier), and renders the bars using `pygame.draw.rect()`.[^5]

### `limitation` 
`limitation` is a function forcing the values of decibel to stay in a certain range, to be used when defining the gradient effect in the colorbars.

### `get_decibel`
This function gets the spectrogram information for a specific location in the track, to be used to generate a colorbar.

### `main`
The `main` function controls the overall operation of the program. It begins by getting the song title from user input, setting the colorway using `get_colorway`, then loading the song to analyze with librosa. It uses `librosa.amplitude_to_db()` and `librosa.mel_frequencies()` to convert the spectrogram into a dB-scaled spectrogram[^2] and compute acoustic frequencies.[^3] `librosa.frames_to_time()` then converts frame counts into seconds.[^4] At this point, pygame comes into the picture! Display settings such as `pygame.display.info()`[^6] and `pygame.display.set_mode()`[^7] are used to define and initialize the visualizer screen. Colorbars are generated, then `pygame.mixer.music.load()`[^8] and `pygame.mixer.music.play()`[^9] load and play the music. `pygame.display.flip()`[^10] is used to update the screen. The program runs until the user closes the visualizer.

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
Some choices were made out of frustration, some because I am still new to this and did not feel comfortable expanding further, and some because they were lower priority. These are things I didn't do, that I would change if I continue with this:

- Playlists, not one song at a time
- Selecting songs, not typing them in
- More colorways in the colormap
- Combination colorways if a song has two dictionary words in the title
- Overlaying lyrics
- GUI
- Perhaps varying the shapes; not always vertical rectangles
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
- [https://khareanu1612.medium.com/audio-signal-processing-with-spectrograms-and-librosa-b66a0a6bc5cc]

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


# MUSICOLORIZER
#### Video Demo:  <https://youtu.be/puraf7z56Hc>
#### Description: 
A music visualizer that chooses colors based on words in each song's title, so that the visualization will match the music's mood, or at least its name. For example, the song "Almost Blue" by Elvis Costello would be visualized in shades of blue, as in this picture:

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
`ColorBar` is a class that defines the vertical colored bars in the visualizer including height and color (inherited from the colorway definition mentioned earlier), and renders the bars using `pygame.draw.rect()`.

### `limitation` 
`limitation` is a function forcing the values of decibel to stay in a certain range, to be used when defining the gradient effect in the colorbars.

### get_decibel
This function gets the spectrogram information 


## Sources that helped me
Sources used to figure out how to use pygame, librosa,  etc. to make a visualizer:
- [https://medium.com/analytics-vidhya/how-to-create-a-music-visualizer-7fad401f5a69](url)
- [https://www.pygame.org/docs/](url)
- [https://librosa.org/doc/latest/](url)
- [https://www.reddit.com/r/VideoEditing/comments/ssci0l/comment/hwxw2fd/](url)
- [https://medium.com/@chaosqueenbee/audio-visualizer-6571b9085f0e](url) -- most helpful, her visualizer inspired the look of mine
- [https://khareanu1612.medium.com/audio-signal-processing-with-spectrograms-and-librosa-b66a0a6bc5cc]

## Footnotes
[^1]: [https://librosa.org/doc/main/glossary.html]

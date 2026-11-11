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
    # More colorways (issue #4): Wendi's picks
    'shine':     [(50, 30, 0),  (255, 215, 60)], # dark amber → brilliant gold
    'bright':    [(25, 25, 30), (255, 255, 245)],# dark grey → dazzling white
    'glow':      [(50, 10, 0),  (255, 170, 60)], # dark ember → warm orange-gold
    'wine':      [(25, 0, 10),  (160, 20, 50)],  # near-black burgundy → deep wine red
    'earth':     [(30, 18, 8),  (190, 130, 80)], # dark soil brown → warm clay
    'wedding':   [(45, 40, 50), (250, 245, 235)],# dark mauve-grey → ivory white
    'marry':     [(50, 10, 25), (255, 180, 200)],# dark rose → soft blush pink
    'twilight':  [(10, 5, 35),  (190, 130, 220)],# deep indigo → soft violet-pink
    'light':     [(20, 25, 35), (245, 245, 255)],# dark slate → bright white
    'sunset':    [(45, 10, 20), (255, 110, 80)], # dark plum-brown → fiery orange-pink
    'sunrise':   [(25, 10, 30), (255, 190, 130)],# dark indigo-brown → warm gold-pink
    'dusk':      [(15, 15, 30), (150, 130, 160)],# dark blue-grey → muted mauve
    'retro':     [(15, 0, 25),  (255, 0, 160)],  # dark plum-black → vivid magenta
    'moon':      [(5, 5, 25),   (220, 225, 255)],# dark navy → pale silver-blue
    'desert':    [(55, 35, 10), (240, 200, 120)],# dark sand-brown → sun-bleached gold
    # More colorways (issue #4): Mews's picks
    'summer':    [(60, 25, 0),  (255, 180, 40)], # deep amber → sunny gold-orange
    'autumn':    [(45, 15, 0),  (220, 100, 20)], # dark brown → burnt orange
    'star':      [(10, 10, 20), (255, 245, 180)],# near-black → warm white-gold
    'neon':      [(5, 0, 10),   (255, 0, 180)],  # black → hot pink
    'crimson':   [(40, 0, 5),   (220, 20, 60)],  # dark maroon → true crimson
    'lavender':  [(35, 25, 55), (210, 180, 250)],# dark grey-purple → soft lavender
    'dance':     [(20, 0, 30),  (255, 80, 200)], # dark plum → bright fuchsia
    'ember':     [(25, 5, 0),   (255, 120, 20)], # near-black red → glowing orange
    'coral':     [(60, 15, 10), (255, 130, 110)],# dark coral-red → bright coral pink-orange
    'mint':      [(10, 30, 25), (170, 255, 210)],# dark green-grey → fresh mint green
    'peach':     [(60, 25, 10), (255, 200, 160)],# dark warm brown → soft peach
    'velvet':    [(15, 0, 20),  (180, 30, 90)],  # near-black plum → rich purple-red
    'cherry':    [(40, 0, 10),  (230, 30, 70)],  # dark red → bright cherry red
    'disco':     [(10, 0, 25),  (255, 60, 220)], # dark purple-black → sparkling magenta
    'aurora':    [(0, 20, 25),  (120, 255, 190)],# dark teal-black → shimmering green-violet
}

# Keyword-to-shape (order matters: if a title matches more than one shape,
# the first shape listed here wins)
shapemap = {
    'triangle':  ['sharp', 'knife', 'edge', 'blade', 'cut', 'pointed'],
    'wavy':      ['wave', 'ocean', 'sea', 'river', 'rain', 'water', 'flow'],
    'rounded':   ['soft', 'gentle', 'cloud', 'pillow', 'dream', 'round'],
    'tapered':   ['tall', 'rise', 'climb', 'mountain', 'tower', 'reach'],
    'rectangle': ['block', 'square', 'city', 'straight', 'steady'],
}

"""Tests for choosing a bar shape from keywords in the song title."""
import pygame

import musicolorizer
from musicolorizer import SHAPES, get_shape, play_song
from colormap import shapemap


# ---------- one test per shape group ----------

def test_triangle_keywords():
    assert get_shape("Sharp Edges") == "triangle"
    for title in ["Knife Fight", "Edge of Seventeen", "Blade", "Cut Here", "Pointed Remarks"]:
        assert get_shape(title) == "triangle", title


def test_wavy_keywords():
    assert get_shape("Ocean Waves") == "wavy"
    for title in ["Beyond the Sea", "Moon River", "Purple Rain", "Water Music", "Go With the Flow"]:
        assert get_shape(title) == "wavy", title


def test_rounded_keywords():
    for title in ["Soft Cell", "Gentle On My Mind", "Cloud Nine", "Pillow Talk", "Dream On", "Round Midnight"]:
        assert get_shape(title) == "rounded", title


def test_tapered_keywords():
    for title in ["Tall Trees", "Rise Up", "Climb Every Hill", "Mountain Song", "Tower of Song", "Reach Out"]:
        assert get_shape(title) == "tapered", title


def test_rectangle_keywords():
    for title in ["Block Party", "Square Dance", "City Lights", "Straight Ahead", "Steady As She Goes"]:
        assert get_shape(title) == "rectangle", title


# ---------- matching rules ----------

def test_case_insensitive():
    assert get_shape("SHARP EDGES") == "triangle"
    assert get_shape("ocean waves") == "wavy"
    assert get_shape("cLoUd NiNe") == "rounded"


def test_substring_match():
    # Same rule as get_colorway: the keyword can appear anywhere in the title
    assert get_shape("daydreams") == "rounded"
    assert get_shape("Sunrise") == "tapered"


def test_first_match_wins():
    # triangle comes before wavy in the mapping, whichever word comes first in the title
    assert get_shape("Sharp Rain") == "triangle"
    assert get_shape("Rain Sharp") == "triangle"
    # wavy before rounded, rounded before tapered, tapered before rectangle
    assert get_shape("Soft Ocean") == "wavy"
    assert get_shape("Tall Cloud") == "rounded"
    assert get_shape("City Tower") == "tapered"


def test_no_match_returns_valid_shape():
    for _ in range(50):
        assert get_shape("Something Else") in SHAPES


def test_no_match_is_random():
    # With no keyword, the shape still varies (50 picks from 5 shapes all equal is ~1 in 10^34)
    assert len({get_shape("Something Else") for _ in range(50)}) > 1


def test_mapping_order_and_shapes():
    assert list(shapemap) == ["triangle", "wavy", "rounded", "tapered", "rectangle"]
    assert set(shapemap) == set(SHAPES)


# ---------- play_song uses get_shape ----------

def test_play_song_uses_title_shape(tmp_path, monkeypatch):
    from test_playlist import make_tiny_wav
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    try:
        screen = pygame.display.set_mode([200, 150])
        shapes_used = []
        real_build_bars = musicolorizer.build_bars

        def spy(colorway, shape, width, height):
            shapes_used.append(shape)
            return real_build_bars(colorway, shape, width, height)
        monkeypatch.setattr(musicolorizer, "build_bars", spy)

        song = make_tiny_wav(tmp_path / "Sharp Edges.wav", seconds=2)
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q))
        play_song(screen, song)
        assert shapes_used == ["triangle"]
    finally:
        pygame.quit()


# ---------- more shape keywords (brief 19) ----------

NEW_SHAPE_KEYWORDS = {
    'triangle':  ['spike', 'thorn', 'razor', 'jagged', 'arrow', 'fang',
                  'claw', 'diamond'],
    'wavy':      ['stream', 'tide', 'surf', 'ripple', 'current', 'drift',
                  'float', 'sway', 'cascade', 'brook'],
    'rounded':   ['smooth', 'mellow', 'tender', 'bubble', 'balloon',
                  'circle', 'orb', 'velvet', 'silk', 'lullaby'],
    'tapered':   ['soar', 'summit', 'peak', 'sky', 'spire', 'rocket',
                  'flight', 'wing'],
    'rectangle': ['brick', 'wall', 'solid', 'grid', 'house', 'street',
                  'stable'],
}

OLD_SHAPE_KEYWORDS = {
    'triangle':  ['sharp', 'knife', 'edge', 'blade', 'cut', 'pointed'],
    'wavy':      ['wave', 'ocean', 'sea', 'river', 'rain', 'water', 'flow'],
    'rounded':   ['soft', 'gentle', 'cloud', 'pillow', 'dream', 'round'],
    'tapered':   ['tall', 'rise', 'climb', 'mountain', 'tower', 'reach'],
    'rectangle': ['block', 'square', 'city', 'straight', 'steady'],
}


def test_new_keywords_appended_after_existing_ones():
    for shape, old in OLD_SHAPE_KEYWORDS.items():
        assert shapemap[shape] == old + NEW_SHAPE_KEYWORDS[shape], shape
    assert sum(len(new) for new in NEW_SHAPE_KEYWORDS.values()) == 43


def test_each_new_keyword_returns_its_shape():
    for shape, keywords in NEW_SHAPE_KEYWORDS.items():
        for keyword in keywords:
            for title in [keyword, keyword.title(), f"The {keyword.title()} Song"]:
                assert get_shape(title) == shape, title


def test_new_keywords_examples_from_brief():
    assert get_shape("Spike") == "triangle"
    assert get_shape("Balloon") == "rounded"
    # substring matching, as before
    assert get_shape("Peaked") == "tapered"
    assert get_shape("Orbit") == "rounded"


def test_existing_keywords_keep_their_shapes():
    for shape, keywords in OLD_SHAPE_KEYWORDS.items():
        for keyword in keywords:
            assert get_shape(keyword.title()) == shape, keyword

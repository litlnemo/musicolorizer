"""Tests for the "Artist — Title" corner text: tag reading with fallback, and the fade timing.

Tag tests use tiny silent files generated in a temp folder (never the committed audio).
No test opens a real window: drawing tests use SDL's dummy video driver.
"""
import numpy as np
import pygame
import pytest
import soundfile
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.id3 import TIT2, TPE1
from mutagen.wave import WAVE

import musicolorizer
from musicolorizer import (
    TITLE_FADE_SECONDS, TITLE_HIDDEN_SECONDS, TITLE_SHOW_SECONDS,
    get_display_info, get_match_title, make_title_image, read_tags, title_alpha,
)
from colormap import colormap


def silent_file(path):
    """A tiny silent audio file (format from the extension), with no tags."""
    try:
        soundfile.write(str(path), np.zeros(800, dtype=np.float32), 8000)
    except Exception as error:
        # Older libsndfile builds can't write MP3; skip rather than fail on those machines
        pytest.skip(f"this soundfile/libsndfile can't write {path.suffix} files ({error})")
    return str(path)


def tagged_wav(path, artist=None, title=None):
    f = silent_file(path)
    wav = WAVE(f)
    wav.add_tags()
    if artist:
        wav.tags.add(TPE1(encoding=3, text=[artist]))
    if title:
        wav.tags.add(TIT2(encoding=3, text=[title]))
    wav.save()
    return f


def tagged_flac(path, **tags):
    f = silent_file(path)
    flac = FLAC(f)
    for key, value in tags.items():
        flac[key] = value
    flac.save()
    return f


def tagged_mp3(path, **tags):
    f = silent_file(path)
    id3 = EasyID3()
    for key, value in tags.items():
        id3[key] = value
    id3.save(f)
    return f


# ---------- tag reading with fallback ----------

def test_artist_and_title_from_tags(tmp_path):
    song = tagged_mp3(tmp_path / "track01.mp3", artist="Elvis Costello", title="Almost Blue")
    assert read_tags(song) == ("Elvis Costello", "Almost Blue")
    assert get_display_info(song) == "Elvis Costello — Almost Blue"


def test_flac_tags(tmp_path):
    song = tagged_flac(tmp_path / "x.flac", artist="Joni Mitchell", title="Blue")
    assert get_display_info(song) == "Joni Mitchell — Blue"


def test_wav_id3_tags(tmp_path):
    # WAV files come back from mutagen as raw ID3 frames, not simple keys
    song = tagged_wav(tmp_path / "x.wav", artist="Mazzy Star", title="Fade Into You")
    assert get_display_info(song) == "Mazzy Star — Fade Into You"


def test_artist_without_title_uses_filename_title(tmp_path):
    song = tagged_wav(tmp_path / "Red Vines.wav", artist="Aimee Mann")
    assert get_display_info(song) == "Aimee Mann — Red Vines"


def test_title_without_artist(tmp_path):
    song = tagged_flac(tmp_path / "track07.flac", title="Daydreams")
    assert get_display_info(song) == "Daydreams"


def test_no_tags_is_filename_title(tmp_path):
    for ext in ("wav", "flac", "mp3"):
        song = silent_file(tmp_path / f"Almost Blue.{ext}")
        assert read_tags(song) == (None, None)
        assert get_display_info(song) == "Almost Blue"


def test_blank_tags_count_as_missing(tmp_path):
    song = tagged_flac(tmp_path / "Winter.flac", artist="   ", title="")
    assert get_display_info(song) == "Winter"


def test_several_artists_joined(tmp_path):
    song = tagged_flac(tmp_path / "x.flac", artist=["Simon", "Garfunkel"], title="America")
    assert get_display_info(song) == "Simon, Garfunkel — America"


def test_unreadable_file_is_filename_title(tmp_path):
    bad = tmp_path / "Mrs Green.mp3"
    bad.write_bytes(b"not audio at all")
    assert get_display_info(str(bad)) == "Mrs Green"


def test_mutagen_error_is_filename_title(monkeypatch):
    def broken(*args, **kwargs):
        raise OSError("disk trouble")
    monkeypatch.setattr(musicolorizer.mutagen, "File", broken)
    assert get_display_info("/music/Baby Blue.mp3") == "Baby Blue"


def watch_matching(monkeypatch):
    """Record which titles play_song matches colors/shape against and shows on the loading screen."""
    seen = {}
    monkeypatch.setattr(musicolorizer, "get_colorway", lambda title, cmap: seen.setdefault("colors", title) and [[(0, 0, 0), (0, 0, 255)]])
    monkeypatch.setattr(musicolorizer, "get_shape", lambda title: seen.setdefault("shape", title) and "rectangle")
    monkeypatch.setattr(musicolorizer, "analyze_song", lambda f: False)  # stop right after setup
    monkeypatch.setattr(musicolorizer, "show_loading", lambda screen, title: seen.setdefault("loading", title))
    return seen


def test_matching_uses_tag_title(tmp_path, monkeypatch):
    # Tags say "Red", filename says "Blue": colors and shape follow the tag title (issue #17)
    song = tagged_wav(tmp_path / "Almost Blue.wav", artist="Someone", title="Red Sharp Rain")
    seen = watch_matching(monkeypatch)
    assert musicolorizer.play_song(None, song) == musicolorizer.UNPLAYABLE
    # The loading screen shows the same "Artist — Title" as the corner title (issue #47)
    assert seen == {"colors": "Red Sharp Rain", "shape": "Red Sharp Rain", "loading": "Someone — Red Sharp Rain"}


def test_matching_untagged_uses_filename_title(tmp_path, monkeypatch):
    song = silent_file(tmp_path / "Almost Blue.wav")
    seen = watch_matching(monkeypatch)
    assert musicolorizer.play_song(None, song) == musicolorizer.UNPLAYABLE
    assert seen == {"colors": "Almost Blue", "shape": "Almost Blue", "loading": "Almost Blue"}


def test_loading_screen_shows_the_tag_title(tmp_path, monkeypatch):
    # Issue #47: the loading screen used to show the filename title ("track01") while everything else showed the tags
    song = tagged_mp3(tmp_path / "track01.mp3", artist="Elvis Costello", title="Almost Blue")
    seen = watch_matching(monkeypatch)
    assert musicolorizer.play_song(None, song) == musicolorizer.UNPLAYABLE
    assert seen["loading"] == "Elvis Costello — Almost Blue"
    assert seen["loading"] == get_display_info(song)


def test_loading_screen_title_only_tag(tmp_path, monkeypatch):
    # A title tag but no artist: just the tag title, still not the filename
    song = tagged_flac(tmp_path / "track02.flac", title="Big Yellow Taxi")
    seen = watch_matching(monkeypatch)
    musicolorizer.play_song(None, song)
    assert seen["loading"] == "Big Yellow Taxi"


def test_match_title_from_tags(tmp_path):
    song = tagged_mp3(tmp_path / "track01.mp3", artist="Aimee Mann", title="Red Vines")
    assert get_match_title(song) == "Red Vines"  # title only, no artist


def test_match_title_without_tags(tmp_path):
    assert get_match_title(silent_file(tmp_path / "Baby Blue.wav")) == "Baby Blue"


def test_match_title_artist_only(tmp_path):
    # An artist tag but no title tag: the title still comes from the filename
    song = tagged_wav(tmp_path / "Winter.wav", artist="Tori Amos")
    assert get_match_title(song) == "Winter"


def test_match_title_unreadable(monkeypatch):
    monkeypatch.setattr(musicolorizer, "read_tags", lambda f: (None, None))
    assert get_match_title("/music/Mrs Green.mp3") == "Mrs Green"


# ---------- playlist panel titles (issue #24) ----------

def test_panel_titles_use_tags(tmp_path):
    # Same text as the corner title, not the filename
    song = tagged_mp3(tmp_path / "mrs green.mp3", artist="The Posies", title="Mrs. Green")
    assert musicolorizer.PlaybackState([song]).titles == ["The Posies — Mrs. Green"]


def test_panel_titles_fall_back_to_filename(tmp_path):
    song = silent_file(tmp_path / "Daydreams.wav")
    assert musicolorizer.PlaybackState([song]).titles == ["Daydreams"]


def test_panel_titles_mixed_playlist(monkeypatch):
    tags = {"/m/a.mp3": ("Aimee Mann", "Red Vines"), "/m/b.mp3": (None, "Winter"), "/m/Baby Blue.wav": (None, None)}
    monkeypatch.setattr(musicolorizer, "read_tags", lambda f: tags[f])
    state = musicolorizer.PlaybackState(list(tags))
    assert state.titles == ["Aimee Mann — Red Vines", "Winter", "Baby Blue"]


def test_panel_titles_read_tags_once(monkeypatch):
    # The panel is drawn every frame, so tags must not be re-read each time
    calls = []
    monkeypatch.setattr(musicolorizer, "read_tags", lambda f: calls.append(f) or ("Artist", "Song"))
    state = musicolorizer.PlaybackState(["/m/one.mp3", "/m/two.mp3"])
    for _ in range(3):
        assert state.titles == ["Artist — Song", "Artist — Song"]
    assert calls == ["/m/one.mp3", "/m/two.mp3"]


def test_panel_draws_tag_title(headless, monkeypatch):
    # draw_overlay passes the tag text to the row drawing (numbered as before)
    monkeypatch.setattr(musicolorizer, "read_tags", lambda f: ("The Posies", "Mrs. Green"))
    drawn = []
    real = musicolorizer.draw_text
    monkeypatch.setattr(musicolorizer, "draw_text", lambda screen, fonts, kind, text, *a, **k: drawn.append(text) or real(screen, fonts, kind, text, *a, **k))
    state = musicolorizer.PlaybackState(["/m/mrs green.mp3"])
    musicolorizer.draw_overlay(headless, state, musicolorizer.load_fonts())
    assert "1. The Posies — Mrs. Green" in drawn  # numbering kept in front
    assert not any("mrs green" in t for t in drawn)


# ---------- fade timing ----------

def test_timing_constants():
    assert (TITLE_SHOW_SECONDS, TITLE_FADE_SECONDS, TITLE_HIDDEN_SECONDS) == (5, 1, 20)
    assert musicolorizer.TITLE_MODE == "cycle"


def test_default_mode_is_cycle():
    assert title_alpha(10) == title_alpha(10, "cycle") == 0.0


@pytest.mark.parametrize("t", [0, 3, 5, 5.5, 6, 30, 600, 3600])
def test_always_is_full(t):
    assert title_alpha(t, "always") == 1.0


def test_fade_mode():
    assert title_alpha(0, "fade") == 1.0
    assert title_alpha(4.99, "fade") == 1.0
    assert title_alpha(5, "fade") == 1.0
    assert title_alpha(5.25, "fade") == pytest.approx(0.75)
    assert title_alpha(5.5, "fade") == pytest.approx(0.5)
    assert title_alpha(6, "fade") == 0.0
    for t in [7, 26.5, 27, 30, 600]:
        assert title_alpha(t, "fade") == 0.0  # gone for good, never returns


def test_cycle_mode_first_cycle():
    assert title_alpha(0, "cycle") == 1.0
    assert title_alpha(4.9, "cycle") == 1.0
    assert title_alpha(5.5, "cycle") == pytest.approx(0.5)   # fading out 5-6
    for t in [6, 10, 20, 25.99]:
        assert title_alpha(t, "cycle") == 0.0                # hidden 6-26
    assert title_alpha(26, "cycle") == pytest.approx(0.0)
    assert title_alpha(26.25, "cycle") == pytest.approx(0.25)  # fading back in 26-27
    assert title_alpha(26.75, "cycle") == pytest.approx(0.75)
    for t in [27, 29, 31.99]:
        assert title_alpha(t, "cycle") == 1.0                # full 27-32


def test_cycle_mode_repeats():
    period = 27
    for t in [0, 2, 5.5, 8, 26.5, 31]:
        for n in (1, 2, 10):
            assert title_alpha(t + n * period, "cycle") == pytest.approx(title_alpha(t, "cycle"))
    assert title_alpha(32.5, "cycle") == pytest.approx(0.5)  # second fade out 32-33
    assert title_alpha(40, "cycle") == 0.0


@pytest.mark.parametrize("mode", ["always", "fade", "cycle"])
def test_alpha_always_between_0_and_1(mode):
    for tenth in range(0, 1200):
        assert 0.0 <= title_alpha(tenth / 10, mode) <= 1.0


def test_before_start_counts_as_start():
    # get_pos() is -1 before a song plays; the text should be fully shown then
    assert title_alpha(-1, "cycle") == 1.0
    assert title_alpha(-1, "fade") == 1.0


def test_bad_mode():
    with pytest.raises(ValueError):
        title_alpha(0, "sometimes")


# ---------- drawing (headless) ----------

@pytest.fixture
def headless(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    yield pygame.display.set_mode([400, 300])
    pygame.quit()


def test_title_image_fits_window(headless):
    long_name = "A Very Long Artist Name — " + "And An Even Longer Song Title " * 5
    image = make_title_image(long_name, 400 - 2 * musicolorizer.TITLE_MARGIN)
    assert image.get_width() <= 400 - 2 * musicolorizer.TITLE_MARGIN


def test_draw_title_bottom_left(headless):
    screen = headless
    screen.fill((0, 0, 0))
    image = make_title_image("Elvis Costello — Almost Blue", 300)
    musicolorizer.draw_title(screen, image, 1.0)
    bottom_left = screen.subsurface((0, 200, 200, 100))
    top_right = screen.subsurface((200, 0, 200, 150))
    assert pygame.transform.average_color(bottom_left)[:3] != (0, 0, 0)
    assert pygame.transform.average_color(top_right)[:3] == (0, 0, 0)


def test_draw_title_hidden_draws_nothing(headless):
    screen = headless
    screen.fill((0, 0, 0))
    musicolorizer.draw_title(screen, make_title_image("Almost Blue", 300), 0.0)
    assert pygame.transform.average_color(screen)[:3] == (0, 0, 0)


def test_play_song_caption_and_timer(tmp_path, headless, monkeypatch):
    from test_playlist import make_tiny_wav
    song = make_tiny_wav(tmp_path / "Love Song.wav", seconds=2)
    wav = WAVE(song)
    wav.add_tags()
    wav.tags.add(TPE1(encoding=3, text=["The Cure"]))
    wav.save()
    pygame.mixer.music.set_endevent(musicolorizer.SONG_END)

    times = []
    real_alpha = musicolorizer.title_alpha
    monkeypatch.setattr(musicolorizer, "title_alpha", lambda t, mode=None: times.append(t) or real_alpha(t, mode))
    frames = iter([[], [], [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q)]])
    monkeypatch.setattr(pygame.event, "get", lambda *a, **k: next(frames, []))

    assert musicolorizer.play_song(headless, song) == musicolorizer.QUIT
    assert pygame.display.get_caption()[0] == "Musicolorizer — The Cure — Love Song"
    assert len(times) == 2 and all(0 <= t < 5 for t in times)  # timer starts at the beginning of the song

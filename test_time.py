"""Tests for the elapsed / total time in the bottom-right corner (issue #41)."""
import pygame
import pytest

import musicolorizer
from musicolorizer import QUIT, format_time, play_song, song_length, time_text
from test_gui import headless_screen, key, scripted_frames  # noqa: F401 (headless_screen is a fixture)
from test_playlist import make_tiny_wav
from test_title import tagged_mp3


@pytest.mark.parametrize("seconds, expected", [
    (0, "0:00"),
    (7, "0:07"),
    (59.9, "0:59"),       # whole seconds only, like a player's clock
    (83, "1:23"),
    (225, "3:45"),
    (600, "10:00"),
    (3600, "1:00:00"),    # from an hour on, hours are shown too
    (3725, "1:02:05"),
])
def test_format_time(seconds, expected):
    assert format_time(seconds) == expected


def test_format_time_never_negative():
    assert format_time(-1) == "0:00"


def test_time_text():
    assert time_text(83, 225) == "1:23 / 3:45"
    assert time_text(83, None) == "1:23"          # length unknown: elapsed only
    assert time_text(230, 225) == "3:45 / 3:45"   # never runs past the end


def test_song_length_of_a_real_file(tmp_path):
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    assert song_length(song) == pytest.approx(2.0, abs=0.01)


def test_song_length_of_a_tagged_file(tmp_path):
    song = tagged_mp3(tmp_path / "track01.mp3", artist="Elvis Costello", title="Almost Blue")
    assert song_length(song) == pytest.approx(0.1, abs=0.06)  # silent_file writes 800 samples at 8000 Hz


def test_song_length_unreadable_is_none(tmp_path):
    bad = tmp_path / "Mrs Green.mp3"
    bad.write_bytes(b"not really audio")
    assert song_length(str(bad)) is None
    assert song_length(str(tmp_path / "missing.mp3")) is None


def record_times(monkeypatch):
    times = []
    real = musicolorizer.draw_time
    monkeypatch.setattr(musicolorizer, "draw_time", lambda screen, fonts, text: times.append(text) or real(screen, fonts, text))
    return times


def test_time_drawn_every_frame_in_the_corner(tmp_path, headless_screen, monkeypatch):
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    monkeypatch.setattr(pygame.mixer.music, "get_pos", lambda: 1500)
    times = record_times(monkeypatch)
    scripted_frames(monkeypatch, [[], [], [key(pygame.K_q)]])
    assert play_song(headless_screen, song) == QUIT
    assert times == ["0:01 / 0:02", "0:01 / 0:02"]


def test_time_shows_elapsed_only_when_length_unknown(tmp_path, headless_screen, monkeypatch):
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    monkeypatch.setattr(musicolorizer, "song_length", lambda f: None)
    monkeypatch.setattr(pygame.mixer.music, "get_pos", lambda: 65000)
    times = record_times(monkeypatch)
    scripted_frames(monkeypatch, [[], [key(pygame.K_q)]])
    play_song(headless_screen, song)
    assert times == ["1:05"]


def test_time_holds_while_paused_and_stays_with_panel_hidden_and_any_title_mode(tmp_path, headless_screen, monkeypatch):
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    position = {"ms": 0}

    def fake_pos():
        return position["ms"]

    monkeypatch.setattr(pygame.mixer.music, "get_pos", fake_pos)
    monkeypatch.setattr(pygame.mixer.music, "pause", lambda: None)
    monkeypatch.setattr(pygame.mixer.music, "unpause", lambda: None)
    times = record_times(monkeypatch)

    def frame(events, ms):
        position["ms"] = ms  # where the mixer says it is during this frame (it holds still while paused)
        return events

    frames = iter([
        lambda: frame([], 1000),
        lambda: frame([key(pygame.K_p)], 1000),   # pause
        lambda: frame([], 1000),
        lambda: frame([key(pygame.K_p)], 1000),   # resume
        lambda: frame([key(pygame.K_h)], 2000),   # hide the panel
        lambda: frame([key(pygame.K_t)], 2000),   # change the title mode
        lambda: frame([key(pygame.K_q)], 2000),
    ])
    monkeypatch.setattr(pygame.event, "get", lambda *a, **k: next(frames, lambda: [])())
    assert play_song(headless_screen, song) == QUIT
    assert times == ["0:01 / 0:02"] * 4 + ["0:02 / 0:02"] * 2


def test_time_is_drawn_in_the_bottom_right_corner(headless_screen):
    fonts = musicolorizer.load_fonts()
    headless_screen.fill((0, 0, 0))
    musicolorizer.draw_time(headless_screen, fonts, "1:23 / 3:45")
    width, height = headless_screen.get_size()
    lit = [(x, y) for x in range(width) for y in range(height) if headless_screen.get_at((x, y))[:3] != (0, 0, 0)]
    assert lit
    margin = musicolorizer.TITLE_MARGIN
    assert max(x for x, _ in lit) < width - margin + 1
    assert max(y for _, y in lit) < height - margin + 1
    assert min(x for x, _ in lit) > width // 2   # right side
    assert min(y for _, y in lit) > height // 2  # bottom


def test_corner_title_leaves_room_for_the_time(tmp_path, headless_screen, monkeypatch):
    song = make_tiny_wav(tmp_path / ("Very " * 30 + "Long Title.wav"), seconds=2)
    widths = []
    real = musicolorizer.make_title_image
    monkeypatch.setattr(musicolorizer, "make_title_image", lambda text, max_width: widths.append(max_width) or real(text, max_width))
    scripted_frames(monkeypatch, [[key(pygame.K_q)]])
    play_song(headless_screen, song)
    fonts = musicolorizer.load_fonts()
    time_room = fonts["row"].size("0:02 / 0:02")[0]
    assert widths and widths[0] + time_room + 2 * musicolorizer.TITLE_MARGIN < headless_screen.get_width()

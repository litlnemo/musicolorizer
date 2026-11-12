"""Tests for the volume control: + and - keys and the panel's status line (issue #39)."""
import pygame
import pytest

import musicolorizer
from musicolorizer import (
    QUIT, VOLUME_DOWN, VOLUME_STEP, VOLUME_UP, PlaybackState, draw_overlay, next_action, panel_rect,
    play_song, run_playlist, status_layout, status_text, title_mode_layout,
)
from test_gui import headless_screen, key, offscreen, record_text, scripted_frames  # noqa: F401 (fixtures)
from test_playlist import make_tiny_wav


def typed(k, char):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=char)


def test_volume_starts_full():
    assert PlaybackState(["a.mp3"]).volume == 1.0


def test_plus_and_minus_keys():
    assert next_action(typed(pygame.K_EQUALS, "+")) == VOLUME_UP   # shift = on most keyboards
    assert next_action(typed(pygame.K_EQUALS, "=")) == VOLUME_UP   # the unshifted + key
    assert next_action(key(pygame.K_PLUS)) == VOLUME_UP
    assert next_action(key(pygame.K_KP_PLUS)) == VOLUME_UP
    assert next_action(typed(pygame.K_MINUS, "-")) == VOLUME_DOWN
    assert next_action(key(pygame.K_KP_MINUS)) == VOLUME_DOWN


def test_volume_steps_and_clamps():
    state = PlaybackState(["a.mp3"])
    assert VOLUME_STEP == 0.05
    assert state.change_volume(VOLUME_STEP) == 1.0           # already full: stays at 1.0
    assert state.change_volume(-VOLUME_STEP) == 0.95
    assert state.change_volume(-VOLUME_STEP) == 0.9
    for _ in range(30):
        state.change_volume(-VOLUME_STEP)
    assert state.volume == 0.0                               # never below silent
    assert state.change_volume(VOLUME_STEP) == 0.05
    for _ in range(30):
        state.change_volume(VOLUME_STEP)
    assert state.volume == 1.0                               # never above full


def test_volume_stays_from_song_to_song():
    state = PlaybackState(["a.mp3", "b.mp3"])
    state.change_volume(-0.25)
    state.start(1)
    assert state.volume == 0.75


@pytest.mark.parametrize("volume, text", [(1.0, "Vol: 100%"), (0.8, "Vol: 80%"), (0.05, "Vol: 5%"), (0.0, "Vol: 0%")])
def test_status_line_shows_the_level_as_a_percent(volume, text):
    state = PlaybackState(["a.mp3"])
    state.volume = volume
    assert status_text(state) == text


def test_status_line_drawn_under_the_title_button_inside_the_panel(offscreen, monkeypatch):
    for count in (1, 3, 20):
        state = PlaybackState([f"{n}.mp3" for n in range(count)])
        state.volume = 0.8
        drawn = record_text(monkeypatch)
        draw_overlay(offscreen, state, musicolorizer.load_fonts())
        assert drawn[-1] == "Vol: 80%"
        line = status_layout(offscreen.get_size(), state)
        assert line.top >= title_mode_layout(offscreen.get_size(), state).bottom
        area = panel_rect(offscreen.get_size(), state)
        assert area.contains(line)  # the panel, and the mouse-wheel area, include it


def test_status_line_hides_with_the_panel(offscreen, monkeypatch):
    state = PlaybackState(["a.mp3"])
    state.toggle_panel()
    drawn = record_text(monkeypatch)
    draw_overlay(offscreen, state, musicolorizer.load_fonts())
    assert not any(text.startswith("Vol:") for text in drawn)


def record_volumes(monkeypatch):
    calls = []
    monkeypatch.setattr(pygame.mixer.music, "set_volume", lambda v: calls.append(v))
    return calls


def test_volume_change_keeps_the_song_playing(tmp_path, headless_screen, monkeypatch):
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    state = PlaybackState([song])
    monkeypatch.setattr(musicolorizer, "now_playing", state)
    volumes = record_volumes(monkeypatch)
    stops = []
    monkeypatch.setattr(pygame.mixer.music, "stop", lambda: stops.append(1))
    drawn = record_text(monkeypatch)
    minus, plus = typed(pygame.K_MINUS, "-"), typed(pygame.K_EQUALS, "+")
    scripted_frames(monkeypatch, [[], [minus], [minus, minus], [plus], [key(pygame.K_q)]])
    assert play_song(headless_screen, song) == QUIT
    assert volumes == [1.0, 0.95, 0.9, 0.85, 0.9]  # set when the song starts, then on each press
    assert len(stops) == 1                          # only the quit stopped the music
    assert [t for t in drawn if t.startswith("Vol:")] == ["Vol: 100%", "Vol: 95%", "Vol: 85%", "Vol: 90%"]


def test_volume_applies_to_every_song(tmp_path, headless_screen, monkeypatch):
    songs = [make_tiny_wav(tmp_path / f"{name}.wav", seconds=2) for name in ("One", "Two")]
    volumes = record_volumes(monkeypatch)
    minus = typed(pygame.K_MINUS, "-")
    scripted_frames(monkeypatch, [[minus, minus], [key(pygame.K_n)], [], [key(pygame.K_q)]])
    assert run_playlist(headless_screen, songs) == 2
    assert volumes == [1.0, 0.95, 0.9, 0.9]  # song 2 starts at the level set on song 1


def test_volume_keys_work_while_the_panel_is_hidden(tmp_path, headless_screen, monkeypatch):
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    volumes = record_volumes(monkeypatch)
    scripted_frames(monkeypatch, [[key(pygame.K_h)], [typed(pygame.K_MINUS, "-")], [key(pygame.K_q)]])
    assert play_song(headless_screen, song) == QUIT
    assert volumes == [1.0, 0.95]

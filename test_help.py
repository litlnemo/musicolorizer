"""Tests for the in-app key help: ? shows and hides a panel listing every key (issue #51)."""
import pygame
import pytest

import musicolorizer
from musicolorizer import (
    HELP_LINES, QUIT, TOGGLE_HELP, PlaybackState, chip_layout, control_layout, draw_help, help_layout,
    next_action, panel_rect, play_song,
)
from test_gui import click, headless_screen, key, offscreen, record_text, scripted_frames  # noqa: F401 (fixtures)
from test_playlist import make_tiny_wav

EXPECTED_LINES = [
    "H — Hide / show the playlist panel",
    "T — Corner-title mode (always / fade / cycle)",
    "P — Pause / resume",
    "N or Right arrow — Skip to the next song",
    "Left arrow — Previous song (or restart it)",
    "Up / Down — Scroll the playlist",
    "Mouse wheel over the panel — Scroll the playlist",
    "+ / - — Volume up / down",
    "S — Shuffle on / off",
    "R — Repeat (off / all / one)",
    "Q — Quit",
    "Click a song in the playlist — Jump to it",
    "? — Show / hide this help",
]


def question_mark():
    return pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SLASH, unicode="?", mod=pygame.KMOD_SHIFT)


def test_help_hidden_by_default():
    assert PlaybackState(["a.mp3"]).help_visible is False


def test_question_mark_toggles_help():
    assert next_action(question_mark()) == TOGGLE_HELP
    assert next_action(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SLASH, unicode="/")) is None  # plain / does nothing
    state = PlaybackState(["a.mp3"])
    assert state.toggle_help() is True
    assert state.toggle_help() is False


def test_help_lists_every_key_in_order(offscreen, monkeypatch):
    assert list(HELP_LINES) == EXPECTED_LINES
    state = PlaybackState(["a.mp3"])
    state.toggle_help()
    drawn = record_text(monkeypatch)
    draw_help(offscreen, state, musicolorizer.load_fonts())
    assert drawn == EXPECTED_LINES


def test_every_key_in_the_help_does_something():
    keys = {
        "H": pygame.K_h, "T": pygame.K_t, "P": pygame.K_p, "N": pygame.K_n, "Right": pygame.K_RIGHT,
        "Left": pygame.K_LEFT, "Up": pygame.K_UP, "Down": pygame.K_DOWN, "S": pygame.K_s, "R": pygame.K_r, "Q": pygame.K_q,
    }
    for name, k in keys.items():
        assert next_action(pygame.event.Event(pygame.KEYDOWN, key=k, unicode="")) is not None, name
    for char, k in (("+", pygame.K_EQUALS), ("-", pygame.K_MINUS), ("?", pygame.K_SLASH)):
        assert next_action(pygame.event.Event(pygame.KEYDOWN, key=k, unicode=char)) is not None, char


def test_help_lines_fit_the_panel():
    pygame.font.init()
    font = musicolorizer.load_fonts()["header"]
    area = help_layout((960, 1000), PlaybackState(["a.mp3"]))
    assert max(font.size(line)[0] for line in HELP_LINES) <= area.width - 2 * musicolorizer.PANEL_PADDING


def test_help_hidden_draws_nothing(offscreen, monkeypatch):
    drawn = record_text(monkeypatch)
    offscreen.fill((1, 2, 3))
    draw_help(offscreen, PlaybackState(["a.mp3"]), musicolorizer.load_fonts())
    assert drawn == []
    assert offscreen.get_at((50, 200))[:3] == (1, 2, 3)


def test_help_sits_below_the_playlist_panel():
    for count in (1, 3, 20):
        state = PlaybackState([f"{n}.mp3" for n in range(count)])
        area = help_layout((400, 900), state)
        assert area.top == panel_rect((400, 900), state).bottom + musicolorizer.PANEL_MARGIN
        assert area.left == musicolorizer.PANEL_MARGIN


def test_help_sits_top_left_when_the_panel_is_hidden():
    state = PlaybackState(["a.mp3"])
    state.toggle_panel()
    area = help_layout((400, 900), state)
    chip = chip_layout((400, 900))
    assert area.left == musicolorizer.PANEL_MARGIN
    assert area.top == chip.bottom + musicolorizer.PANEL_MARGIN  # just under the "Show playlist" chip, which stays clickable
    assert not area.colliderect(chip)


def test_toggling_help_keeps_the_song_playing(tmp_path, headless_screen, monkeypatch):
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    state = PlaybackState([song])
    monkeypatch.setattr(musicolorizer, "now_playing", state)
    stops = []
    monkeypatch.setattr(pygame.mixer.music, "stop", lambda: stops.append(1))
    shown = []
    real = musicolorizer.draw_help
    monkeypatch.setattr(musicolorizer, "draw_help", lambda screen, st, fonts: shown.append(st.help_visible) or real(screen, st, fonts))
    scripted_frames(monkeypatch, [[], [question_mark()], [], [question_mark()], [key(pygame.K_q)]])
    assert play_song(headless_screen, song) == QUIT
    assert shown == [False, True, True, False]
    assert len(stops) == 1  # only the quit stopped the song


def test_keys_and_clicks_still_work_with_help_showing(tmp_path, headless_screen, monkeypatch):
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    pauses = []
    monkeypatch.setattr(pygame.mixer.music, "pause", lambda: pauses.append("pause"))
    monkeypatch.setattr(pygame.mixer.music, "unpause", lambda: pauses.append("unpause"))
    skip = control_layout(headless_screen.get_size())[musicolorizer.NEXT]
    scripted_frames(monkeypatch, [[question_mark()], [key(pygame.K_p)], [key(pygame.K_p)], [click(skip.center)]])
    assert play_song(headless_screen, song) == musicolorizer.NEXT
    assert pauses == ["pause", "unpause"]


def test_help_shows_with_the_panel_hidden(tmp_path, headless_screen, monkeypatch):
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    drawn = record_text(monkeypatch)
    scripted_frames(monkeypatch, [[key(pygame.K_h)], [question_mark()], [key(pygame.K_q)]])
    assert play_song(headless_screen, song) == QUIT
    assert drawn.count(HELP_LINES[0]) == 1

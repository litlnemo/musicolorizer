"""Tests for repeat: R cycles off -> all -> one -> off (issue #43)."""
import random

import pygame
import pytest

import musicolorizer
from musicolorizer import (
    CYCLE_REPEAT, ENDED, NEXT, PREVIOUS, QUIT, UNPLAYABLE,
    PlaybackState, next_action, play_song, run_playlist, status_text,
)
from test_gui import headless_screen, key, record_text, scripted_frames  # noqa: F401 (fixtures)
from test_playlist import make_tiny_wav
from test_shuffle import scripted_run, shuffle_on

SONGS = ["/m/A.mp3", "/m/B.mp3", "/m/C.mp3"]


def repeat(mode):
    def change(state):
        state.repeat = mode
    return change


def test_repeat_off_by_default():
    assert PlaybackState(SONGS).repeat == 'off'


def test_r_key_cycles_off_all_one_off():
    assert next_action(key(pygame.K_r)) == CYCLE_REPEAT
    state = PlaybackState(SONGS)
    assert [state.next_repeat() for _ in range(4)] == ['all', 'one', 'off', 'all']


@pytest.mark.parametrize("mode, text", [('off', "Vol: 80%"), ('all', "Vol: 80% · Repeat: all"), ('one', "Vol: 80% · Repeat: one")])
def test_status_line_shows_repeat_while_on(mode, text):
    state = PlaybackState(SONGS)
    state.volume = 0.8
    state.repeat = mode
    assert status_text(state) == text


def test_status_line_with_shuffle_and_repeat():
    state = PlaybackState(SONGS)
    state.toggle_shuffle()
    state.repeat = 'all'
    assert status_text(state) == "Vol: 100% · Shuffle · Repeat: all"


def test_playlist_still_ends_after_the_last_song_with_repeat_off(monkeypatch):
    played = scripted_run(monkeypatch, [ENDED, ENDED, ENDED])
    assert run_playlist(None, SONGS) == 3
    assert played == [0, 1, 2]


def test_repeat_one_plays_a_finished_song_again(monkeypatch):
    played = scripted_run(monkeypatch, [(ENDED, repeat('one')), ENDED, ENDED, QUIT])
    run_playlist(None, SONGS)
    assert played == [0, 0, 0, 0]


def test_repeat_one_skip_moves_on(monkeypatch):
    played = scripted_run(monkeypatch, [(NEXT, repeat('one')), ENDED, NEXT, ENDED, QUIT])
    run_playlist(None, SONGS)
    assert played == [0, 1, 1, 2, 2]


def test_repeat_one_skip_at_the_last_song_ends_the_playlist(monkeypatch):
    played = scripted_run(monkeypatch, [NEXT, NEXT, (NEXT, repeat('one'))])
    assert run_playlist(None, SONGS) == 3
    assert played == [0, 1, 2]


def test_repeat_all_wraps_to_the_first_song_when_the_last_one_ends(monkeypatch):
    played = scripted_run(monkeypatch, [(ENDED, repeat('all')), ENDED, ENDED, ENDED, QUIT])
    run_playlist(None, SONGS)
    assert played == [0, 1, 2, 0, 1]


def test_repeat_all_skip_at_the_last_song_wraps(monkeypatch):
    played = scripted_run(monkeypatch, [(NEXT, repeat('all')), NEXT, NEXT, QUIT])
    run_playlist(None, SONGS)
    assert played == [0, 1, 2, 0]


def test_repeat_all_wraps_past_songs_that_cant_play(monkeypatch):
    played = scripted_run(monkeypatch, [UNPLAYABLE, (ENDED, repeat('all')), ENDED, ENDED, QUIT])
    run_playlist(None, SONGS)
    assert played == [0, 1, 2, 1, 2]  # A couldn't play, so B and C go round


def test_repeat_all_stops_if_nothing_can_play(monkeypatch):
    def fake_play(screen, songfile):
        musicolorizer.now_playing.repeat = 'all'
        return UNPLAYABLE
    monkeypatch.setattr(musicolorizer, "play_song", fake_play)
    assert run_playlist(None, SONGS) == 0  # doesn't go round forever


def test_previous_unchanged_in_repeat(monkeypatch):
    played = scripted_run(monkeypatch, [(ENDED, repeat('one')), PREVIOUS, ENDED, QUIT])
    run_playlist(None, SONGS)
    assert played == [0, 0, 0, 0]  # Previous on the first song restarts it, as before


def test_repeat_one_wins_over_shuffle(monkeypatch):
    def both(state):
        state.toggle_shuffle()
        state.repeat = 'one'
    played = scripted_run(monkeypatch, [(ENDED, both), ENDED, QUIT])
    run_playlist(None, SONGS)
    assert played == [0, 0, 0]


def test_repeat_one_and_shuffle_skip_is_random(monkeypatch):
    picks = iter([2])
    monkeypatch.setattr(random, "choice", lambda options: next(picks))

    def both(state):
        state.toggle_shuffle()
        state.repeat = 'one'
    played = scripted_run(monkeypatch, [(NEXT, both), QUIT])
    run_playlist(None, SONGS)
    assert played == [0, 2]


def test_repeat_all_and_shuffle_keeps_shuffling(monkeypatch):
    random.seed(6)

    def both(state):
        state.toggle_shuffle()
        state.repeat = 'all'
    played = scripted_run(monkeypatch, [(ENDED, both)] + [ENDED] * 10 + [QUIT])
    run_playlist(None, SONGS)
    assert len(played) == 12
    assert all(a != b for a, b in zip(played, played[1:]))


def test_r_in_play_song_keeps_playing(tmp_path, headless_screen, monkeypatch):
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    state = PlaybackState([song])
    monkeypatch.setattr(musicolorizer, "now_playing", state)
    stops = []
    monkeypatch.setattr(pygame.mixer.music, "stop", lambda: stops.append(1))
    drawn = record_text(monkeypatch)
    r = key(pygame.K_r)
    scripted_frames(monkeypatch, [[r], [r], [r], [key(pygame.K_q)]])
    assert play_song(headless_screen, song) == QUIT
    assert len(stops) == 1
    assert [t for t in drawn if t.startswith("Vol:")] == ["Vol: 100% · Repeat: all", "Vol: 100% · Repeat: one", "Vol: 100%"]

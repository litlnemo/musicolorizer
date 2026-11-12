"""Tests for shuffle: S plays the songs in a random order, Previous goes back through what played (issue #42)."""
import random

import pygame
import pytest

import musicolorizer
from musicolorizer import (
    ENDED, JUMP, NEXT, PREVIOUS, QUIT, RESTART, TOGGLE_SHUFFLE, UNPLAYABLE,
    PlaybackState, next_action, play_song, random_next, run_playlist, status_text,
)
from test_gui import headless_screen, key, record_text, scripted_frames  # noqa: F401 (fixtures)
from test_playlist import make_tiny_wav

SONGS = [f"/m/Song {n}.mp3" for n in range(1, 7)]


def scripted_run(monkeypatch, steps):
    """Stand-in for play_song. Each step is a result, or a (result, change) pair where change(state) runs
    while that song plays, like a key press would (e.g. turning shuffle on). Records the index of each song played."""
    played = []
    queue = iter(steps)

    def fake_play(screen, songfile):
        state = musicolorizer.now_playing
        played.append(state.index)
        assert state.current_song == songfile
        step = next(queue, QUIT)
        if isinstance(step, tuple) and callable(step[1]):
            result, change = step
            change(state)
            return result
        return step

    monkeypatch.setattr(musicolorizer, "play_song", fake_play)
    return played


def shuffle_on(state):
    state.toggle_shuffle()


def test_shuffle_off_by_default():
    state = PlaybackState(SONGS)
    assert state.shuffle is False
    assert state.history == []


def test_s_key_and_toggle():
    assert next_action(key(pygame.K_s)) == TOGGLE_SHUFFLE
    state = PlaybackState(SONGS)
    assert state.toggle_shuffle() is True
    assert state.toggle_shuffle() is False


def test_status_line_shows_shuffle_only_while_on():
    state = PlaybackState(SONGS)
    state.volume = 0.8
    assert status_text(state) == "Vol: 80%"
    state.toggle_shuffle()
    assert status_text(state) == "Vol: 80% · Shuffle"


def test_random_next_never_the_current_song():
    random.seed(1)
    for index in range(6):
        picks = {random_next(index, 6, set()) for _ in range(200)}
        assert index not in picks
        assert picks == set(range(6)) - {index}  # every other song can come up


def test_random_next_skips_unplayable_and_handles_one_song():
    for _ in range(50):
        assert random_next(0, 4, {1, 2}) == 3
    assert random_next(2, 4, {0, 1, 3}) == 2     # the only playable song plays again
    assert random_next(0, 1, set()) == 0         # a one-song playlist repeats it
    assert random_next(0, 2, {0, 1}) is None     # nothing left that can play


@pytest.mark.parametrize("result", [ENDED, NEXT])
def test_next_song_is_random_and_never_the_current_one(monkeypatch, result):
    random.seed(7)
    played = scripted_run(monkeypatch, [(result, shuffle_on)] + [result] * 40 + [QUIT])
    run_playlist(None, SONGS)
    assert played[0] == 0
    assert all(a != b for a, b in zip(played, played[1:]))   # never the same song twice in a row
    assert played[1:13] != [1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5, 0][:12]  # not playlist order
    assert set(played) == set(range(6))


def test_shuffle_keeps_playing_past_the_last_song(monkeypatch):
    # In playlist order the playlist ends after the last song; shuffled there's always a next song
    random.seed(3)
    played = scripted_run(monkeypatch, [(ENDED, shuffle_on)] + [ENDED] * 20 + [QUIT])
    assert run_playlist(None, SONGS[:3]) == 22
    assert len(played) == 22


def test_previous_goes_back_through_the_history(monkeypatch):
    random.seed(11)
    played = scripted_run(monkeypatch, [(NEXT, shuffle_on), NEXT, NEXT, PREVIOUS, PREVIOUS, PREVIOUS, QUIT])
    run_playlist(None, SONGS)
    first, second, third, fourth = played[:4]
    # Back from the 4th song goes to the 3rd, then the 2nd, then the 1st...
    assert played[4:7] == [third, second, first]


def test_previous_with_no_earlier_song_behaves_as_before(monkeypatch):
    # Shuffle turned on during the first song: Previous has no history to go back to, so it restarts song 1
    played = scripted_run(monkeypatch, [(PREVIOUS, shuffle_on), QUIT])
    run_playlist(None, SONGS)
    assert played == [0, 0]


def test_restart_doesnt_add_to_the_history(monkeypatch):
    random.seed(5)
    played = scripted_run(monkeypatch, [(NEXT, shuffle_on), RESTART, RESTART, PREVIOUS, QUIT])
    run_playlist(None, SONGS)
    assert played[1] == played[2] == played[3]
    assert played[4] == 0  # Previous after restarting goes back to the song before, not the same song


def test_turning_shuffle_off_resumes_playlist_order(monkeypatch):
    # Shuffled picks are 3, then 1; shuffle is turned off while song index 1 plays, so 2 and 3 follow in order
    picks = iter([3, 1])
    monkeypatch.setattr(random, "choice", lambda options: next(picks))
    played = scripted_run(monkeypatch, [(NEXT, shuffle_on), NEXT, (NEXT, shuffle_on), NEXT, QUIT])
    run_playlist(None, SONGS)
    assert played == [0, 3, 1, 2, 3]


def test_clicking_a_row_while_shuffled(monkeypatch):
    random.seed(4)
    played = scripted_run(monkeypatch, [(NEXT, shuffle_on), (JUMP, 4), PREVIOUS, QUIT])
    run_playlist(None, SONGS)
    assert played[2] == 4                 # the clicked song plays
    assert played[3] == played[1]         # and it joined the history: Previous goes back to the song before it


def test_shuffle_skips_songs_that_cant_play(monkeypatch):
    random.seed(9)
    played = []

    def fake_play(screen, songfile):
        state = musicolorizer.now_playing
        played.append(state.index)
        if len(played) == 1:
            state.toggle_shuffle()
        if state.index in (2, 3):
            return UNPLAYABLE
        return NEXT if len(played) < 30 else QUIT

    monkeypatch.setattr(musicolorizer, "play_song", fake_play)
    run_playlist(None, SONGS)
    assert played.count(2) <= 1 and played.count(3) <= 1   # each bad song is tried at most once
    assert len(played) == 30


def test_shuffle_previous_skips_a_song_that_couldnt_play(monkeypatch):
    picks = iter([2, 4])
    monkeypatch.setattr(random, "choice", lambda options: next(picks))

    def fake_play(screen, songfile):
        state = musicolorizer.now_playing
        fake_play.played.append(state.index)
        if state.index == 0 and len(fake_play.played) == 1:
            state.toggle_shuffle()
            return NEXT
        if state.index == 2:
            return UNPLAYABLE
        return PREVIOUS if state.index == 4 else QUIT

    fake_play.played = []
    monkeypatch.setattr(musicolorizer, "play_song", fake_play)
    run_playlist(None, SONGS)
    assert fake_play.played == [0, 2, 4, 0]  # back from 4 lands on 0, not on the song that couldn't play


def test_panel_rows_stay_in_playlist_order_while_shuffled():
    state = PlaybackState(SONGS)
    state.toggle_shuffle()
    state.start(4)
    assert state.titles == [f"Song {n}" for n in range(1, 7)]
    assert state.index == 4  # the playing song is the one highlighted


def test_s_in_play_song_keeps_playing(tmp_path, headless_screen, monkeypatch):
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    state = PlaybackState([song, str(tmp_path / "Two.wav")])
    monkeypatch.setattr(musicolorizer, "now_playing", state)
    stops = []
    monkeypatch.setattr(pygame.mixer.music, "stop", lambda: stops.append(1))
    drawn = record_text(monkeypatch)
    scripted_frames(monkeypatch, [[key(pygame.K_s)], [key(pygame.K_s)], [key(pygame.K_q)]])
    assert play_song(headless_screen, song) == QUIT
    assert len(stops) == 1  # only the quit stopped the song
    assert [t for t in drawn if t.startswith("Vol:")] == ["Vol: 100% · Shuffle", "Vol: 100%"]

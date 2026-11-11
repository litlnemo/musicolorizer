"""Tests for playlist building and song advancement.

Uses only tiny files generated on the fly (or empty placeholder files),
never the large audio files committed in the repo.
"""
import os
import wave

import numpy as np
import pygame
import pytest

import musicolorizer
from musicolorizer import (
    ENDED, NEXT, QUIT, UNPLAYABLE, SONG_END,
    analyze_song, build_playlist, clean_path, is_audio_file,
    next_action, play_song, run_playlist, scan_folder,
)


def touch(path):
    """Create an empty placeholder file (playlist building never reads the contents)."""
    path.write_bytes(b"")
    return str(path)


def make_tiny_wav(path, seconds=0.3, sample_rate=8000):
    """Write a very short sine-wave .wav file for tests that need real audio."""
    t = np.linspace(0, seconds, int(sample_rate * seconds), endpoint=False)
    samples = (0.3 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(samples.tobytes())
    return str(path)


# ---------- input parsing ----------

def test_clean_path():
    assert clean_path("  song.mp3  ") == "song.mp3"
    assert clean_path('"/Music/My Song.mp3"') == "/Music/My Song.mp3"
    assert clean_path("'/Music/My Song.mp3'") == "/Music/My Song.mp3"
    assert clean_path("") == ""


def test_is_audio_file():
    assert is_audio_file("a.mp3")
    assert is_audio_file("a.WAV")
    assert is_audio_file("a.flac")
    assert not is_audio_file("a.txt")
    assert not is_audio_file("mp3")


def test_single_file_unchanged(tmp_path):
    song = touch(tmp_path / "Almost Blue.mp3")
    assert build_playlist(song) == [song]
    assert build_playlist(f"  {song}  ") == [song]


def test_single_file_with_comma_in_name(tmp_path):
    song = touch(tmp_path / "Hello, Goodbye.mp3")
    assert build_playlist(song) == [song]


def test_comma_separated(tmp_path):
    a = touch(tmp_path / "a.mp3")
    b = touch(tmp_path / "b.wav")
    c = touch(tmp_path / "c.flac")
    assert build_playlist(f"{a}, {b},{c}") == [a, b, c]


def test_comma_separated_keeps_order_and_missing(tmp_path):
    a = touch(tmp_path / "a.mp3")
    missing = str(tmp_path / "nope.mp3")
    # Missing files stay in the list; play_song reports and skips them
    assert build_playlist(f"{missing}, {a}") == [missing, a]


def test_comma_separated_ignores_blanks(tmp_path):
    a = touch(tmp_path / "a.mp3")
    assert build_playlist(f"{a}, , ") == [a]


def test_empty_input():
    assert build_playlist("") == []
    assert build_playlist("   ") == []


# ---------- folder scan ----------

def test_folder_scan_sorted_and_filtered(tmp_path):
    touch(tmp_path / "zebra.mp3")
    touch(tmp_path / "Apple.wav")
    touch(tmp_path / "middle.FLAC")
    touch(tmp_path / "notes.txt")
    touch(tmp_path / "cover.jpg")
    (tmp_path / "subfolder.mp3").mkdir()  # a folder named like a song is not a song
    names = [os.path.basename(p) for p in build_playlist(str(tmp_path))]
    assert names == ["Apple.wav", "middle.FLAC", "zebra.mp3"]


def test_folder_paths_are_full(tmp_path):
    touch(tmp_path / "a.mp3")
    assert scan_folder(str(tmp_path)) == [os.path.join(str(tmp_path), "a.mp3")]


def test_folder_with_trailing_slash_and_quotes(tmp_path):
    touch(tmp_path / "a.mp3")
    assert len(build_playlist(f'"{tmp_path}{os.sep}"')) == 1


def test_empty_folder(tmp_path):
    assert build_playlist(str(tmp_path)) == []


# ---------- song advancement ----------

def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def test_next_action_quit():
    assert next_action(pygame.event.Event(pygame.QUIT)) == QUIT
    assert next_action(key(pygame.K_q)) == QUIT
    assert next_action(key(pygame.K_ESCAPE)) == QUIT


def test_next_action_skip():
    assert next_action(key(pygame.K_n)) == NEXT
    assert next_action(key(pygame.K_RIGHT)) == NEXT


def test_next_action_song_ended():
    assert next_action(pygame.event.Event(SONG_END)) == ENDED


def test_next_action_ignores_other_events():
    assert next_action(key(pygame.K_a)) is None
    assert next_action(key(pygame.K_F2)) is None  # (Up used to be checked here; it scrolls the playlist since issue #36)
    assert next_action(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(0, 0))) is None


def fake_player(results):
    """Stand-in for play_song that returns preset results and records what it was asked to play."""
    calls = []

    def play(screen, songfile):
        calls.append(songfile)
        return results[songfile]
    return play, calls


def test_run_playlist_plays_all(monkeypatch):
    play, calls = fake_player({"a": ENDED, "b": ENDED, "c": ENDED})
    monkeypatch.setattr(musicolorizer, "play_song", play)
    assert run_playlist(None, ["a", "b", "c"]) == 3
    assert calls == ["a", "b", "c"]


def test_run_playlist_skip_moves_on(monkeypatch):
    play, calls = fake_player({"a": NEXT, "b": ENDED})
    monkeypatch.setattr(musicolorizer, "play_song", play)
    assert run_playlist(None, ["a", "b"]) == 2
    assert calls == ["a", "b"]


def test_run_playlist_quit_stops(monkeypatch):
    play, calls = fake_player({"a": ENDED, "b": QUIT, "c": ENDED})
    monkeypatch.setattr(musicolorizer, "play_song", play)
    assert run_playlist(None, ["a", "b", "c"]) == 2
    assert calls == ["a", "b"]


def test_run_playlist_skips_unplayable(monkeypatch):
    play, calls = fake_player({"bad": UNPLAYABLE, "good": ENDED})
    monkeypatch.setattr(musicolorizer, "play_song", play)
    assert run_playlist(None, ["bad", "good"]) == 1
    assert calls == ["bad", "good"]


def test_run_playlist_nothing_playable(monkeypatch):
    play, _ = fake_player({"x": UNPLAYABLE, "y": UNPLAYABLE})
    monkeypatch.setattr(musicolorizer, "play_song", play)
    assert run_playlist(None, ["x", "y"]) == 0


# ---------- loading and bad files ----------

def test_play_song_missing_file(tmp_path, capsys):
    missing = str(tmp_path / "gone.mp3")
    assert play_song(None, missing) == UNPLAYABLE
    assert "Can't find" in capsys.readouterr().out


def test_analyze_song_unreadable(tmp_path, capsys):
    bad = tmp_path / "broken.wav"
    bad.write_bytes(b"this is not audio")
    assert analyze_song(str(bad)) is False
    assert "Couldn't read" in capsys.readouterr().out


def test_analyze_song_tiny_wav(tmp_path):
    assert analyze_song(make_tiny_wav(tmp_path / "tiny.wav")) is True
    # get_decibel must stay in range even past the end of the song or at pos -1
    assert musicolorizer.get_decibel(0.0, 440) <= 0
    assert musicolorizer.get_decibel(999.0, 440) <= 0
    assert musicolorizer.get_decibel(-0.001, 440) <= 0


# ---------- full play_song, headless ----------

@pytest.fixture
def headless_screen(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    screen = pygame.display.set_mode([200, 150])
    pygame.mixer.music.set_endevent(SONG_END)
    yield screen
    pygame.quit()


def test_play_song_skip(tmp_path, headless_screen):
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_n))
    assert play_song(headless_screen, song) == NEXT


def test_play_song_quit(tmp_path, headless_screen):
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert play_song(headless_screen, song) == QUIT


def test_play_song_ignores_stale_end_event(tmp_path, headless_screen):
    # An end event left over from a previous song must not skip this one
    song = make_tiny_wav(tmp_path / "Love.wav", seconds=2)
    pygame.event.post(pygame.event.Event(SONG_END))
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q))
    assert play_song(headless_screen, song) == QUIT


def test_play_song_unreadable(tmp_path, headless_screen):
    bad = tmp_path / "broken.mp3"
    bad.write_bytes(b"not audio at all")
    assert play_song(headless_screen, str(bad)) == UNPLAYABLE

"""Tests for the song chooser, command-line launch, playlist panel, and pause/resume.

No test opens a real dialog or window: the chooser gets fake dialog functions,
and pygame runs with SDL's dummy video and audio drivers. Audio comes only from
tiny WAVs generated in a temp folder, never the committed audio files.
"""
import os

import pygame
import pytest

import musicolorizer
from musicolorizer import (
    ENDED, NEXT, PAUSE, QUIT, UNPLAYABLE,
    PlaybackState, choose_songs, control_layout, existing_songs,
    next_action, play_song, playlist_from_paths, run_playlist, visible_range,
)
from test_playlist import make_tiny_wav, touch


def fail_if_called():
    raise AssertionError("this dialog should not have opened")


# ---------- chooser selection -> playlist ----------

def test_chooser_several_files(tmp_path):
    a = touch(tmp_path / "b song.mp3")
    b = touch(tmp_path / "a song.wav")
    chosen = choose_songs(ask_files=lambda: (a, b), ask_folder=fail_if_called)
    # Files play in the order the dialog gave them
    assert playlist_from_paths(chosen) == [a, b]


def test_chooser_one_file(tmp_path):
    a = touch(tmp_path / "Hello, Goodbye.mp3")
    assert playlist_from_paths(choose_songs(lambda: (a,), fail_if_called)) == [a]


def test_chooser_cancel_files_then_folder(tmp_path):
    touch(tmp_path / "zebra.mp3")
    touch(tmp_path / "Apple.wav")
    touch(tmp_path / "notes.txt")
    chosen = choose_songs(ask_files=lambda: (), ask_folder=lambda: str(tmp_path))
    names = [os.path.basename(p) for p in playlist_from_paths(chosen)]
    assert names == ["Apple.wav", "zebra.mp3"]  # alphabetical, audio only


@pytest.mark.parametrize("cancelled", ["", (), None])
def test_chooser_cancel_both(cancelled):
    assert choose_songs(lambda: cancelled, lambda: cancelled) == []


def test_main_cancel_exits_without_window(monkeypatch, capsys):
    monkeypatch.setattr(musicolorizer, "choose_songs", lambda: [])
    monkeypatch.setattr(pygame, "init", fail_if_called)
    musicolorizer.main([])
    assert "nothing to play" in capsys.readouterr().out


def test_main_no_tkinter_falls_back_to_prompt(monkeypatch, capsys):
    def no_dialogs():
        raise ImportError("No module named 'tkinter'")
    monkeypatch.setattr(musicolorizer, "native_dialogs", no_dialogs)
    monkeypatch.setattr("builtins.input", lambda prompt: "")
    monkeypatch.setattr(pygame, "init", fail_if_called)
    musicolorizer.main([])
    out = capsys.readouterr().out
    assert "Couldn't open the song chooser" in out
    assert "nothing to play" in out


# ---------- command-line launch ----------

def test_main_args_skip_dialog(tmp_path, monkeypatch):
    a = touch(tmp_path / "a.mp3")
    b = touch(tmp_path / "b.mp3")
    monkeypatch.setattr(musicolorizer, "choose_songs", fail_if_called)
    played = []
    monkeypatch.setattr(musicolorizer, "run_playlist", lambda screen, songs: played.extend(songs) or len(songs))
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    musicolorizer.main([a, b])
    assert played == [a, b]


def test_cli_folder_and_files_mixed(tmp_path):
    folder = tmp_path / "album"
    folder.mkdir()
    touch(folder / "2.mp3")
    touch(folder / "1.mp3")
    single = touch(tmp_path / "single.wav")
    names = [os.path.basename(p) for p in playlist_from_paths([single, str(folder)])]
    assert names == ["single.wav", "1.mp3", "2.mp3"]


def test_main_args_all_missing(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(pygame, "init", fail_if_called)
    musicolorizer.main([str(tmp_path / "gone.mp3")])
    out = capsys.readouterr().out
    assert "Can't find" in out and "nothing to play" in out


def test_main_args_empty_folder(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(pygame, "init", fail_if_called)
    musicolorizer.main([str(tmp_path)])
    assert "No songs to play" in capsys.readouterr().out


def test_existing_songs_reports_missing(tmp_path, capsys):
    a = touch(tmp_path / "a.mp3")
    missing = str(tmp_path / "gone.mp3")
    assert existing_songs([missing, a]) == [a]
    assert "Can't find" in capsys.readouterr().out


# ---------- current-song tracking ----------

def test_run_playlist_tracks_current_song(monkeypatch):
    seen = []

    def fake_play(screen, songfile):
        state = musicolorizer.now_playing
        seen.append((state.index, state.current_song, sorted(state.unplayable)))
        return UNPLAYABLE if songfile == "/m/bad.mp3" else ENDED

    monkeypatch.setattr(musicolorizer, "play_song", fake_play)
    songs = ["/m/One.mp3", "/m/bad.mp3", "/m/Three.mp3"]
    assert run_playlist(None, songs) == 2
    assert seen == [(0, "/m/One.mp3", []), (1, "/m/bad.mp3", []), (2, "/m/Three.mp3", [1])]
    assert musicolorizer.now_playing is None  # cleared when the playlist finishes


def test_playback_state_titles_and_start():
    state = PlaybackState(["/m/Almost Blue.mp3", "/m/Sharp Edges.wav"])
    assert state.titles == ["Almost Blue", "Sharp Edges"]
    assert state.current_song == "/m/Almost Blue.mp3"
    state.toggle_pause()
    state.start(1)
    assert state.current_song == "/m/Sharp Edges.wav"
    assert state.paused is False  # every new song starts playing


def test_visible_range():
    assert visible_range(0, 3, 8) == (0, 3)           # short playlist: show all
    assert visible_range(0, 20, 8) == (0, 8)
    assert visible_range(5, 20, 8) == (3, 11)         # two earlier songs stay visible
    assert visible_range(19, 20, 8) == (12, 20)       # never runs past the end


# ---------- pause/resume state ----------

def test_toggle_pause():
    state = PlaybackState(["a.mp3"])
    assert state.paused is False
    assert state.toggle_pause() is True
    assert state.toggle_pause() is False


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def click(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)


def test_next_action_pause_key():
    assert next_action(key(pygame.K_p)) == PAUSE


def test_next_action_buttons():
    buttons = control_layout((400, 300))
    assert next_action(click(buttons[PAUSE].center), buttons) == PAUSE
    assert next_action(click(buttons[NEXT].center), buttons) == NEXT
    assert next_action(click(buttons[QUIT].center), buttons) == QUIT
    assert next_action(click((390, 290)), buttons) is None  # clicking the bars does nothing
    right_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=buttons[QUIT].center)
    assert next_action(right_click, buttons) is None


def test_buttons_fit_in_small_window():
    for size in [(200, 150), (720, 900), (1600, 1000)]:
        buttons = control_layout(size)
        assert all(rect.right <= size[0] and rect.width > 0 for rect in buttons.values())
        assert buttons[PAUSE].right < buttons[NEXT].left < buttons[QUIT].left


# ---------- full play_song, headless ----------

@pytest.fixture
def headless_screen(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    screen = pygame.display.set_mode([400, 300])
    pygame.mixer.music.set_endevent(musicolorizer.SONG_END)
    yield screen
    pygame.quit()


def scripted_frames(monkeypatch, frames):
    """Make pygame.event.get return one batch of events per frame, then nothing."""
    batches = iter(frames)
    monkeypatch.setattr(pygame.event, "get", lambda *args, **kwargs: next(batches, []))


def test_pause_holds_bars_and_resumes(tmp_path, headless_screen, monkeypatch):
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    mixer_calls = []
    monkeypatch.setattr(pygame.mixer.music, "pause", lambda: mixer_calls.append("pause"))
    monkeypatch.setattr(pygame.mixer.music, "unpause", lambda: mixer_calls.append("unpause"))
    updates = []
    real_update = musicolorizer.ColorBar.update
    monkeypatch.setattr(musicolorizer.ColorBar, "update", lambda self, db: updates.append(1) or real_update(self, db))

    # Frame 1 plays, frames 2-4 are paused, frame 5 resumes, frame 6 plays, frame 7 quits
    p = key(pygame.K_p)
    scripted_frames(monkeypatch, [[], [p], [], [], [p], [], [key(pygame.K_q)]])
    assert play_song(headless_screen, song) == QUIT

    bars_per_frame = len(updates) // 3
    assert bars_per_frame > 0
    assert len(updates) == 3 * bars_per_frame  # only the 3 unpaused frames moved the bars
    assert mixer_calls == ["pause", "unpause"]


def test_skip_button_click(tmp_path, headless_screen, monkeypatch):
    song = make_tiny_wav(tmp_path / "Love.wav", seconds=2)
    skip = control_layout(headless_screen.get_size())[NEXT]
    scripted_frames(monkeypatch, [[], [click(skip.center)]])
    assert play_song(headless_screen, song) == NEXT


def test_quit_button_click_while_paused(tmp_path, headless_screen, monkeypatch):
    song = make_tiny_wav(tmp_path / "Love.wav", seconds=2)
    buttons = control_layout(headless_screen.get_size())
    scripted_frames(monkeypatch, [[click(buttons[PAUSE].center)], [], [click(buttons[QUIT].center)]])
    assert play_song(headless_screen, song) == QUIT


def test_playlist_shows_current_song(tmp_path, headless_screen, monkeypatch):
    # Song 2 of 3 plays from run_playlist; the panel draws with index 1
    songs = [make_tiny_wav(tmp_path / f"{name}.wav", seconds=2) for name in ("One", "Two", "Three")]
    drawn = []
    real_draw = musicolorizer.draw_overlay
    monkeypatch.setattr(musicolorizer, "draw_overlay",
                        lambda screen, state, fonts, pos=(-1, -1): drawn.append((state.index, state.titles)) or real_draw(screen, state, fonts, pos))
    scripted_frames(monkeypatch, [[], [key(pygame.K_n)], [], [key(pygame.K_q)]])
    assert run_playlist(headless_screen, songs) == 2
    assert (0, ["One", "Two", "Three"]) in drawn
    assert (1, ["One", "Two", "Three"]) in drawn
    assert all(index in (0, 1) for index, _ in drawn)

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

@pytest.fixture(autouse=True)
def temp_last_folder(tmp_path, monkeypatch):
    """Keep the remembered-folder file in a temp folder, never the real home folder."""
    path = tmp_path / "last_folder"
    monkeypatch.setattr(musicolorizer, "LAST_FOLDER_FILE", str(path))
    return path


class FakeChooser:
    """Stands in for NativeChooser: returns preset answers and records where each dialog was opened."""

    def __init__(self, mode, files=(), folder=""):
        self.mode, self.files, self.folder = mode, files, folder
        self.opened = []
        self.closed = False

    def ask_mode(self):
        return self.mode

    def ask_files(self, start_dir):
        self.opened.append(("files", start_dir))
        return self.files

    def ask_folder(self, start_dir):
        self.opened.append(("folder", start_dir))
        return self.folder

    def close(self):
        self.closed = True


def use_chooser(monkeypatch, chooser):
    monkeypatch.setattr(musicolorizer, "native_dialogs", lambda: chooser)
    return chooser


def test_chooser_several_files(tmp_path):
    a = touch(tmp_path / "b song.mp3")
    b = touch(tmp_path / "a song.wav")
    fake = FakeChooser("songs", files=(a, b))
    chosen = choose_songs(fake.ask_mode, fake.ask_files, fake.ask_folder, str(tmp_path))
    # Files play in the order the dialog gave them
    assert playlist_from_paths(chosen) == [a, b]
    assert fake.opened == [("files", str(tmp_path))]


def test_chooser_one_file(tmp_path):
    a = touch(tmp_path / "Hello, Goodbye.mp3")
    fake = FakeChooser("songs", files=(a,))
    assert playlist_from_paths(choose_songs(fake.ask_mode, fake.ask_files, fake.ask_folder, "/")) == [a]


def test_chooser_folder(tmp_path):
    touch(tmp_path / "zebra.mp3")
    touch(tmp_path / "Apple.wav")
    touch(tmp_path / "notes.txt")
    fake = FakeChooser("folder", folder=str(tmp_path))
    chosen = choose_songs(fake.ask_mode, fake.ask_files, fake.ask_folder, "/start")
    names = [os.path.basename(p) for p in playlist_from_paths(chosen)]
    assert names == ["Apple.wav", "zebra.mp3"]  # alphabetical, audio only
    assert fake.opened == [("folder", "/start")]  # only the folder dialog opened


def test_chooser_cancel_at_choice_opens_nothing():
    fake = FakeChooser(None)
    assert choose_songs(fake.ask_mode, fake.ask_files, fake.ask_folder, "/") == []
    assert fake.opened == []


@pytest.mark.parametrize("mode", ["songs", "folder"])
@pytest.mark.parametrize("cancelled", ["", (), None])
def test_chooser_cancel_in_dialog_means_never_mind(mode, cancelled):
    # Cancel in a dialog just stops; it doesn't open the other dialog
    fake = FakeChooser(mode, files=cancelled, folder=cancelled)
    assert choose_songs(fake.ask_mode, fake.ask_files, fake.ask_folder, "/") == []
    assert len(fake.opened) == 1


# ---------- starting folder ----------

def test_start_folder_defaults_to_music_then_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    assert musicolorizer.start_folder() == str(home)
    (home / "Music").mkdir()
    assert musicolorizer.start_folder() == str(home / "Music")


def test_last_folder_round_trip(tmp_path):
    music = tmp_path / "Tryout"
    music.mkdir()
    assert musicolorizer.load_last_folder() is None
    musicolorizer.save_last_folder(str(music))
    assert musicolorizer.load_last_folder() == str(music)
    assert musicolorizer.start_folder() == str(music)


def test_last_folder_gone_is_ignored(tmp_path, temp_last_folder):
    temp_last_folder.write_text(str(tmp_path / "deleted folder"))
    assert musicolorizer.load_last_folder() is None


def test_folder_of_choice(tmp_path):
    nested = tmp_path / "Music" / "Albums" / "Blue"
    nested.mkdir(parents=True)
    song = touch(nested / "Almost Blue.mp3")
    assert musicolorizer.folder_of_choice([song]) == str(nested)
    assert musicolorizer.folder_of_choice([str(nested)]) == str(nested)
    assert musicolorizer.folder_of_choice([]) is None


def test_next_run_starts_where_songs_were_picked(tmp_path, monkeypatch):
    nested = tmp_path / "Music" / "tryout"
    nested.mkdir(parents=True)
    song = touch(nested / "Red Vines.mp3")

    # First run: pick a song from the nested folder
    first = use_chooser(monkeypatch, FakeChooser("songs", files=(song,)))
    assert musicolorizer.ask_for_songs() == [song]
    assert first.closed

    # Second run: the folder dialog opens right there, no re-navigating
    second = use_chooser(monkeypatch, FakeChooser("folder", folder=str(nested)))
    musicolorizer.ask_for_songs()
    assert second.opened == [("folder", str(nested))]

    # Third run: the files dialog opens there too
    third = use_chooser(monkeypatch, FakeChooser("songs", files=()))
    musicolorizer.ask_for_songs()
    assert third.opened == [("files", str(nested))]


def test_cancel_does_not_change_remembered_folder(tmp_path, monkeypatch):
    music = tmp_path / "Music"
    music.mkdir()
    musicolorizer.save_last_folder(str(music))
    fake = use_chooser(monkeypatch, FakeChooser(None))
    assert musicolorizer.ask_for_songs() == []
    assert fake.closed
    assert musicolorizer.load_last_folder() == str(music)


def test_main_cancel_exits_without_window(monkeypatch, capsys):
    use_chooser(monkeypatch, FakeChooser(None))
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


def test_mac_message_only_on_mac(monkeypatch):
    monkeypatch.setattr(musicolorizer.sys, "platform", "darwin")
    assert musicolorizer.mac_message("hi") == {"message": "hi"}
    monkeypatch.setattr(musicolorizer.sys, "platform", "linux")
    assert musicolorizer.mac_message("hi") == {}


# ---------- command-line launch ----------

def test_main_args_skip_dialog(tmp_path, monkeypatch):
    a = touch(tmp_path / "a.mp3")
    b = touch(tmp_path / "b.mp3")
    monkeypatch.setattr(musicolorizer, "native_dialogs", fail_if_called)
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


def test_corner_title_drawn_on_screen_every_frame_including_paused(tmp_path, headless_screen, monkeypatch):
    # The corner text (issue #14) goes on the screen after the bar layer and panel,
    # so it stays visible while paused instead of being frozen into the bar layer
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    monkeypatch.setattr(musicolorizer, "title_alpha", lambda t, mode=None: 1.0)
    order = []
    real_overlay, real_title = musicolorizer.draw_overlay, musicolorizer.draw_title
    monkeypatch.setattr(musicolorizer, "draw_overlay",
                        lambda screen, state, fonts, pos=(-1, -1): order.append(("panel", screen, state.paused)) or real_overlay(screen, state, fonts, pos))
    monkeypatch.setattr(musicolorizer, "draw_title",
                        lambda screen, image, alpha: order.append(("title", screen, None)) or real_title(screen, image, alpha))

    p = key(pygame.K_p)
    scripted_frames(monkeypatch, [[], [p], [], [key(pygame.K_q)]])
    assert play_song(headless_screen, song) == QUIT

    display = pygame.display.get_surface()
    assert [kind for kind, _, _ in order] == ["panel", "title"] * 3  # title after the panel, every frame
    assert all(surface is display for _, surface, _ in order)       # drawn on the screen, not the bar layer
    assert [paused for kind, _, paused in order if kind == "panel"] == [False, True, True]


# ---------- hiding and showing the playlist panel (issue #25) ----------

from musicolorizer import CHIP_LABEL, TOGGLE_PANEL, chip_layout, draw_overlay


def test_panel_starts_visible_and_toggles():
    state = PlaybackState(["a.mp3", "b.mp3"])
    assert state.panel_visible is True
    assert state.toggle_panel() is False
    assert state.panel_visible is False
    # Moving to the next song doesn't bring a hidden panel back
    state.start(1)
    assert state.panel_visible is False
    assert state.toggle_panel() is True
    # A fresh playlist always starts with the panel showing
    assert PlaybackState(["a.mp3"]).panel_visible is True


def test_next_action_h_key_toggles_panel():
    assert next_action(key(pygame.K_h)) == TOGGLE_PANEL


@pytest.fixture
def offscreen():
    """A plain Surface to draw on: fonts work, but no window is opened."""
    pygame.font.init()
    yield pygame.Surface((400, 300))
    pygame.font.quit()


def record_text(monkeypatch):
    drawn = []
    real = musicolorizer.draw_text
    monkeypatch.setattr(musicolorizer, "draw_text",
                        lambda screen, fonts, kind, text, *rest, **kw: drawn.append(text) or real(screen, fonts, kind, text, *rest, **kw))
    return drawn


def test_draw_overlay_hidden_draws_only_the_chip(offscreen, monkeypatch):
    state = PlaybackState(["One.mp3", "Two.mp3", "Three.mp3"])
    state.panel_visible = False
    drawn = record_text(monkeypatch)
    background = (12, 34, 56)
    offscreen.fill(background)

    clickable = draw_overlay(offscreen, state, musicolorizer.load_fonts())

    assert drawn == [CHIP_LABEL]  # no buttons, no header, no playlist rows
    assert clickable == {TOGGLE_PANEL: chip_layout(offscreen.get_size())}
    # Where the playlist rows would be (below the chip) is left untouched
    chip = clickable[TOGGLE_PANEL]
    for y in range(chip.bottom + 4, chip.bottom + 120, 10):
        assert offscreen.get_at((chip.left + 20, y))[:3] == background


def test_draw_overlay_visible_unchanged(offscreen, monkeypatch):
    state = PlaybackState(["One.mp3", "Two.mp3"])
    drawn = record_text(monkeypatch)
    clickable = draw_overlay(offscreen, state, musicolorizer.load_fonts())
    # Same buttons and rows as before the toggle existed, and no chip
    assert clickable == control_layout(offscreen.get_size())
    assert drawn == ["Prev (<)", "Pause (P)", "Skip (>)", "Quit (Q)", "Playlist: 1 of 2", "1. One", "2. Two"]


def test_chip_is_hit_testable(offscreen):
    state = PlaybackState(["a.mp3"])
    state.panel_visible = False
    clickable = draw_overlay(offscreen, state, None)  # works without fonts too
    chip = clickable[TOGGLE_PANEL]
    assert next_action(click(chip.center), clickable) == TOGGLE_PANEL
    assert next_action(click((390, 290)), clickable) is None
    # The hidden Pause/Skip/Quit buttons can't be clicked where they used to be
    hidden_buttons = control_layout(offscreen.get_size())
    assert next_action(click(hidden_buttons[QUIT].center), clickable) is None


def test_chip_fits_in_small_window():
    for size in [(120, 90), (200, 150), (1600, 1000)]:
        chip = chip_layout(size)
        assert chip.width > 0 and chip.right <= size[0]
        assert chip.topleft == (musicolorizer.PANEL_MARGIN, musicolorizer.PANEL_MARGIN)


def test_hide_with_h_keys_still_work_click_chip_to_show(tmp_path, headless_screen, monkeypatch):
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    monkeypatch.setattr(musicolorizer, "title_alpha", lambda t, mode=None: 1.0)
    mixer_calls = []
    monkeypatch.setattr(pygame.mixer.music, "pause", lambda: mixer_calls.append("pause"))
    monkeypatch.setattr(pygame.mixer.music, "unpause", lambda: mixer_calls.append("unpause"))
    frames = []
    real_overlay, real_title = musicolorizer.draw_overlay, musicolorizer.draw_title
    monkeypatch.setattr(musicolorizer, "draw_overlay",
                        lambda screen, state, fonts, pos=(-1, -1): frames.append([state.panel_visible, state.paused]) or real_overlay(screen, state, fonts, pos))
    monkeypatch.setattr(musicolorizer, "draw_title",
                        lambda screen, image, alpha: frames[-1].append("title") or real_title(screen, image, alpha))

    chip = chip_layout(headless_screen.get_size())
    p = key(pygame.K_p)
    # Frame 1 shows the panel, H hides it, P pauses and resumes while hidden, clicking the chip shows it, Q quits
    scripted_frames(monkeypatch, [[], [key(pygame.K_h)], [p], [p], [click(chip.center)], [key(pygame.K_q)]])
    assert play_song(headless_screen, song) == QUIT

    assert frames == [
        [True, False, "title"],
        [False, False, "title"],
        [False, True, "title"],   # pausing works with the panel hidden
        [False, False, "title"],
        [True, False, "title"],   # the chip brought the panel back
    ]
    assert mixer_calls == ["pause", "unpause"]


def test_hidden_panel_stays_hidden_across_songs_and_new_playlist_shows_it(tmp_path, headless_screen, monkeypatch):
    songs = [make_tiny_wav(tmp_path / f"{name}.wav", seconds=2) for name in ("One", "Two")]
    seen = []
    real_draw = musicolorizer.draw_overlay
    monkeypatch.setattr(musicolorizer, "draw_overlay",
                        lambda screen, state, fonts, pos=(-1, -1): seen.append((state.index, state.panel_visible)) or real_draw(screen, state, fonts, pos))
    # Hide on song 1, skip to song 2 (still hidden), quit
    scripted_frames(monkeypatch, [[key(pygame.K_h)], [key(pygame.K_n)], [], [key(pygame.K_q)]])
    assert run_playlist(headless_screen, songs) == 2
    assert seen == [(0, False), (1, False)]

    # Starting a new playlist starts with the panel showing again
    seen.clear()
    scripted_frames(monkeypatch, [[], [key(pygame.K_q)]])
    assert run_playlist(headless_screen, songs[:1]) == 1
    assert seen == [(0, True)]


# ---------- Previous track (issue #19) ----------

from musicolorizer import PREVIOUS, RESTART, previous_index, previous_or_restart


def test_next_action_left_arrow_is_previous():
    assert next_action(key(pygame.K_LEFT)) == PREVIOUS
    assert next_action(key(pygame.K_RIGHT)) == NEXT  # Right still skips


def test_four_buttons_same_width_and_fit_the_panel():
    for size in [(200, 150), (400, 300), (720, 900), (1600, 1000)]:
        buttons = control_layout(size)
        assert list(buttons) == [PREVIOUS, PAUSE, NEXT, QUIT]
        widths = {rect.width for rect in buttons.values()}
        assert len(widths) == 1 and widths.pop() > 0
        # Inside the panel, which still caps at 380px wide
        panel_right = musicolorizer.PANEL_MARGIN + musicolorizer.panel_width(size)
        assert buttons[QUIT].right <= panel_right - musicolorizer.PANEL_PADDING
        assert buttons[PREVIOUS].right < buttons[PAUSE].left
    assert musicolorizer.panel_width((1600, 1000)) == 380


def test_button_labels_fit_at_full_width():
    pygame.font.init()
    try:
        fonts = musicolorizer.load_fonts()
        buttons = control_layout((1600, 1000))
        for label in ("Prev (<)", "Pause (P)", "Resume (P)", "Skip (>)", "Quit (Q)"):
            assert fonts["control"].size(label)[0] <= buttons[PAUSE].width - 8  # no "..." at full size
    finally:
        pygame.font.quit()


def test_previous_button_click():
    buttons = control_layout((400, 300))
    assert next_action(click(buttons[PREVIOUS].center), buttons) == PREVIOUS


def test_previous_index():
    assert previous_index(2, set()) == 1
    assert previous_index(0, set()) == 0        # first song: restart it
    assert previous_index(3, {1, 2}) == 0       # skip songs that couldn't play
    assert previous_index(2, {0, 1}) == 2       # nothing playable before: restart


def scripted_player(monkeypatch, results):
    """Stand-in for play_song: returns the next preset result each time, and records which index was playing."""
    played = []
    queue = iter(results)

    def fake_play(screen, songfile):
        state = musicolorizer.now_playing
        played.append(state.index)
        assert state.current_song == songfile and state.paused is False
        return next(queue)

    monkeypatch.setattr(musicolorizer, "play_song", fake_play)
    return played


def test_previous_steps_back_one(monkeypatch):
    played = scripted_player(monkeypatch, [ENDED, NEXT, PREVIOUS, ENDED, ENDED])
    assert run_playlist(None, ["/m/A.mp3", "/m/B.mp3", "/m/C.mp3"]) == 5
    assert played == [0, 1, 2, 1, 2]


def test_previous_on_first_song_restarts_it(monkeypatch):
    played = scripted_player(monkeypatch, [PREVIOUS, PREVIOUS, ENDED, QUIT])
    assert run_playlist(None, ["/m/A.mp3", "/m/B.mp3"]) == 4
    assert played == [0, 0, 0, 1]


def test_previous_skips_back_over_unplayable(monkeypatch):
    played = scripted_player(monkeypatch, [ENDED, UNPLAYABLE, PREVIOUS, ENDED, ENDED])
    assert run_playlist(None, ["/m/A.mp3", "/m/bad.mp3", "/m/C.mp3"]) == 4
    assert played == [0, 1, 2, 0, 2]  # back from C lands on A; going forward again doesn't retry the bad song


def test_previous_while_paused_returns_previous_and_unpauses(tmp_path, headless_screen, monkeypatch):
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    stops = []
    real_stop = pygame.mixer.music.stop
    monkeypatch.setattr(pygame.mixer.music, "stop", lambda: stops.append(1) or real_stop())
    buttons = control_layout(headless_screen.get_size())
    scripted_frames(monkeypatch, [[key(pygame.K_p)], [click(buttons[PREVIOUS].center)]])
    assert play_song(headless_screen, song) == PREVIOUS
    assert stops  # the paused song was stopped, like Skip


def test_previous_in_real_playlist_while_paused(tmp_path, headless_screen, monkeypatch):
    songs = [make_tiny_wav(tmp_path / f"{name}.wav", seconds=2) for name in ("One", "Two")]
    seen = []
    real_draw = musicolorizer.draw_overlay
    monkeypatch.setattr(musicolorizer, "draw_overlay",
                        lambda screen, state, fonts, pos=(-1, -1): seen.append((state.index, state.paused)) or real_draw(screen, state, fonts, pos))
    # Song 1, skip; song 2, pause, then Left while paused goes back to song 1 playing; quit
    scripted_frames(monkeypatch, [[], [key(pygame.K_n)], [key(pygame.K_p)], [key(pygame.K_LEFT)], [], [key(pygame.K_q)]])
    assert run_playlist(headless_screen, songs) == 3
    assert seen == [(0, False), (1, True), (0, False)]


# ---------- Previous restarts the song after a few seconds; < and > keys ----------

def test_less_and_greater_keys():
    assert next_action(key(pygame.K_COMMA)) == PREVIOUS
    assert next_action(key(pygame.K_PERIOD)) == NEXT
    assert next_action(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_COMMA, unicode="<")) == PREVIOUS
    assert next_action(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_PERIOD, unicode=">")) == NEXT
    assert next_action(key(pygame.K_n)) == NEXT  # N still skips


def test_previous_or_restart():
    assert previous_or_restart(0.0) == PREVIOUS
    assert previous_or_restart(musicolorizer.PREVIOUS_RESTART_SECONDS) == PREVIOUS
    assert previous_or_restart(musicolorizer.PREVIOUS_RESTART_SECONDS + 0.1) == RESTART
    assert previous_or_restart(95.0) == RESTART


def test_restart_replays_same_song(monkeypatch):
    played = scripted_player(monkeypatch, [ENDED, RESTART, ENDED, ENDED])
    assert run_playlist(None, ["/m/A.mp3", "/m/B.mp3", "/m/C.mp3"]) == 4
    assert played == [0, 1, 1, 2]


@pytest.mark.parametrize("ms, expected", [(1500, PREVIOUS), (12000, RESTART)])
def test_play_song_previous_depends_on_position(tmp_path, headless_screen, monkeypatch, ms, expected):
    song = make_tiny_wav(tmp_path / "Happy.wav", seconds=2)
    monkeypatch.setattr(pygame.mixer.music, "get_pos", lambda: ms)
    scripted_frames(monkeypatch, [[], [key(pygame.K_LEFT)]])
    assert play_song(headless_screen, song) == expected


def test_restart_while_paused_plays_again(tmp_path, headless_screen, monkeypatch):
    songs = [make_tiny_wav(tmp_path / f"{name}.wav", seconds=2) for name in ("One", "Two")]
    monkeypatch.setattr(pygame.mixer.music, "get_pos", lambda: 10000)  # well into the song
    seen = []
    real_draw = musicolorizer.draw_overlay
    monkeypatch.setattr(musicolorizer, "draw_overlay",
                        lambda screen, state, fonts, pos=(-1, -1): seen.append((state.index, state.paused)) or real_draw(screen, state, fonts, pos))
    scripted_frames(monkeypatch, [[key(pygame.K_p)], [key(pygame.K_COMMA)], [], [key(pygame.K_q)]])
    assert run_playlist(headless_screen, songs) == 2
    assert seen == [(0, True), (0, False)]  # same song, started over and playing

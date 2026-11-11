import pytest
from musicolorizer import get_colorway
from musicolorizer import random_color
from musicolorizer import limitation
from musicolorizer import get_title_from_path
from musicolorizer import pick_color_for_bar
from colormap import colormap

def test_get_title_from_path():
    assert get_title_from_path("/Users/litlnemo/Music/Almost Blue.mp3") == "Almost Blue"
    assert get_title_from_path("/some/path/Happy Days.wav") == "Happy Days"

def test_new_colormap_keywords():
    assert get_colorway("Gold Dust", colormap) == [[(50, 40, 0), (255, 215, 0)]]
    assert get_colorway("Electric Feel", colormap) == [[(0, 5, 30), (80, 240, 255)]]
    assert get_colorway("Night Moves", colormap) == [[(5, 5, 20), (40, 20, 80)]]
    assert get_colorway("Ghost Town", colormap) == [[(10, 20, 20), (200, 220, 215)]]

def test_pick_color_for_bar():
    colorways = [[(0, 0, 50), (0, 0, 255)], [(10, 0, 0), (255, 105, 180)]]
    result = pick_color_for_bar(colorways)
    assert result in colorways


def main():
    test_get_title_from_path()
    test_get_colorway()
    test_random_color()
    test_limitation()


def test_get_colorway():
    # Single keyword match - returns a list containing one colorway
    assert get_colorway("Happy Days", colormap) == [[(10, 10, 0), (255, 255, 0)]]
    assert get_colorway("happy days", colormap) == [[(10, 10, 0), (255, 255, 0)]]
    assert get_colorway("Almost Blue", colormap) == [[(0, 0, 50), (0, 0, 255)]]
    # Multiple keyword match - returns a list containing multiple colorways
    assert get_colorway("Blue Love Song", colormap) == [[(0, 0, 50), (0, 0, 255)], [(10, 0, 0), (255, 105, 180)]]
    # No match - returns a list with one random colorway (just check structure)
    result = get_colorway("Something Else", colormap)
    assert len(result) == 1
    assert len(result[0]) == 2

def test_random_color():
    with pytest.raises(Exception):
        random_color(["test"])

def test_limitation(): #min_value, max_value, value
    assert limitation(40, 100, 30) == 40
    assert limitation(100, 1000, 1200) == 1000
    assert limitation(100, 500, 250) == 250

if __name__ == "__main__":
    main()


# The thirty keywords added for issue #4, exactly as given in the brief
NEW_COLORWAYS_ISSUE_4 = {
    'shine':    [(50, 30, 0),  (255, 215, 60)],
    'bright':   [(25, 25, 30), (255, 255, 245)],
    'glow':     [(50, 10, 0),  (255, 170, 60)],
    'wine':     [(25, 0, 10),  (160, 20, 50)],
    'earth':    [(30, 18, 8),  (190, 130, 80)],
    'wedding':  [(45, 40, 50), (250, 245, 235)],
    'marry':    [(50, 10, 25), (255, 180, 200)],
    'twilight': [(10, 5, 35),  (190, 130, 220)],
    'light':    [(20, 25, 35), (245, 245, 255)],
    'sunset':   [(45, 10, 20), (255, 110, 80)],
    'sunrise':  [(25, 10, 30), (255, 190, 130)],
    'dusk':     [(15, 15, 30), (150, 130, 160)],
    'retro':    [(15, 0, 25),  (255, 0, 160)],
    'moon':     [(5, 5, 25),   (220, 225, 255)],
    'desert':   [(55, 35, 10), (240, 200, 120)],
    'summer':   [(60, 25, 0),  (255, 180, 40)],
    'autumn':   [(45, 15, 0),  (220, 100, 20)],
    'star':     [(10, 10, 20), (255, 245, 180)],
    'neon':     [(5, 0, 10),   (255, 0, 180)],
    'crimson':  [(40, 0, 5),   (220, 20, 60)],
    'lavender': [(35, 25, 55), (210, 180, 250)],
    'dance':    [(20, 0, 30),  (255, 80, 200)],
    'ember':    [(25, 5, 0),   (255, 120, 20)],
    'coral':    [(60, 15, 10), (255, 130, 110)],
    'mint':     [(10, 30, 25), (170, 255, 210)],
    'peach':    [(60, 25, 10), (255, 200, 160)],
    'velvet':   [(15, 0, 20),  (180, 30, 90)],
    'cherry':   [(40, 0, 10),  (230, 30, 70)],
    'disco':    [(10, 0, 25),  (255, 60, 220)],
    'aurora':   [(0, 20, 25),  (120, 255, 190)],
}


def test_issue_4_colorways_are_in_the_colormap():
    assert len(NEW_COLORWAYS_ISSUE_4) == 30
    for keyword, colors in NEW_COLORWAYS_ISSUE_4.items():
        assert colormap[keyword] == colors


def test_each_issue_4_keyword_returns_its_colorway():
    for keyword, colors in NEW_COLORWAYS_ISSUE_4.items():
        # Matching is case-insensitive and finds the keyword inside a longer title
        matched = get_colorway(f"The {keyword.title()} Song", colormap)
        assert colors in matched, keyword


def test_issue_4_keywords_on_their_own():
    # Keywords that contain no other keyword match just their own entry
    for keyword in ('wine', 'earth', 'retro', 'moon', 'neon', 'mint', 'disco', 'aurora', 'velvet', 'cherry'):
        assert get_colorway(keyword.upper(), colormap) == [NEW_COLORWAYS_ISSUE_4[keyword]]
    # Overlapping keywords all count and blend, as before (substring matching is unchanged)
    assert get_colorway("Sunset", colormap) == [colormap['sun'], colormap['sunset']]
    assert get_colorway("Twilight", colormap) == [colormap['twilight'], colormap['light']]


def test_existing_colorways_unchanged():
    assert colormap['sun'] == [(60, 30, 0), (255, 230, 50)]
    assert colormap['night'] == [(5, 5, 20), (40, 20, 80)]
    assert len(colormap) == 48 + 30  # the 48 earlier keywords plus the 30 new ones

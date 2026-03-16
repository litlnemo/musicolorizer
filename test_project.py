import pytest
from project import get_colorway
from project import random_color
from project import limitation
from project import get_title_from_path

def test_get_title_from_path():
    assert get_title_from_path("/Users/litlnemo/Music/Almost Blue.mp3") == "Almost Blue"
    assert get_title_from_path("/some/path/Happy Days.wav") == "Happy Days"

colormap = {
    'blue': [(0, 0, 50), (0, 0, 255)],  # Blues
    'sad': [(0, 0, 0), (0, 0, 255)],
    'winter': [(0, 0, 0), (0, 0, 255)],
    'happy': [(10, 10, 0), (255, 255, 0)],  # Yellows
    'love': [(10, 0, 0), (255, 105, 180)],  # Pinks
    'red': [(0, 0, 0), (255, 0, 0)],  # Reds
    'green': [(0, 10, 0), (0, 255, 0)],  # Lime Green
    'spring': [(10, 10, 0), (100, 255, 0)],
    'daydreams': [(0, 0, 0), (200, 80, 255)],  # Magenta
}

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

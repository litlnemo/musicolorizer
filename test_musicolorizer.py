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

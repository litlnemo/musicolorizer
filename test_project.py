import pytest
from project import get_colorway
from project import random_color
from project import limitation

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
    test_get_colorway()
    test_random_color()
    test_limitation()


def test_get_colorway():
    assert get_colorway("happydays.wav", colormap) == [(10, 10, 0), (255, 255, 0)]
    assert get_colorway("HappyDays.wav", colormap) == [(10, 10, 0), (255, 255, 0)]
    assert get_colorway("almostBLUE.mp3", colormap) == [(0, 0, 50), (0, 0, 255)]

def test_random_color():
    with pytest.raises(Exception):
        random_color(["test"])

def test_limitation(): #min_value, max_value, value
    assert limitation(40, 100, 30) == 40
    assert limitation(100, 1000, 1200) == 1000
    assert limitation(100, 500, 250) == 250

if __name__ == "__main__":
    main()

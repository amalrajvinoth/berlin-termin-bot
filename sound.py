# sound.py
import logging
import time

from AppKit import NSSound
from Foundation import NSURL


# stolen from https://github.com/JaDogg/pydoro/blob/develop/pydoro/pydoro_core/sound.py
def play_sound_osx(sound, block=True):
    """
    Utilizes AppKit.NSSound. Tested and known to work with MP3 and WAVE on
    OS X 10.11 with Python 2.7. Probably works with anything QuickTime supports.
    Probably works on OS X 10.5 and newer. Probably works with all versions of
    Python.
    Inspired by (but not copied from) Aaron's Stack Overflow answer here:
    http://stackoverflow.com/a/34568298/901641
    I never would have tried using AppKit.NSSound without seeing his code.
    """

    logging.info("Play sound")
    if "://" not in sound:
        if not sound.startswith("/"):
            from os import getcwd

            sound = getcwd() + "/" + sound
        sound = "file://" + sound
    url = NSURL.URLWithString_(sound)
    ns_sound = NSSound.alloc().initWithContentsOfURL_byReference_(url, True)
    if not ns_sound:
        raise IOError("Unable to load sound named: " + sound)
    ns_sound.play()

    if block:
        time.sleep(ns_sound.duration())


class Sound:
    def __init__(self, name, dog):
        self.name = name
        self.dog = dog
        _play_sound_osx(self.name)

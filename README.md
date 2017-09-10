Note: I am not going to make any changes to this unless I suddenly gain interest
in this game again.  Anyone is free to fork this and do whatever they want
under the terms of the MIT license.

# osr stuff

[![Kokou no Sousei](http://img.youtube.com/vi/jCK9dTT6hEA/0.jpg)](https://www.youtube.com/watch?v=jCK9dTT6hEA "Kokou no Sousei")

This is a few things I was messing around with the osu! replay format and
pygame. There's also a sort of library in `osr.py` for reading the maps.

I made this with `Python 3.5` and `pygame 1.9.2b1` on Windows, and I haven't
tested it elsewhere yet. But it might work.

## multi_render.py
This will read a bunch of replays at the same time and show them at the same
time.

To run it, you need a folder with an mp3 in it and some replays.
Then run it like `python multi_render.py ooi` where ooi is the folder containing
the mp3 and replays. Note that the mp3 must be 44.1 kHz otherwise the song will
play really slowly. I don't know why this happens, and I don't know why some of
the mp3s that osu! downloads are 48 kHz but it's not that hard to resample them.
I used Audacity for this.

### hotkeys
- `left click`: increase circle radius
- `right click`: decrease circle radius
- `scroll up`: increase trail duration
- `scroll down`: decrease trail duration
- `escape`, `ctrl+c`: quit

## multi_image.py

This script will write images to a file for each 60 fps frame of all of
the maps. You can then mux/encode these together with `ffmpeg` to make a video
you can actually upload to YouTube or whatever. [This][script] is what I used
to upload a bunch of the videos on [my YouTube channel][youtube] automatically.

[example]: https://www.youtube.com/watch?v=fkeoHRaMPbU
[youtube]: https://www.youtube.com/user/go4it7arh
[script]: https://gist.github.com/andrew12/1b68bc74385d45cd92517d200c0bf9c9

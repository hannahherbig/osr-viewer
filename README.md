# osr stuff

This is a few things I was messing around with the osu! replay format and
pygame. This will probably become an actual library eventually.

I made this with Python 3.5 and pygame 1.9.2b1 on Windows, and I haven't tested
it elsewhere yet. But it might work.

## multi_render.py
This will read a bunch of replays at the same time and show them at the same time.
[This is what it looks like](https://www.youtube.com/watch?v=-T6Caicfpwc)

To run it, you need a folder with an mp3 in it and some replays.
Then run it like `python multi_render.py ooi` where ooi is the folder containing
the mp3 and replays. Note that the mp3 must be 44.1 kHz otherwise the song will play really slowly. I don't know why this happens, and I don't know why some of the mp3s that osu! downloads are 48 kHz but it's not that hard to resample them.

### hotkeys
- `left click`: increase circle radius
- `right click`: decrease circle radius
- `scroll up`: increase trail duration
- `scroll down`: decrease trail duration
- `escape`, `ctrl+c`: quit

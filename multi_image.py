import struct
import lzma
import time
import sys
import glob
import os.path
import PIL.Image
import PIL.ImageDraw
import random
import argparse
from collections import deque
import math
import osr

BLACK = (  0,   0,   0)
GRAY  = (100, 100, 100)
WHITE = (255, 255, 255)

def pick_color():
    return tuple(random.randrange(64, 256) for i in range(3))

parser = argparse.ArgumentParser(description='osu! replay visualizer')
parser.add_argument('path', help='folder containing replays and mp3')
parser.add_argument('-t', '--tail', help='tail length', type=int, default=100)
parser.add_argument('-r', '--radius', help='circle radius', type=int, default=5)
parser.add_argument('-n', '--no-wipe', help="don't wipe the screen each frame", dest='wipe', action='store_false')
args = parser.parse_args()

pathname = args.path
tail = args.tail
radius = args.radius
wipe = args.wipe

basename = os.path.basename(pathname)

files = glob.glob(os.path.join(pathname, '*.osr'))
if len(files) == 0:
    sys.exit('no replays to read')

replays = []

for name in files:
    replay = osr.read_file(name)
    replay.color = WHITE if len(files) == 1 else pick_color()
    replays.append(replay)

replays.sort()

n = len(replays)
for r in replays:
    print('%2d. %15s - %d' % (n, r.player, r.score))
    n -= 1
print('read %d replays' % len(replays))

HEIGHT = 768
WIDTH = 1366
KEYSIZE = min((WIDTH-1024)/5, HEIGHT / (len(replays)))

interval = 1000/60
frame = 0
last_pos = 0
done = False
clock = deque(maxlen=100)

frames = math.ceil(max(len(r) for r in replays)/interval)

print('%d frames total = %.1f seconds' % (frames, frames/60))

for frame in range(frames):
    clock.append(time.clock())
    current_pos = int(frame*interval)
    im = PIL.Image.new('RGB', (WIDTH, HEIGHT))
    draw = PIL.ImageDraw.Draw(im)

    if tail:
        for replay in replays:
            hr = replay.has_mod(16)

            if tail:
                pointlist = []
            last_point = None

            for pos in range(max(current_pos-tail, 0), current_pos):
                p = replay[pos]
                x, y = p.x, p.y

                if hr:
                    y = 384 - y

                point = (x*2, y*2)

                if last_point != point:
                    if tail:
                        pointlist.append(point)
                    last_point = point

            if tail and len(pointlist) > 1:
                draw.line(pointlist, replay.color, 2)

    if radius:
        for replay in replays:
            p = replay[current_pos]
            x, y = p.x, p.y
            if replay.has_mod(16):
                y = 384 - y
            x *= 2
            y *= 2

            draw.ellipse((x-radius, y-radius, x+radius, y+radius), replay.color, BLACK)

    for i, replay in enumerate(replays):
        p = replay[current_pos]
        y = i*KEYSIZE
        for j, o in enumerate(p.buttons):
            x = WIDTH-KEYSIZE*5+j*KEYSIZE
            rect = (x, y, x+KEYSIZE, y+KEYSIZE)
            color = replay.color if o else BLACK
            draw.rectangle(rect, color)

    del draw

    last_pos = current_pos

    im.save(os.path.join('out', '%s-%05d.png' % (basename, frame)))

    if frame % 10 == 0:
        d = clock[-1]-clock[0]
        if d:
            fps = len(clock)/d
            sys.stderr.write('%5d - %5.0f fps - %.4f\r' % (frame, fps, frame / frames))

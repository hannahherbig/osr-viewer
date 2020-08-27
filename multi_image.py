import argparse
import glob
import math
import os.path
import random
import sys
import time
from collections import deque

import PIL.Image
import PIL.ImageDraw
from recordclass import recordclass

import osr

BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
WHITE = (255, 255, 255)


def pick_color():
    return tuple(random.randrange(64, 256) for i in range(3))


parser = argparse.ArgumentParser(description="osu! replay visualizer")
parser.add_argument("path", help="folder containing replays and mp3")
parser.add_argument("-t", "--tail", help="tail length", type=int, default=100)
parser.add_argument("-r", "--radius", help="circle radius", type=int, default=5)
parser.add_argument(
    "-w",
    "--no-wipe",
    help="don't wipe the screen each frame",
    dest="wipe",
    action="store_false",
)
parser.add_argument(
    "-f", "--no-flip", help="don't flip hr plays", dest="flip", action="store_false"
)
args = parser.parse_args()

pathname = args.path
tail = args.tail
radius = args.radius
wipe = args.wipe
flip = args.flip

basename = os.path.basename(pathname)

files = glob.glob(os.path.join(pathname, "*.osr"))
if len(files) == 0:
    sys.exit("no replays to read")

replays = []

for name in files:
    replay = osr.read_file(name, flip)
    replays.append(replay)

replays.sort()

n = len(replays)
for r in replays:
    print("%2d. %15s - %d" % (n, r.player, r.score))
    n -= 1
print("read %d replays" % len(replays))

State = recordclass("State", "replay color x y z trail")
states = []

for replay in replays:
    # we don't need anything else on the replay object so remove the references
    replay = replay.replay
    color = WHITE if len(replays) == 1 else pick_color()
    states.append(State(replay, color, 0, 0, 0, deque()))

del replays

HEIGHT = 768
WIDTH = 1366
KEYSIZE = min((WIDTH - 1024) / 5, HEIGHT / len(states))


def scale(x, y):
    return x * 2, y * 2


interval = 1000 / 60
frame = 0
last_pos = 0
done = False
clock = deque(maxlen=100)

msec = 0

for state in states:
    for p in state.replay:
        if p.t > msec:
            msec = p.t

frames = math.ceil(msec / interval)

mins, secs = divmod(frames / 60, 60)
print("%d frames total -> %dm%02ds" % (frames, mins, secs))

im = PIL.Image.new("RGB", (WIDTH, HEIGHT))

for frame in range(frames):
    clock.append(time.monotonic())
    pos = int(frame * interval)
    if not wipe:
        im = PIL.Image.new("RGB", (WIDTH, HEIGHT))
    draw = PIL.ImageDraw.Draw(im)

    lines = []
    circles = []
    rects = []

    for i, state in enumerate(states):
        r = state.replay
        trail = state.trail
        color = state.color
        while r and r[0].t <= pos:
            p = r.popleft()
            state.x, state.y, state.z = p.x, p.y, p.z
            circles.append((scale(state.x, state.y), color))
            trail.append(p)
        o = (scale(state.x, state.y), color)
        if o not in circles:
            circles.append(o)
        while trail and (pos - trail[0].t) > tail:
            trail.popleft()
        if len(trail) > 1:
            points = [scale(p.x, p.y) for p in trail]
            lines.append((points, color))
        y = i * KEYSIZE
        for j, o in enumerate(osr.keys(state.z)):
            x = WIDTH - KEYSIZE * 5 + j * KEYSIZE
            rects.append(((x, y, x + KEYSIZE, y + KEYSIZE), color if o else BLACK))

    if tail:
        for points, color in lines:
            draw.line(points, color, 2)

    if radius:
        for (x, y), color in circles:
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), color, BLACK)

    for rect, color in rects:
        draw.rectangle(rect, color)

    del draw

    im.save(os.path.join("out", "%s-%05d.tga" % (basename, frame)))

    if frame % 10 == 0:
        d = clock[-1] - clock[0]
        if d:
            fps = len(clock) / d
            sys.stderr.write("%5d - %5.0f fps - %.4f\r" % (frame, fps, frame / frames))

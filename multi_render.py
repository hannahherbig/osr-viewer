import pygame
import pygame.gfxdraw
from recordclass import recordclass
import time
import sys
from glob import glob
from os.path import join
from collections import deque
import random
import argparse
import osr

BLACK = (  0,   0,   0)
GRAY  = (100, 100, 100)
WHITE = (255, 255, 255)

def pick_color():
    return tuple(random.randrange(64, 256) for i in range(3))

def quit():
    print('\n')
    pygame.quit()
    sys.exit(42)

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

files = glob(join(pathname, '**/*.osr'), recursive=True)
if len(files) == 0:
    sys.exit('no replays to read')

replays = []

for name in files:
    replay = osr.read_file(name, True)
    replays.append(replay)

replays.sort()

n = len(replays)
for r in replays:
    print('%2d. %15s - %d' % (n, r.player, r.score))
    n -= 1
print('read %d replays' % len(replays))

state = recordclass('state', 'replay color x y z trail')
states = []

for replay in replays:
    # we don't need anything else on the replay object so remove the references
    replay = replay.replay
    color = WHITE if len(replays) == 1 else pick_color()
    states.append(state(replay, color, 0, 0, 0, deque()))

del replays

HEIGHT = 768
WIDTH = 1366
KEYSIZE = min((WIDTH-1024)/5, HEIGHT / len(states))

# Only works with Height of 768 and Width of 1366 if you want different size you will have to work out yourself
# This Change Centers the play on the window just like in Osu client
# Helps with easy overlay for video
X_CHANGE = 273
Y_CHANGE = 89
SCALE = 1.551

def scale(x, y):
    return (x + X_CHANGE / SCALE) * SCALE, (y + Y_CHANGE / SCALE) * SCALE

pygame.mixer.pre_init(44100)
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('radius=%d tail=%d' % (radius, tail))
pygame.mixer.music.load(*glob(join(pathname, '*.mp3')))
pygame.mixer.music.play()
pygame.mixer.music.set_volume(0.5)
clock = pygame.time.Clock()

UPDATE_FPS = pygame.USEREVENT
pygame.time.set_timer(UPDATE_FPS, 100)

last_pos = 0

screen.fill(BLACK)

while pygame.mixer.music.get_busy():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                quit()
            elif event.mod & pygame.KMOD_CTRL and event.key == pygame.K_c:
                quit()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # left mouse button
                radius += 1
            elif event.button == 3: # right mouse button
                radius = max(0, radius - 1)
            elif event.button == 4: # scroll up
                tail += 10
            elif event.button == 5: # scroll down
                tail = max(0, tail - 10)
            if event.button == 2: # middle mouse button
                wipe = not wipe
            pygame.display.set_caption('radius=%d tail=%d' % (radius, tail))

        elif event.type == UPDATE_FPS:
            sys.stderr.write('%5.0f fps\r' % clock.get_fps())

    clock.tick()
    pos = pygame.mixer.music.get_pos()
    if wipe:
        screen.fill(BLACK)

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
        else:
            circles.append((scale(state.x, state.y), color))
        while trail and (pos - trail[0].t) > tail:
            trail.popleft()
        points = [scale(p.x, p.y) for p in trail]
        if len(points) > 1:
            lines.append((points, color))
        y = i * KEYSIZE
        for j, o in enumerate(osr.keys(state.z)):
            x = WIDTH - KEYSIZE * 5 + j * KEYSIZE
            rects.append(((x, y, KEYSIZE, KEYSIZE), color if o else BLACK))

    if tail:
        for points, color in lines:
            pygame.draw.lines(screen, color, False, points)

    if radius:
        for (x, y), color in circles:
            x, y = int(x), int(y)
            pygame.gfxdraw.filled_circle(screen, x, y, radius, color)
            pygame.gfxdraw.aacircle(screen, x, y, radius, BLACK)

    for rect, color in rects:
        pygame.draw.rect(screen, color, rect)

    pygame.display.flip()

pygame.quit()

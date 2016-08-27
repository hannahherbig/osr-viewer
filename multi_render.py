import struct
import lzma
import time
import sys
from glob import glob
from os.path import join
import pygame
import pygame.gfxdraw
import random
from statistics import mean
import argparse

BLACK = (  0,   0,   0)
GRAY  = (100, 100, 100)
WHITE = (255, 255, 255)

def parse_uleb128(f):
    result = 0
    shift = 0
    while True:
        byte = struct.unpack('<B', f.read(1))[0]
        result |= ((byte & 0x7f) << shift)
        if (byte & 0x80) == 0:
            break
        shift += 7

    return result

def parse_string(f):
    head = struct.unpack('<B', f.read(1))[0]
    if head == 0x00:
        return ''
    elif head == 0x0b:
        length = parse_uleb128(f)
        return f.read(length).decode()

def parse(path):
    with open(path, 'rb') as f:
        mode, version = struct.unpack('<BI', f.read(5))
        beatmap_md5 = parse_string(f)
        player_name = parse_string(f)
        replay_md5 = parse_string(f)
        n300, n100, n50, ngeki, nkatu, nmiss, score, combo, perfect, mods = \
            struct.unpack('<HHHHHHIH?I', f.read(23))
        life_bar = parse_string(f) # ms|life
        timestamp, length = struct.unpack('<QI', f.read(12))

        hardrock = mods & 16 == 16

        data = lzma.decompress(f.read(length)).decode()
        out = []
        last_w = 0
        t = 0
        last_t = 0
        was_keyed = False
        for record in data.split(','):
            if record:
                w, x, y, z = record.split('|')
                w = int(w)
                t += w
                if t > last_t:
                    x, y = float(x), float(y)
                    z = int(z)
                    keyed = z & 3
                    start_key = keyed and was_keyed != keyed
                    if hardrock:
                        y = 384 - y
                    out[last_t:t] = [(int(x), int(y))] * w
                    was_keyed = keyed
                last_t = t
        return player_name, score, out

def pick_color():
    x = [random.randrange(64, 256) for i in range(3)]
    return tuple(x)

def quit():
    pygame.quit()
    sys.exit()

parser = argparse.ArgumentParser(description='osu! replay visualizer')
parser.add_argument('path', help='folder containing replays and mp3')
parser.add_argument('-t', '--tail', help='tail length', type=int, default=100)
parser.add_argument('-r', '--radius', help='circle radius', type=int, default=5)
args = parser.parse_args()

pathname = args.path
tail = args.tail
radius = args.radius

files = glob(join(pathname, '*.osr'))
if len(files) == 0:
    sys.exit('no replays to read')

replays = []

for name in files:
    player_name, score, points = parse(name)
    color = WHITE if len(files) == 1 else pick_color()
    replays.append((score, player_name, points, color))

replays.sort()

n = len(replays)
for score, player_name, points, color in replays:
    print('%2d. %15s - %d' % (n, player_name, score))
    n -= 1
print('read %d replays' % len(replays))

WIDTH = 512*2
HEIGHT = 384*2

pygame.mixer.pre_init(44100)
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('radius=%d tail=%d' % (radius, tail))
pygame.mixer.music.load(*glob(join(pathname, '*.mp3')))
pygame.mixer.music.play()
pygame.mixer.music.set_volume(0.5)
clock = pygame.time.Clock()

UPDATE_FPS = pygame.USEREVENT
pygame.time.set_timer(UPDATE_FPS, 1000)

last_pos = 0
done = False

screen.fill(BLACK)

while not done and pygame.mixer.music.get_busy():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                done = True
            elif event.mod & pygame.KMOD_CTRL and event.key == pygame.K_c:
                done = True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # left mouse button
                radius += 1
            elif event.button == 3: # right mouse button
                radius = max(0, radius - 1)
            elif event.button == 4: # scroll up
                tail += 10
            elif event.button == 5: # scroll down
                tail = max(0, tail - 10)
            pygame.display.set_caption('radius=%d tail=%d' % (radius, tail))

        elif event.type == UPDATE_FPS:
            sys.stderr.write('%5.0f fps\r' % clock.get_fps())

    clock.tick()
    current_pos = pygame.mixer.music.get_pos()
    screen.fill(BLACK)

    if tail:
        for _, _, points, color in replays:
            if tail:
                pointlist = []
            last_point = None

            for pos in range(max(current_pos-tail, 0), min(len(points), current_pos)):
                x, y = points[pos]
                x *= 2
                y *= 2
                point = x, y
                if 0 < x < WIDTH and 0 < y < HEIGHT:
                    if last_point != point:
                        if tail:
                            pointlist.append(point)
                        last_point = point

            if tail and len(pointlist) > 1:
                pygame.draw.aalines(screen, color, False, pointlist)

    if radius:
        for _, _, points, color in replays:
            if current_pos < len(points):
                x, y = points[current_pos]
                x *= 2
                y *= 2
                if 0 < x < WIDTH and 0 < y < HEIGHT:
                    pygame.gfxdraw.filled_circle(screen, x, y, radius, color)
                    pygame.gfxdraw.aacircle(screen, x, y, radius, BLACK)

    last_pos = current_pos

    pygame.display.flip()

pygame.quit()

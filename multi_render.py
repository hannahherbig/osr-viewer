import struct
import lzma
import time
import sys
from glob import glob
from os.path import join
import pygame
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

        print(player_name)
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
        return out

def rr():
    return random.randrange(16, 256)

def pick_color():
    a = random.randrange(64, 256)
    b = random.randrange(256)
    c = random.randrange(256)
    x = [a, b, c]
    random.shuffle(x)
    return tuple(x)

def quit():
    pygame.quit()
    sys.exit()

parser = argparse.ArgumentParser(description='osu! replay visualizer')
parser.add_argument('path', help='folder containing replays and mp3')
parser.add_argument('-t', '--tail', help='tail length', type=int, default=128)
parser.add_argument('-r', '--radius', help='circle radius', type=int, default=5)
args = parser.parse_args()

pathname = args.path
tail = args.tail
radius = args.radius

files = glob(join(pathname, '*.osr'))
if len(files) == 0:
    sys.exit('no replays to read')
if len(files) == 1:
    colors = [WHITE]
else:
    colors = [pick_color() for _ in files]

pointss = [parse(name) for name in files]

pygame.mixer.pre_init(44100)
pygame.init()
screen = pygame.display.set_mode((512*2, 384*2))
pygame.display.set_caption('radius=%d tail=%d' % (radius, tail))
pygame.mixer.music.load(*glob(join(pathname, '*.mp3')))
pygame.mixer.music.play()
pygame.mixer.music.set_volume(0.5)
clock = pygame.time.Clock()

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
                radius -= 1
                if radius < 0:
                    radius = 0
            elif event.button == 4: # scroll up
                tail += 8
            elif event.button == 5: # scroll down
                tail -= 8
                if tail < 0:
                    tail = 0
            pygame.display.set_caption('radius=%d tail=%d' % (radius, tail))

    clock.tick()
    sys.stderr.write('%5.0f fps\r' % clock.get_fps())

    current_pos = pygame.mixer.music.get_pos()

    screen.fill(BLACK)

    if tail:
        for color, points in zip(colors, pointss):
            if tail:
                pointlist = []
            last_point = None

            for pos in range(max(current_pos-tail, 0), current_pos):
                if pos < len(points):
                    x, y = points[pos]
                    point = (x*2, y*2)

                    if last_point != point:
                        if tail:
                            pointlist.append(point)
                        last_point = point

            if tail and len(pointlist) > 1:
                pygame.draw.aalines(screen, color, False, pointlist)

    if radius:
        for color, points in zip(colors, pointss):
            if current_pos < len(points):
                x, y = points[current_pos]
                pygame.draw.circle(screen, color, (x*2, y*2), radius)

    last_pos = current_pos

    pygame.display.flip()

pygame.quit()

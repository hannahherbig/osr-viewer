import struct
import lzma
import time
import sys
import glob
import pygame
import random

BLACK = (  0,   0,   0)
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
        for record in data.split(','):
            if record:
                w, x, y, z = record.split('|')
                w = int(w)
                t += w
                if t > last_t:
                    z = int(z)
                    x, y = float(x), float(y)
                    if hardrock:
                        y = 384 - y
                    out[last_t:t] = [(int(x), int(y))] * w
                last_t = t
        return out

def rr():
    return random.randrange(64, 256)

files = glob.glob('cracktraxxxx\\*.osr')
print('\n'.join(files))
colors = [(rr(), rr(), rr()) for _ in files]
pointss = [parse(name) for name in files]

pygame.init()
pygame.mixer.init(44100)
pygame.display.init()
screen = pygame.display.set_mode((512*2, 384*2))
pygame.mixer.music.load('cracktraxxxx\\cracktraxxxx.mp3')
pygame.mixer.music.play()
pygame.mixer.music.set_volume(0.5)
clock = pygame.time.Clock()

last_pos = 0

while pygame.mixer.music.get_busy():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    clock.tick()
    sys.stderr.write('%10.2f fps\r' % clock.get_fps())

    current_pos = pygame.mixer.music.get_pos()

    screen.fill(BLACK)

    for color, points in zip(colors, pointss):
        pointlist = []
        last_point = None
        for pos in range(max(current_pos-200, 0), current_pos):
            if pos < len(points):
                x, y = points[pos]
                point = (x*2, y*2)
                if last_point != point:
                    pointlist.append(point)
                    last_point = point
                # screen.fill(color, (x*2, y*2, 5, 5))
        if len(pointlist) > 1:
            pygame.draw.aalines(screen, color, False, pointlist)

        if last_point:
            pygame.draw.circle(screen, color, last_point, 10)

    last_pos = current_pos

    pygame.display.flip()

pygame.quit()

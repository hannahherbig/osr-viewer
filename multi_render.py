import struct
import lzma
import time
import sys
import glob
import pygame

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
    out = []
    with open(path, 'rb') as f:
        mode, version = struct.unpack('<BI', f.read(5))
        beatmap_md5 = parse_string(f)
        player_name = parse_string(f)
        replay_md5 = parse_string(f)
        n300, n100, n50, ngeki, nkatu, nmiss, score, combo, perfect, mods = struct.unpack('<HHHHHHIH?I', f.read(23))
        life_bar = parse_string(f) # ms|life
        timestamp, length = struct.unpack('<QI', f.read(12))
        hardrock = mods & 16 == 16

        data = lzma.decompress(f.read(length)).decode()
        for record in data.split(','):
            if record:
                w, x, y, z = record.split('|')
                w, z = int(w), int(z)
                x, y = float(x), float(y)
                if w > 0:
                    for i in range(w):
                        # flip hr back so it lines up
                        out.append((int(x), int(384-y if hardrock else y)))
    return out

files = glob.glob('ooi\\*.osr')
print(files)
pointss = [parse(name) for name in files]

pygame.init()
pygame.mixer.init(44100)
pygame.mixer.music.load('ooi\\ooi.mp3')
pygame.mixer.music.play()
pygame.display.init()
screen = pygame.display.set_mode((512, 384))
clock = pygame.time.Clock()

while pygame.mixer.music.get_busy():
    pos = pygame.mixer.music.get_pos()

    screen.fill(BLACK)

    for points in pointss:
        if pos < len(points):
            x, y = points[pos]
            screen.fill(WHITE, (x, y, 5, 5))

    pygame.display.flip()
    pygame.event.pump()

    clock.tick(144)

pygame.display.quit()

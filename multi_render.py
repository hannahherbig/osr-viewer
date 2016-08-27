import time
import sys
from glob import glob
from os.path import join
import pygame
import pygame.gfxdraw
import random
import argparse
import osr

BLACK = (  0,   0,   0)
GRAY  = (100, 100, 100)
WHITE = (255, 255, 255)

def pick_color():
    return tuple(random.randrange(64, 256) for i in range(3))

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
    replay = osr.read_file(name)
    # this is hacky but whatever
    replay.color = WHITE if len(files) == 1 else pick_color()
    replays.append(replay)

replays.sort()

n = len(replays)
for r in replays:
    print('%2d. %15s - %d' % (n, r.player, r.score))
    n -= 1
print('read %d replays' % len(replays))

HEIGHT = 768
KEYSIZE = min(15, HEIGHT // len(replays))
WIDTH = 1024+5*KEYSIZE

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
        for replay in replays:
            if tail:
                pointlist = []
            last_point = None

            for pos in range(max(current_pos-tail, 0), min(len(replay), current_pos)):
                p = replay[pos]
                y = p.y
                if replay.has_mod(16): # hr
                    y = 384 - y
                x, y = p.x*2, y*2
                point = x, y
                if 0 < x < WIDTH and 0 < y < HEIGHT:
                    if last_point != point:
                        if tail:
                            pointlist.append(point)
                        last_point = point

            if tail and len(pointlist) > 1:
                pygame.draw.aalines(screen, replay.color, False, pointlist)

    if radius:
        for replay in replays:
            if current_pos < len(replay):
                p = replay[current_pos]
                y = p.y
                if replay.has_mod(16): # hr
                    y = 384 - y
                x, y = int(p.x*2), int(y*2)
                if 0 < x < WIDTH and 0 < y < HEIGHT:
                    pygame.gfxdraw.filled_circle(screen, x, y, radius, replay.color)
                    pygame.gfxdraw.aacircle(screen, x, y, radius, BLACK)

    for i, replay in enumerate(replays):
        p = replay[current_pos]
        y = i*KEYSIZE
        for j, o in enumerate(p.buttons):
            x = 1024+j*KEYSIZE
            rect = (x, y, KEYSIZE, KEYSIZE)
            if o:
                screen.fill(replay.color, rect)
            else:
                screen.fill(BLACK, rect)

    last_pos = current_pos

    pygame.display.flip()

pygame.quit()

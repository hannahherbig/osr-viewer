import lzma
import struct
import sys
from collections import deque
from textwrap import dedent

import pygame

BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (64, 64, 64)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)


def parse_uleb128(f):
    result = 0
    shift = 0
    while True:
        byte = struct.unpack("<B", f.read(1))[0]
        result |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0:
            break
        shift += 7

    return result


def parse_string(f):
    head = struct.unpack("<B", f.read(1))[0]
    if head == 0x00:
        return ""
    elif head == 0x0B:
        length = parse_uleb128(f)
        return f.read(length).decode()


MODES = ["osu!", "Taiko", "Catch the Beat", "osu!mania"]
SHORTMODS = ["", "NF", "EZ", "", "HD", "HR", "SD", "DT", "RX", "HT", "NC", "FL"]
MODS = [
    "None",
    "NoFail",
    "Easy",
    "NoVideo",
    "Hidden",
    "HardRock",
    "SuddenDeath",
    "DoubleTime",
    "Relax",
    "HalfTime",
    "NightCore",
    "Flashlight",
    "Autoplay",
    "SpunOut",
    "Autopilot",
    "Perfect",
    "Key4",
    "Key5",
    "Key6",
    "Key7",
    "Key8",
    "FadeIn",
    "Random",
    "Cinema",
    "TargetPractice",
    "Key9",
    "Co-op",
    "Key1",
    "Key3",
    "Key2",
]


def mods_to_str(n):
    i = 1
    s = set()
    while n:
        if n & 1:
            s.add(MODS[i])
        i += 1
        n >>= 1
    return ",".join(s)


def shortmods(n):
    i = 1
    s = ""
    while n:
        if n & 1:
            s += SHORTMODS[i]
        i += 1
        n >>= 1
    return s


def to_bin(n, size):
    s = ""
    while size:
        s = s + "01"[n & 1]
        n >>= 1
        size -= 1
    return s


def keys(n):
    k1 = n & 5 == 5
    k2 = n & 10 == 10
    m1 = not k1 and n & 1 == 1
    m2 = not k2 and n & 2 == 2
    smoke = n & 16 == 16
    return " ".join(
        [
            ("K1" if k1 else "  "),
            ("K2" if k2 else "  "),
            ("M1" if m1 else "  "),
            ("M2" if m2 else "  "),
            ("SMOKE" if smoke else "     "),
        ]
    )


path = r"""C:\Users\notan\AppData\Local\osu!\Replays\Cookiezi - xi - Blue Zenith [FOUR DIMENSIONS] (2016-01-02) Osu.osr"""
out = deque()

with open(path, "rb") as f:
    mode, version = struct.unpack("<BI", f.read(5))
    beatmap_md5 = parse_string(f)
    player_name = parse_string(f)
    replay_md5 = parse_string(f)
    n300, n100, n50, ngeki, nkatu, nmiss, score, combo, perfect, mods = struct.unpack(
        "<HHHHHHIH?I", f.read(23)
    )
    life_bar = parse_string(f)  # ms|life
    timestamp, length = struct.unpack("<QI", f.read(12))
    print(
        dedent(
            """
        Game mode   : %s
        Version     : %d
        Beatmap MD5 : %s
        Player      : %s
        Replay MD5  : %s
        300s        : %d
        100s        : %d
        50s         : %d
        Gekis       : %d
        Katus       : %d
        Misses      : %d
        Score       : %d
        Combo       : %d
        Perfect     : %s
        Mods        : %s
        Life        : %s
        Timestamp   : %d
        Length      : %d
    """
        )
        % (
            MODES[mode],
            version,
            beatmap_md5,
            player_name,
            replay_md5,
            n300,
            n100,
            n50,
            ngeki,
            nkatu,
            nmiss,
            score,
            combo,
            perfect,
            shortmods(mods),
            life_bar,
            timestamp,
            length,
        )
    )

    data = lzma.decompress(f.read(length)).decode()
    t = 0
    for record in data.split(","):
        if record:
            w, x, y, z = record.split("|")
            w, z = int(w), int(z)
            x, y = float(x), float(y)
            if w >= 0:
                t += w
                out.append((t, int(x), int(y)))

pygame.init()
pygame.mixer.init(44100)
pygame.mixer.music.load(
    r"""C:\Users\notan\AppData\Local\osu!\Songs\292301 xi - Blue Zenith\zenith.mp3"""
)
pygame.mixer.music.play()
screen = pygame.display.set_mode((512, 384))
clock = pygame.time.Clock()

while pygame.mixer.music.get_busy():
    while out and out[0][0] < pygame.mixer.music.get_pos():
        out.popleft()

    screen.fill(BLACK)

    if out:
        t, x, y = out[0]
        screen.fill(WHITE, (x, y, 10, 10))
        sys.stdout.write("%3d %3d\r" % (x, y))

    pygame.display.flip()

    clock.tick(60)

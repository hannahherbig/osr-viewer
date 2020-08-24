import lzma
import struct
from collections import deque, namedtuple

MODES = ["osu!", "Taiko", "Catch the Beat", "osu!mania"]
SHORTMODS = [
    None,
    "NF",
    "EZ",
    None,
    "HD",
    "HR",
    "SD",
    "DT",
    "RX",
    "HT",
    "NC",
    "FL",
    "AO",
    "SO",
    "AP",
    "PF",
    "4K",
    "5K",
    "6K",
    "7K",
    "8K",
    "FI",
    "RD",
    None,
    "TP",
    "9K",
    "CO",
    "1K",
    "3K",
    "2K",
]
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


def shortmods(n):
    i = 1
    s = ""
    while n:
        if n & 1:
            s += SHORTMODS[i]
        i += 1
        n >>= 1
    return s


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


def each_bit(n, count):
    for x in range(count):
        yield n & (1 << x)


def keys(z):
    k1 = z & 5 == 5
    k2 = z & 10 == 10
    yield k1
    yield k2
    yield not k1 and z & 1 == 1
    yield not k2 and z & 2 == 2
    yield z & 16 == 16


ReplayPoint = namedtuple("ReplayPoint", "t x y z")


class Replay:
    __slots__ = [
        "mode",
        "version",
        "beatmap_hash",
        "player",
        "replay_hash",
        "n300",
        "n100",
        "n50",
        "ngeki",
        "nkatu",
        "nmiss",
        "score",
        "combo",
        "perfect",
        "mods",
        "life_events",
        "timestamp",
        "length",
        "replay",
        "color",
    ]

    def read_file(self, f, flip_hr=False):
        self.mode, self.version = struct.unpack("<BI", f.read(5))
        assert self.mode == 0, "%s support not added yet" % MODES[self.mode]
        self.beatmap_hash = parse_string(f)
        self.player = parse_string(f)
        self.replay_hash = parse_string(f)
        (
            self.n300,
            self.n100,
            self.n50,
            self.ngeki,
            self.nkatu,
            self.nmiss,
            self.score,
            self.combo,
            self.perfect,
            self.mods,
        ) = struct.unpack("<HHHHHHIH?I", f.read(23))
        self.life_events = deque()
        for rec in parse_string(f).split(","):
            if rec:
                u, v = rec.split("|")
                self.life_events.append((int(u), float(v)))
        self.timestamp, self.length = struct.unpack("<QI", f.read(12))
        self.replay = replay = deque()
        flip = flip_hr and self.has_mod(16)
        t = 0
        for rec in lzma.decompress(f.read(self.length)).decode().split(","):
            if rec:
                w, x, y, z = rec.split("|")
                w, x, y, z = int(w), float(x), float(y), int(z)
                t += w
                if flip:
                    y = 384 - y
                p = ReplayPoint(t, x, y, z)
                replay.append(p)

    def has_mod(self, mod):
        return self.mods & mod == mod

    def __len__(self):
        return len(self.replay)

    def __getitem__(self, t):
        if t < len(self):
            return self.replay[t]
        return self.replay[-1]

    def _key(self):
        return (self.score, -self.timestamp, self.player)

    def __lt__(self, other):
        return self._key() < other._key()


def read_file(f, flip_hr=False):
    if isinstance(f, str):
        with open(f, "rb") as ff:
            return read_file(ff, flip_hr)
    r = Replay()
    r.read_file(f, flip_hr)
    return r

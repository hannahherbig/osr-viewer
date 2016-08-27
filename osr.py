import struct
import lzma
from collections import namedtuple

MODES = ['osu!', 'Taiko', 'Catch the Beat', 'osu!mania']
SHORTMODS = [None, 'NF', 'EZ', None, 'HD', 'HR', 'SD', 'DT', 'RX', 'HT', 'NC',
             'FL', 'AO', 'SO', 'AP', 'PF', '4K', '5K', '6K', '7K', '8K', 'FI',
             'RD', None, 'TP', '9K', 'CO', '1K', '3K', '2K']
MODS = ['None', 'NoFail', 'Easy', 'NoVideo', 'Hidden', 'HardRock',
        'SuddenDeath', 'DoubleTime', 'Relax', 'HalfTime', 'NightCore',
        'Flashlight', 'Autoplay', 'SpunOut', 'Autopilot', 'Perfect', 'Key4',
        'Key5', 'Key6', 'Key7', 'Key8', 'FadeIn', 'Random', 'Cinema',
        'TargetPractice', 'Key9', 'Co-op', 'Key1', 'Key3', 'Key2']

def shortmods(n):
    i = 1
    s = ''
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

ReplayPoint = namedtuple('ReplayPoint', 'x y buttons')

class Buttons:
    def __init__(self, z):
        self.z = z
        self.k1 = z & 5 == 5
        self.k2 = z & 10 == 10
        self.m1 = not self.k1 and z & 1 == 1
        self.m2 = not self.k2 and z & 2 == 2
        self.smoke = z & 16 == 16

    def __iter__(self):
        yield self.k1
        yield self.k2
        yield self.m1
        yield self.m2
        yield self.smoke

    def __str__(self):
        return  ' '.join([('K1' if self.k1 else '  '),
                          ('K2' if self.k2 else '  '),
                          ('M1' if self.m1 else '  '),
                          ('M2' if self.m2 else '  '),
                          ('SMOKE' if self.smoke else '     ')])

class Replay:
    def read_file(self, f):
        self.mode, self.version = struct.unpack('<BI', f.read(5))
        assert self.mode == 0, "%s support not added yet" % MODES[self.mode]
        self.beatmap_hash = parse_string(f)
        self.player = parse_string(f)
        self.replay_hash = parse_string(f)
        self.n300, self.n100, self.n50, self.ngeki, self.ngaku, self.nmiss, \
            self.score, self.combo, self.perfect, self.mods = \
            struct.unpack('<HHHHHHIH?I', f.read(23))
        self.life_events = []
        for rec in parse_string(f).split(','):
            if rec:
                u, v = rec.split('|')
                self.life_events.append((int(u), float(v)))
        self.timestamp, self.length = struct.unpack('<QI', f.read(12))
        self.replay = []
        last_t = t = 0
        for rec in lzma.decompress(f.read(self.length)).decode().split(','):
            if rec:
                w, x, y, z = rec.split('|')
                w = int(w)
                t += w
                if t > last_t:
                    e = ReplayPoint(float(x), float(y), Buttons(int(z)))
                    self.replay[last_t:t] = [e] * w
                last_t = t

    def has_mod(self, mod):
        return self.mods & mod == mod

    def __len__(self):
        return len(self.replay)

    def __getitem__(self, t):
        if t < len(self):
            return self.replay[t]
        return self.replay[-1]

    def _sort_key(self):
        return (self.score, -self.timestamp, self.player)

    def __lt__(self, other): return self._sort_key() < other._sort_key()

def read_file(f):
    if isinstance(f, str):
        with open(f, 'rb') as ff:
            return read_file(ff)
    r = Replay()
    r.read_file(f)
    return r

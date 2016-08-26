import struct
import lzma

MODES = ['osu!', 'Taiko', 'Catch the Beat', 'osu!mania']
SHORTMODS = ['', 'NF', 'EZ', '', 'HD', 'HR', 'SD', 'DT', 'RX', 'HT', 'NC', 'FL']
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

def keys(n):
    k1 = n & 5 == 5
    k2 = n & 10 == 10
    m1 = not k1 and n & 1 == 1
    m2 = not k2 and n & 2 == 2
    smoke = n & 16 == 16
    return ' '.join([('K1' if k1 else '  '),
                     ('K2' if k2 else '  '),
                     ('M1' if m1 else '  '),
                     ('M2' if m2 else '  '),
                     ('SMOKE' if smoke else '     ')])

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

class Replay:
    def read_entire_file(self, f):
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
        self.replay_events = []
        for rec in lzma.decompress(f.read(self.length)).decode().split(','):
            if rec:
                w, x, y, z = record.split('|')
                self.replay_events.append((int(w), float(x), float(y), int(z)))

    def each_ms(self):
        last = None
        for w, x, y, z in self.replay_events:


def parse_file(f):
    if isinstance(f, str):
        f = open(f, 'rb')

    r = Replay()
    r.mode, r.version = struct.unpack('<BI', f.read(5))
    r.beatmap_hash = parse_string(f)
    r.player = parse_string(f)
    r.replay_hash = parse_string(f)
    r.n300, r.n100, r.n50, r.ngeki, r.nkatu, r.nmiss, r.score, r.combo, \
        r.perfect, r.mods = struct.unpack('<HHHHHHIH?I', f.read(23))
    r.life_events = []

    for rec in parse_string(f).split(','):
        if rec:
            ms, life = rec.split('|')
            ms, life = int(ms), float(life)
            r.life_events.append((ms, life))

    r.timestamp, r.length = struct.unpack('<QI', f.read(12))
    r.replay = []

    for rec in lzma.decompress(f.read(r.length)).decode().split(','):
        if rec:
            w, x, y, z = record.split('|')
            w, x, y, z = int(w), float(x), float(y), int(z)
            r.replay.append((w, x, y, z))

    f.close()

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

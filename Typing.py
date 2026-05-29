import pygame, sys, math, random, json, os, array

# ═══════════════════════════════════════════════════════════
#  INIT
# ═══════════════════════════════════════════════════════════
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

W, H  = 1040, 640
GY    = H - 95           # ground y-level
FPS   = 60
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("TYPING RUNNER  ✦  Enhanced Edition v2")
clock  = pygame.time.Clock()

# ═══════════════════════════════════════════════════════════
#  FONTS
# ═══════════════════════════════════════════════════════════
def _font(names, size):
    for n in names:
        try:
            f = pygame.font.SysFont(n, size)
            if f: return f
        except: pass
    return pygame.font.SysFont("Arial", size)

F16 = _font(["Consolas","Courier New","monospace"], 16)
F22 = _font(["Consolas","Courier New","monospace"], 22)
F30 = _font(["Consolas","Courier New","monospace"], 30)
F52 = _font(["Consolas","Courier New","monospace"], 52)
F76 = _font(["Consolas","Courier New","monospace"], 76)

# ═══════════════════════════════════════════════════════════
#  COLOUR PALETTE
# ═══════════════════════════════════════════════════════════
BG     = (6, 4, 14)
WHITE  = (230, 230, 240)
GRAY   = (110, 110, 130)
DGRAY  = (35,  35,  50)
CYAN   = (0,   210, 255)
GREEN  = (0,   255, 120)
RED    = (255,  55,  55)
YELLOW = (255, 220,  10)
PURPLE = (185,  70, 255)
ORANGE = (255, 145,  25)
PINK   = (255,  80, 180)
TEAL   = (0,   200, 160)

def lerp_col(a, b, t):
    return tuple(int(a[i]*(1-t)+b[i]*t) for i in range(3))

# ═══════════════════════════════════════════════════════════
#  SOUND GENERATION
# ═══════════════════════════════════════════════════════════
def _snd(freq, ms, vol=0.35, decay=True):
    sr = 22050; n = int(sr * ms / 1000)
    buf = array.array('h')
    for i in range(n):
        env = (1 - i/n) if decay else 1.0
        v   = int(vol * 32767 * env * math.sin(2*math.pi*freq*i/sr))
        buf.append(v); buf.append(v)
    try:   return pygame.mixer.Sound(buffer=buf)
    except: return None

def _chord(freqs, ms, vol=0.25, decay=True):
    sr = 22050; n = int(sr*ms/1000)
    buf = array.array('h')
    for i in range(n):
        env = (1 - i/n) if decay else 1.0
        v   = sum(math.sin(2*math.pi*f*i/sr) for f in freqs)
        buf.append(int(vol*32767*env*v/len(freqs)))
        buf.append(int(vol*32767*env*v/len(freqs)))
    try:   return pygame.mixer.Sound(buffer=buf)
    except: return None

SND_OK    = _chord([880, 1100], 90)
SND_COMBO = _chord([660, 880, 1100], 150)
SND_FAIL  = _snd(160, 200)
SND_HIT   = _snd(220, 180)
SND_PU    = _chord([1320, 1760], 110)
SND_LEVEL = _chord([440, 550, 660], 300, decay=False)
SND_TYPO  = _snd(280, 80, vol=0.15)  # soft typo sound

def sfx(s):
    if s:
        try: s.play()
        except: pass

# ═══════════════════════════════════════════════════════════
#  HIGH SCORE
# ═══════════════════════════════════════════════════════════
HS_FILE = "typing_runner_hs.json"
def load_hs():
    if os.path.exists(HS_FILE):
        try:
            with open(HS_FILE) as f: return json.load(f).get("hs", 0)
        except: pass
    return 0

def save_hs(v):
    try:
        with open(HS_FILE,"w") as f: json.dump({"hs":v}, f)
    except: pass

high_score = load_hs()

# ═══════════════════════════════════════════════════════════
#  STORY MODE DATA
# ═══════════════════════════════════════════════════════════
CHAPTERS = [
    dict(title="Chapter 1  ·  The Awakening",
         lines=["You jolt awake in a rain-slicked neon alley.",
                "A glitching terminal flashes: TYPE FAST OR GET ERASED.",
                "You don't know who's chasing you — but your fingers do."],
         diff="easy", target=7,
         sky_top=(5,5,30), sky_bot=(18,12,60), gnd=(28,24,48), accent=CYAN),
    dict(title="Chapter 2  ·  Downtown Rush",
         lines=["The streets compress into corridors of blinding light.",
                "Drones lock on. Barriers slam down across your path.",
                "Your only weapon: the speed of your own thoughts."],
         diff="normal", target=14,
         sky_top=(28,8,5), sky_bot=(62,18,10), gnd=(52,24,18), accent=ORANGE),
    dict(title="Chapter 3  ·  The Underworld",
         lines=["You drop below the city into the data-stream underworld.",
                "Words dissolve before you finish reading them.",
                "Only the fastest typists have ever made it back."],
         diff="normal", target=22,
         sky_top=(10,2,32), sky_bot=(30,5,72), gnd=(24,10,48), accent=PURPLE),
    dict(title="Chapter 4  ·  The Pursuit",
         lines=["The algorithm has learned your rhythm. It adapts.",
                "You must break every pattern, every habit.",
                "Type harder than thought itself."],
         diff="hard", target=30,
         sky_top=(0,22,10), sky_bot=(0,58,28), gnd=(8,42,22), accent=GREEN),
    dict(title="Chapter 5  ·  Final Run",
         lines=["The data-wall is ahead. One last sprint.",
                "Every. Single. Keystroke. Echoes. Forever.",
                "FINISH. THE. RUN."],
         diff="hard", target=40,
         sky_top=(32,0,0), sky_bot=(80,5,5), gnd=(58,14,14), accent=RED),
]

# ═══════════════════════════════════════════════════════════
#  WORDS
# ═══════════════════════════════════════════════════════════
W_EASY = ["run","jump","left","right","duck","slide","go","fast","dash","fly",
          "skip","leap","fire","drop","move","step","kick","push","flip","turn"]
W_NORM = W_EASY + ["dodge","escape","boost","sprint","rush","avoid","smash",
                    "evade","break","surge","blast","drive","pivot","vault",
                    "flank","charge","phase","ghost","storm","burst"]
W_HARD = ["accelerate","eliminate","teleport","overdrive","counterattack",
          "reposition","annihilate","devastate","obliterate","hyperdrive",
          "supercharge","disintegrate","rampage","quantumleap","velocity",
          "barricade","overcharge","flashpoint","shutdown","infiltrate"]

def pick(diff):
    if diff == "easy":   pool = W_EASY
    elif diff == "hard": pool = W_HARD + W_NORM
    else:                pool = W_NORM
    return random.choice(pool)

# ═══════════════════════════════════════════════════════════
#  BACKGROUND ASSETS
# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════
#  IMAGE ASSET PATHS  — edit these to point at your files.
#  Set any value to None to keep the built-in drawn version.
# ═══════════════════════════════════════════════════════════

BG_IMAGE_PATH     = None   # e.g. "assets/background.png"  — full-screen bg image
GROUND_IMG_PATH   = None   # e.g. "assets/ground.png"      — tiled horizontally
OBSTACLE_IMG_PATH = None   # e.g. "assets/obstacle.png"    — scaled to each obstacle
POWERUP_IMG_PATH  = None   # e.g. "assets/powerup.png"     — all power-up circles

def _load_img(path):
    if path is None: return None
    try:   return pygame.image.load(path).convert_alpha()
    except Exception as e:
        print(f"[IMG] Could not load '{path}': {e}"); return None

_bg_img     = _load_img(BG_IMAGE_PATH)
_ground_img = _load_img(GROUND_IMG_PATH)
_obs_img    = _load_img(OBSTACLE_IMG_PATH)
_pu_img     = _load_img(POWERUP_IMG_PATH)

if _bg_img:
    _bg_img = pygame.transform.scale(_bg_img, (W, H))

# ── fallback procedural bg data ──────────────────────────
random.seed(12)
STARS = [(random.randint(0,W), random.randint(0,H//2+30),
          random.randint(1,3),  random.random()*math.pi*2) for _ in range(140)]
def _mountain(count, lo, hi, seed):
    random.seed(seed); pts = [(0, H)]
    step = W // (count - 1)
    for i in range(count):
        pts.append((i*step, H - random.randint(lo, hi)))
    pts.append((W, H)); random.seed(); return pts
MTN_FAR  = _mountain(18, 110, 230, 42)
MTN_MID  = _mountain(14,  55, 140, 99)
MTN_NEAR = _mountain(10,  25,  80, 77)
random.seed()

def draw_bg(surf, sky_top, sky_bot, gnd_col):
    if _bg_img:
        surf.blit(_bg_img, (0, 0))
        return
    for i in range(H):
        t = i/H; col = lerp_col(sky_top, sky_bot, t)
        pygame.draw.line(surf, col, (0,i),(W,i))
    tick = pygame.time.get_ticks()/1000
    for sx,sy,sr,phase in STARS:
        bright = 160 + int(60*math.sin(tick*1.3+phase))
        c = (min(255,bright),min(255,bright),min(255,bright+30))
        pygame.draw.circle(surf, c, (sx,sy), sr)
    def mc(base, offset):
        return tuple(min(255,base[j]+offset) for j in range(3))
    pygame.draw.polygon(surf, mc(sky_top,18), MTN_FAR)
    pygame.draw.polygon(surf, mc(sky_top,36), MTN_MID)
    pygame.draw.polygon(surf, mc(sky_top,58), MTN_NEAR)
    pygame.draw.rect(surf, gnd_col, (0,GY,W,H-GY))
    edge = mc(gnd_col, 55)
    pygame.draw.line(surf, edge, (0,GY),(W,GY), 3)

road_scroll = 0.0
def draw_road(surf, offset, gnd_col):
    if _ground_img:
        tw = _ground_img.get_width()
        x  = -(int(offset) % tw)
        while x < W:
            surf.blit(_ground_img, (x, GY))
            x += tw
        return
    step = 72
    dash_col = tuple(min(255,c+42) for c in gnd_col)
    for i in range(-1, W//step+2):
        x = i*step - (int(offset)%step)
        pygame.draw.rect(surf, dash_col, (x,GY+20,48,8), border_radius=3)

# ═══════════════════════════════════════════════════════════
#  SPRITE LOADER
#  ─────────────────────────────────────────────────────────
#  Point SPRITE_PATH at your image file (PNG recommended).
#
#  If your file is a SPRITE SHEET with multiple frames laid
#  out in a horizontal row, set SPRITE_SHEET = True and fill
#  in how many columns (frames) it has.  The loader will
#  slice it evenly.  Frame order expected:  run_A, run_B, jump
#  (if you only have 1 frame it just uses that for all states)
#
#  If it's a single standalone image, set SPRITE_SHEET = False.
# ═══════════════════════════════════════════════════════════

SPRITE_PATH  = "player.png"   # ← change this to your file path
SPRITE_SHEET = False          # ← set True if it's a horizontal strip
SHEET_COLS   = 3              # ← number of frames in the strip (ignored if SPRITE_SHEET=False)
SPRITE_SCALE = 3              # ← scale multiplier (1 = original size, 3 = 3× bigger)

def _load_sprite():
    try:
        raw = pygame.image.load(SPRITE_PATH).convert_alpha()
    except Exception as e:
        print(f"[SPRITE] Could not load '{SPRITE_PATH}': {e}")
        print("[SPRITE] Falling back to placeholder rectangle.")
        # Fallback: plain cyan rectangle so game still runs
        raw = pygame.Surface((16, 24), pygame.SRCALPHA)
        raw.fill((0, 200, 240, 255))

    if SPRITE_SHEET:
        # Slice horizontal strip into individual frames
        fw = raw.get_width() // SHEET_COLS
        fh = raw.get_height()
        frames = []
        for i in range(SHEET_COLS):
            frame = pygame.Surface((fw, fh), pygame.SRCALPHA)
            frame.blit(raw, (0, 0), (i * fw, 0, fw, fh))
            frames.append(frame)
    else:
        frames = [raw]   # single image → same frame for all states

    # Scale up
    def _scale(s):
        if SPRITE_SCALE == 1:
            return s
        w = s.get_width()  * SPRITE_SCALE
        h = s.get_height() * SPRITE_SCALE
        return pygame.transform.scale(s, (w, h))

    frames = [_scale(f) for f in frames]

    # Pad to 3 frames: [run_A, run_B, jump]
    while len(frames) < 3:
        frames.append(frames[-1])

    return frames   # [run_A, run_B, jump]

def _tint_red(surf):
    s = surf.copy()
    overlay = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    overlay.fill((255, 30, 30, 130))
    s.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return s

_frames      = _load_sprite()
_f0, _f1, _fj = _frames[0], _frames[1], _frames[2]
_f0r = _tint_red(_f0)
_f1r = _tint_red(_f1)
_fjr = _tint_red(_fj)

SPRITE_W = _f0.get_width()
SPRITE_H = _f0.get_height()

# ═══════════════════════════════════════════════════════════
#  PARTICLES
# ═══════════════════════════════════════════════════════════
class Particle:
    __slots__ = ('x','y','vx','vy','col','life','size')
    def __init__(self, x, y, col):
        self.x=float(x); self.y=float(y)
        angle=random.uniform(0,math.pi*2); speed=random.uniform(1.5,6.0)
        self.vx=math.cos(angle)*speed; self.vy=math.sin(angle)*speed-2
        self.col=col; self.life=1.0; self.size=random.randint(3,9)
    def update(self, dt):
        self.x+=self.vx; self.y+=self.vy; self.vy+=9*dt; self.vx*=0.98; self.life-=2.0*dt
    def draw(self, surf):
        if self.life<=0: return
        s=pygame.Surface((self.size*2,self.size*2),pygame.SRCALPHA)
        a=int(255*max(0,self.life))
        pygame.draw.circle(s,(*self.col,a),(self.size,self.size),self.size)
        surf.blit(s,(int(self.x-self.size),int(self.y-self.size)))

particles=[]

def burst(x, y, col, n=24):
    particles.extend(Particle(x,y,col) for _ in range(n))

def ring_burst(x, y, col, n=14):
    for i in range(n):
        angle=(i/n)*math.pi*2; p=Particle(x,y,col)
        spd=random.uniform(3,7)
        p.vx=math.cos(angle)*spd; p.vy=math.sin(angle)*spd
        particles.append(p)

# ═══════════════════════════════════════════════════════════
#  FLOATING TEXT
# ═══════════════════════════════════════════════════════════
class FloatText:
    def __init__(self, x, y, text, col, big=False):
        self.x=float(x); self.y=float(y)
        self.text=text; self.col=col; self.life=1.0
        self.font=F52 if big else F30
    def update(self, dt): self.y-=65*dt; self.life-=1.6*dt
    def draw(self, surf):
        if self.life<=0: return
        s=self.font.render(self.text,True,self.col)
        s.set_alpha(int(255*max(0,self.life)))
        surf.blit(s,(int(self.x-s.get_width()//2),int(self.y)))

floats=[]

# ═══════════════════════════════════════════════════════════
#  PLAYER  (pixel-art sprite)
# ═══════════════════════════════════════════════════════════
class Player:
    def __init__(self):
        self.x       = 135
        self.y       = float(GY)
        self.vy      = 0.0
        self.ground  = True
        self.anim    = 0.0
        self.shield  = False
        self.sh_t    = 0.0
        self.flash   = 0.0
        self.trail   = []

    @property
    def foot_y(self): return int(self.y)
    @property
    def cx(self): return int(self.x)

    def update(self, dt):
        speed_mult = 2.0 if not self.ground else 1.0
        if self.ground:
            self.anim += dt * 10
        else:
            self.anim += dt * 5

        if not self.ground:
            self.vy += 32*dt
            self.y  += self.vy
            if self.y >= GY:
                self.y=GY; self.vy=0; self.ground=True

        if self.shield:
            self.sh_t -= dt
            if self.sh_t <= 0: self.shield=False
        self.flash = max(0, self.flash-dt)

        # Motion trail (store foot position)
        self.trail.append((self.cx, self.foot_y, 160))
        if len(self.trail) > 8:
            self.trail.pop(0)

    def jump(self):
        if self.ground:
            self.vy=-15; self.ground=False
            burst(self.cx, self.foot_y, CYAN, 8)

    def rect(self):
        return pygame.Rect(self.cx - SPRITE_W//2 + 6,
                           self.foot_y - SPRITE_H + 4,
                           SPRITE_W - 12, SPRITE_H - 4)

    def _get_frame(self):
        flash_on = self.flash > 0 and int(self.flash*12)%2 == 0
        if not self.ground:
            return _fjr if flash_on else _fj
        idx = int(self.anim) % 2
        if flash_on:
            return _f0r if idx==0 else _f1r
        return _f0 if idx==0 else _f1

    def draw(self, surf):
        # Motion trail
        for i,(tx,ty,_) in enumerate(self.trail):
            alpha = int(80 * i/len(self.trail))
            s = pygame.Surface((SPRITE_W, SPRITE_H), pygame.SRCALPHA)
            frame = _f0 if i%2==0 else _f1
            s.blit(frame,(0,0))
            s.set_alpha(alpha)
            surf.blit(s, (tx - SPRITE_W//2, ty - SPRITE_H))

        frame = self._get_frame()
        draw_x = self.cx - SPRITE_W//2
        draw_y = self.foot_y - SPRITE_H

        # Glow under sprite
        gs = pygame.Surface((SPRITE_W+16, SPRITE_H+12), pygame.SRCALPHA)
        pygame.draw.ellipse(gs, (*CYAN, 25), (0,0,SPRITE_W+16, SPRITE_H+12))
        surf.blit(gs, (draw_x-8, draw_y-6))

        surf.blit(frame, (draw_x, draw_y))

        # Shield bubble
        if self.shield:
            r  = 42 + int(4*math.sin(self.anim*2))
            ss = pygame.Surface((r*2+6,r*2+6), pygame.SRCALPHA)
            pygame.draw.circle(ss,(100,220,255,45),(r+3,r+3),r)
            pygame.draw.circle(ss,(160,240,255,170),(r+3,r+3),r,2)
            surf.blit(ss,(self.cx-r-3, self.foot_y-SPRITE_H//2-r-8))

        # Shadow on ground
        sw = int(30 + 10*(1 - abs(self.foot_y - GY)/200))
        shadow = pygame.Surface((sw*2, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0,0,0,80), (0,0,sw*2,10))
        surf.blit(shadow, (self.cx - sw, GY - 4))

player = Player()

# ═══════════════════════════════════════════════════════════
#  OBSTACLES
# ═══════════════════════════════════════════════════════════
OBS_TYPES = [
    dict(name="block",   w=(28,55), h=(35,75), col=(200,45,45)),
    dict(name="barrier", w=(60,90), h=(20,35), col=(200,130,30)),
    dict(name="spike",   w=(20,35), h=(45,80), col=(180,40,180)),
    dict(name="wall",    w=(14,22), h=(GY//2, GY-10), col=(60,60,200)),
]

class Obstacle:
    def __init__(self, spd):
        t=random.choice(OBS_TYPES)
        self.spd=spd; self.x=float(W+60)
        self.w=random.randint(*t["w"]); self.h=random.randint(*t["h"])
        self.col=tuple(random.randint(max(0,c-30),min(255,c+30)) for c in t["col"])
    def update(self,dt): self.x -= self.spd*60*dt
    def gone(self):      return self.x+self.w < 0
    def top(self):       return GY-self.h
    def rect(self):      return pygame.Rect(int(self.x),int(self.top()),self.w,self.h)
    def draw(self, surf):
        x,y=int(self.x),int(self.top()); w,h=self.w,self.h
        if _obs_img:
            scaled = pygame.transform.scale(_obs_img, (w, h))
            surf.blit(scaled, (x, y))
        else:
            pygame.draw.rect(surf,self.col,(x,y,w,h),border_radius=3)
            ec=tuple(min(255,c+90) for c in self.col)
            pygame.draw.rect(surf,ec,(x,y,w,h),2,border_radius=3)
            for i in range(0,h,18):
                pygame.draw.line(surf,(255,220,0),(x+1,y+i),(x+min(w-2,i+12),y+max(0,i-6)),2)
            gs=pygame.Surface((w+12,h+12),pygame.SRCALPHA)
            pygame.draw.rect(gs,(*self.col,40),(0,0,w+12,h+12),border_radius=5)
            surf.blit(gs,(x-6,y-6))

# ═══════════════════════════════════════════════════════════
#  POWER-UPS
# ═══════════════════════════════════════════════════════════
PU_DEFS = {
    "shield": dict(col=CYAN,   label="SH",   msg="SHIELD!",       dur=6.0),
    "slow":   dict(col=YELLOW, label="SLO",  msg="SLOW-MO!",      dur=5.0),
    "double": dict(col=PURPLE, label="2X",   msg="DOUBLE SCORE!", dur=7.0),
    "life":   dict(col=RED,    label="♥",    msg="+LIFE!",        dur=0.0),
    "skip":   dict(col=TEAL,   label="SKIP", msg="WORD SKIP!",    dur=0.0),
    "time":   dict(col=GREEN,  label="+T",   msg="+TIME BONUS!",  dur=0.0),
}

class PowerUp:
    def __init__(self, spd):
        self.kind=random.choice(list(PU_DEFS))
        d=PU_DEFS[self.kind]
        self.col=d["col"]; self.lbl=d["label"]; self.msg=d["msg"]; self.dur=d["dur"]
        self.x=float(W+32); self.y=float(GY-70-random.randint(0,60))
        self.spd=spd; self.t=0.0
    def update(self,dt):
        self.x-=self.spd*60*dt; self.t+=dt*3
    def gone(self): return self.x+28<0
    def rect(self): return pygame.Rect(int(self.x)-22,int(self.y)-22,44,44)
    def draw(self,surf):
        bob=int(math.sin(self.t)*5); cx,cy=int(self.x),int(self.y)+bob
        if _pu_img:
            size = 44
            scaled = pygame.transform.scale(_pu_img, (size, size))
            # Spin the image
            rotated = pygame.transform.rotate(scaled, -self.t * 60)
            rw, rh = rotated.get_size()
            surf.blit(rotated, (cx - rw//2, cy - rh//2 + bob))
        else:
            gs=pygame.Surface((60,60),pygame.SRCALPHA)
            pygame.draw.circle(gs,(*self.col,55),(30,30),30); surf.blit(gs,(cx-30,cy-30))
            pygame.draw.circle(surf,self.col,(cx,cy),22)
            pygame.draw.circle(surf,WHITE,(cx,cy),22,2)
            angle=self.t*1.5
            for i in range(6):
                a=angle+i*(math.pi/3)
                rx=cx+int(28*math.cos(a)); ry=cy+int(28*math.sin(a))
                pygame.draw.circle(surf,(*self.col,120),(rx,ry),3)
        lbl=F16.render(self.lbl,True,WHITE if _pu_img else BG)
        surf.blit(lbl,(cx-lbl.get_width()//2,cy-lbl.get_height()//2 + bob))

# ═══════════════════════════════════════════════════════════
#  SCREEN SHAKE
# ═══════════════════════════════════════════════════════════
_sh_t=0.0; _sh_amp=0
def shake(amp=8, dur=0.3): global _sh_t,_sh_amp; _sh_t=dur; _sh_amp=amp
def get_offset():
    if _sh_t>0: return (random.randint(-_sh_amp,_sh_amp),random.randint(-_sh_amp,_sh_amp))
    return 0,0

# ═══════════════════════════════════════════════════════════
#  HUD HELPERS
# ═══════════════════════════════════════════════════════════
def timer_color(frac):
    if frac>0.5: return GREEN
    if frac>0.25: return YELLOW
    return RED

def draw_bar(surf, x, y, w, h, frac, col, label=""):
    pygame.draw.rect(surf,DGRAY,(x,y,w,h),border_radius=4)
    fw=int(w*max(0,frac))
    if fw>0:
        pygame.draw.rect(surf,col,(x,y,fw,h),border_radius=4)
        if frac<0.3:
            pulse=abs(math.sin(pygame.time.get_ticks()/180))
            gs=pygame.Surface((fw,h),pygame.SRCALPHA)
            gs.fill((*col,int(90*pulse))); surf.blit(gs,(x,y))
    pygame.draw.rect(surf,GRAY,(x,y,w,h),1,border_radius=4)
    if label:
        ls=F16.render(label,True,GRAY)
        surf.blit(ls,(x+w//2-ls.get_width()//2,y+h+2))

def draw_hearts(surf, lives):
    for i in range(lives):
        cx=W-26-i*34
        pygame.draw.circle(surf,RED,(cx,28),13)
        pygame.draw.circle(surf,(255,150,150),(cx,28),13,2)
        pygame.draw.circle(surf,(255,200,200),(cx-4,22),4)

def draw_hud(surf, gv):
    surf.blit(F30.render(f"Score:  {gv['score']}",True,YELLOW),(20,18))
    if gv['combo']>1:
        col=ORANGE if gv['combo']<10 else PINK
        surf.blit(F22.render(f"✦ x{gv['combo']} COMBO",True,col),(20,52))
    surf.blit(F16.render(f"Diff: {gv['diff'].upper()}",True,gv['accent']),(20,78))
    surf.blit(F16.render(f"Best: {high_score}",True,GRAY),(20,98))
    draw_hearts(surf,gv['lives'])

    # Timer bar — shows remaining time (reversed from old)
    remaining_frac = max(0, 1 - gv['timer'] / max(0.001, gv['tlimit']))
    bw=340
    draw_bar(surf,W//2-bw//2,11,bw,22,remaining_frac,timer_color(remaining_frac),"TIME")

    # Typo warning indicator
    if gv['typo_count'] > 0:
        tc = RED if gv['typo_count'] >= 2 else YELLOW
        surf.blit(F16.render(f"⚠ {gv['typo_count']} typo{'s' if gv['typo_count']>1 else ''}",True,tc),(W//2+bw//2+12,11))

    py=125
    if gv['slow']:
        surf.blit(F16.render(f"SLOW  {gv['s_t']:.1f}s",True,YELLOW),(20,py)); py+=22
    if gv['double']:
        surf.blit(F16.render(f"2X    {gv['d_t']:.1f}s",True,PURPLE),(20,py)); py+=22
    if player.shield:
        surf.blit(F16.render(f"SH    {player.sh_t:.1f}s",True,CYAN),(20,py)); py+=22

    # Typed text area
    ts=F30.render(gv['typed'] or "type here…",True,GREEN if gv['typed'] else DGRAY)
    tx=W//2-ts.get_width()//2
    surf.blit(ts,(tx,H-58))
    if gv['typed'] and int(pygame.time.get_ticks()/420)%2==0:
        cx=tx+ts.get_width()+4
        pygame.draw.rect(surf,GREEN,(cx,H-58,3,30))

# ═══════════════════════════════════════════════════════════
#  WORD DISPLAY  (letter-by-letter coloured)
# ═══════════════════════════════════════════════════════════
def draw_word(surf, word, typed, typo_count):
    letters=[]
    for i,ch in enumerate(word):
        if i < len(typed):
            col = GREEN if typed[i]==ch else RED
        else:
            col=WHITE
        letters.append(F52.render(ch,True,col))

    total=sum(l.get_width() for l in letters)
    x0=W//2-total//2; y0=H//2-120
    pad=18
    box=pygame.Surface((total+pad*2,72),pygame.SRCALPHA)
    box.fill((0,0,0,140))
    # Red border hint if typos accumulating
    border_col = (*RED, 120) if typo_count >= 2 else (*GRAY, 60)
    pygame.draw.rect(box,border_col,(0,0,total+pad*2,72),1,border_radius=6)
    surf.blit(box,(x0-pad,y0-8))
    x=x0
    for l in letters:
        surf.blit(l,(x,y0)); x+=l.get_width()

# ═══════════════════════════════════════════════════════════
#  SCREEN DRAWERS
# ═══════════════════════════════════════════════════════════
_menu_scroll=0.0

def draw_menu(surf):
    global _menu_scroll
    _menu_scroll+=2.5
    draw_bg(surf,(5,5,30),(18,12,60),(28,24,48))
    draw_road(surf,_menu_scroll,(28,24,48))

    sl=pygame.Surface((W,H),pygame.SRCALPHA)
    for y in range(0,H,4):
        pygame.draw.line(sl,(0,0,0,22),(0,y),(W,y))
    surf.blit(sl,(0,0))

    # Chromatic-aberration style title
    title=F76.render("TYPING RUNNER",True,CYAN)
    tr=F76.render("TYPING RUNNER",True,RED)
    tx=W//2-title.get_width()//2; ty=H//2-200
    tr_s=tr.copy(); tr_s.set_alpha(70)
    surf.blit(tr_s,(tx+3,ty+2))
    surf.blit(title,(tx,ty))

    sub=F22.render("— cyberpunk speed-typing adventure —",True,GRAY)
    surf.blit(sub,(W//2-sub.get_width()//2,H//2-136))
    pygame.draw.line(surf,CYAN,(W//2-220,H//2-112),(W//2+220,H//2-112),1)

    opts=[
        ("1  ·  EASY MODE",                GREEN),
        ("2  ·  NORMAL MODE",              YELLOW),
        ("3  ·  HARD MODE",                RED),
        ("S  ·  STORY MODE  (5 chapters)", CYAN),
        ("ENTER  ·  Quick Play (Normal)",  GRAY),
    ]
    for i,(txt,col) in enumerate(opts):
        s=F30.render(txt,True,col)
        bx,by=W//2-s.get_width()//2,H//2-82+i*50
        hb=pygame.Surface((s.get_width()+24,s.get_height()+6),pygame.SRCALPHA)
        hb.fill((*col,15)); surf.blit(hb,(bx-12,by-3))
        surf.blit(s,(bx,by))

    # Controls hint
    ctrl=F16.render("Controls:  Type words  ·  SPACE = jump  ·  P/ESC = pause",True,DGRAY)
    surf.blit(ctrl,(W//2-ctrl.get_width()//2,H-90))

    hs=F30.render(f"Best Score:  {high_score}",True,PURPLE)
    surf.blit(hs,(W//2-hs.get_width()//2,H-58))

def draw_story(surf, ch_idx, line_idx):
    ch=CHAPTERS[ch_idx]
    surf.fill((3,2,12))
    grid=pygame.Surface((W,H),pygame.SRCALPHA)
    for x in range(0,W,55):
        pygame.draw.line(grid,(*ch['accent'],18),(x,0),(x,H))
    surf.blit(grid,(0,0))
    title=F52.render(ch['title'],True,ch['accent'])
    surf.blit(title,(W//2-title.get_width()//2,65))
    pygame.draw.line(surf,ch['accent'],(W//2-240,120),(W//2+240,120),2)
    for i,line in enumerate(ch['lines']):
        if i<=line_idx:
            ls=F30.render(line,True,WHITE)
            surf.blit(ls,(W//2-ls.get_width()//2,160+i*65))
    hint=F16.render("SPACE — continue   |   ESC — back to menu",True,GRAY)
    surf.blit(hint,(W//2-hint.get_width()//2,H-55))

def draw_between(surf, gv, ch_idx):
    ch=CHAPTERS[ch_idx]
    surf.fill((2,12,4))
    t=F76.render("CHAPTER CLEAR!",True,GREEN)
    surf.blit(t,(W//2-t.get_width()//2,H//2-170))
    pygame.draw.line(surf,GREEN,(W//2-260,H//2-95),(W//2+260,H//2-95),2)
    rows=[
        (f"Score:      {gv['score']}  /  Target: {ch['target']}",YELLOW),
        (f"Max Combo:  {gv['max_combo']}",CYAN),
        (f"Lives Left: {gv['lives']}",RED),
    ]
    for i,(txt,col) in enumerate(rows):
        s=F30.render(txt,True,col)
        surf.blit(s,(W//2-s.get_width()//2,H//2-40+i*50))
    if ch_idx+1<len(CHAPTERS):
        nxt=F22.render(f"Next: {CHAPTERS[ch_idx+1]['title']}",True,ch['accent'])
        surf.blit(nxt,(W//2-nxt.get_width()//2,H//2+120))
    hint=F16.render("ENTER — continue",True,GRAY)
    surf.blit(hint,(W//2-hint.get_width()//2,H-55))

def draw_pause(surf):
    ov=pygame.Surface((W,H),pygame.SRCALPHA); ov.fill((0,0,0,175))
    surf.blit(ov,(0,0))
    t=F76.render("PAUSED",True,CYAN)
    surf.blit(t,(W//2-t.get_width()//2,H//2-110))
    pygame.draw.line(surf,CYAN,(W//2-180,H//2-30),(W//2+180,H//2-30),1)
    for i,(txt,col) in enumerate([
        ("ESC / P  —  Resume",       WHITE),
        ("Q        —  Quit to Menu", RED),
    ]):
        s=F30.render(txt,True,col)
        surf.blit(s,(W//2-s.get_width()//2,H//2+10+i*52))

def draw_gameover(surf, gv):
    surf.fill((10,2,2))
    sl=pygame.Surface((W,H),pygame.SRCALPHA)
    for y in range(0,H,3): pygame.draw.line(sl,(255,0,0,10),(0,y),(W,y))
    surf.blit(sl,(0,0))
    t=F76.render("GAME  OVER",True,RED)
    surf.blit(t,(W//2-t.get_width()//2,H//2-180))
    pygame.draw.line(surf,RED,(W//2-260,H//2-100),(W//2+260,H//2-100),2)
    new_hs=gv['score']>0 and gv['score']>=high_score
    rows=[
        (f"Score:      {gv['score']}",   YELLOW if new_hs else WHITE),
        (f"Max Combo:  {gv['max_combo']}",CYAN),
        (f"Best:       {high_score}",    PURPLE),
    ]
    for i,(txt,col) in enumerate(rows):
        s=F30.render(txt,True,col)
        surf.blit(s,(W//2-s.get_width()//2,H//2-45+i*52))
    if new_hs:
        n=F30.render("✦ NEW HIGH SCORE! ✦",True,YELLOW)
        surf.blit(n,(W//2-n.get_width()//2,H//2+118))
    hint=F16.render("ENTER — Main Menu",True,GRAY)
    surf.blit(hint,(W//2-hint.get_width()//2,H-55))

# ═══════════════════════════════════════════════════════════
#  GAME STATE
# ═══════════════════════════════════════════════════════════
MENU_S="menu"; STORY_S="story"; PLAY_S="play"
PAUSE_S="pause"; BETWEEN_S="between"; OVER_S="over"

state     = MENU_S
mode      = "free"
story_ch  = 0
story_line= 0

# ─────────────────────────────────────────────────────────
#  DIFFICULTY SETTINGS  (much more forgiving than before)
# ─────────────────────────────────────────────────────────
DIFF_CFG = {
    "easy":   dict(tlimit=6.0, tlimit_min=3.5, tlimit_dec=0.05, speed=2.2, lives=5, obs_iv=3.5),
    "normal": dict(tlimit=5.0, tlimit_min=2.5, tlimit_dec=0.08, speed=2.7, lives=4, obs_iv=2.8),
    "hard":   dict(tlimit=4.0, tlimit_min=2.0, tlimit_dec=0.11, speed=3.2, lives=3, obs_iv=2.2),
}

def new_gv(diff="normal", ch=None, accent=CYAN,
           sky_top=(5,5,30), sky_bot=(18,12,60), gnd=(28,24,48)):
    cfg = DIFF_CFG[diff]
    return dict(
        diff=diff, ch=ch,
        accent=accent, sky_top=sky_top, sky_bot=sky_bot, gnd=gnd,
        word=pick(diff), typed="",
        score=0, combo=0, max_combo=0,
        speed=cfg['speed'], lives=cfg['lives'],
        timer=0.0, tlimit=cfg['tlimit'],
        tlimit_min=cfg['tlimit_min'], tlimit_dec=cfg['tlimit_dec'],
        double=False, d_t=0.0,
        slow=False,   s_t=0.0,
        obs=[], pus=[],
        obs_t=0.0, obs_iv=cfg['obs_iv'],
        pu_t=0.0,  pu_iv=9.0,
        grace=0.0,        # grace period after new word (no timer damage)
        typo_count=0,     # typos on current word before penalty
        typo_tolerance=2, # allowed typos before life loss penalty
    )

gv = new_gv()

def start_game(diff="normal", ch=None):
    global gv, player, particles, floats, _sh_t, road_scroll
    extra={}
    if ch is not None and ch < len(CHAPTERS):
        c=CHAPTERS[ch]
        extra=dict(accent=c['accent'],sky_top=c['sky_top'],sky_bot=c['sky_bot'],gnd=c['gnd'])
    gv=new_gv(diff, ch, **extra)
    player=Player(); particles=[]; floats=[]; _sh_t=0

# ─── gameplay events ─────────────────────────────────────
def lose_life():
    global state
    gv['lives']-=1; gv['combo']=0; gv['typed']=""
    gv['word']=pick(gv['diff']); gv['timer']=0.0
    gv['typo_count']=0; gv['grace']=0.6
    shake(14,0.45); player.flash=0.65; sfx(SND_HIT)
    ring_burst(player.cx, player.foot_y-SPRITE_H//2, RED, 16)
    if gv['lives']<=0:
        global high_score
        if gv['score']>high_score:
            high_score=gv['score']; save_hs(high_score)
        state=OVER_S

def word_correct():
    global state
    pts=max(1,1+gv['combo']//5)*(2 if gv['double'] else 1)
    gv['score']+=pts; gv['combo']+=1
    gv['max_combo']=max(gv['max_combo'],gv['combo'])
    gv['speed']=min(10.0, gv['speed']+0.12)

    # Time bonus for clean words (no typos)
    if gv['typo_count']==0:
        gv['timer']=max(0.0, gv['timer']-0.4)  # small time reward

    d=gv['diff']
    gv['tlimit']=max(gv['tlimit_min'], gv['tlimit']-gv['tlimit_dec'])
    gv['typed']=""; gv['word']=pick(d); gv['timer']=0.0
    gv['typo_count']=0; gv['grace']=0.25  # brief grace on new word

    combo_milestone=gv['combo']%5==0 and gv['combo']>0
    sfx(SND_COMBO if combo_milestone else SND_OK)
    ring_burst(W//2, H//2-90, GREEN if not combo_milestone else YELLOW)
    burst(W//2, H//2-60, GREEN, 18)

    label=f"+{pts}"+("  COMBO!" if combo_milestone else "")
    floats.append(FloatText(W//2,H//2-130,label,YELLOW,big=combo_milestone))

    ch=gv.get('ch')
    if ch is not None and ch<len(CHAPTERS):
        if gv['score']>=CHAPTERS[ch]['target']:
            sfx(SND_LEVEL); state=BETWEEN_S

def apply_pu(pu):
    if pu.kind=="shield":  player.shield=True; player.sh_t=pu.dur
    elif pu.kind=="slow":  gv['slow']=True; gv['s_t']=pu.dur
    elif pu.kind=="double":gv['double']=True; gv['d_t']=pu.dur
    elif pu.kind=="life":  gv['lives']=min(5,gv['lives']+1)
    elif pu.kind=="skip":
        gv['typed']=""; gv['word']=pick(gv['diff']); gv['timer']=0.0; gv['typo_count']=0; gv['grace']=0.3
    elif pu.kind=="time":
        gv['timer']=max(0, gv['timer']-1.5)
    floats.append(FloatText(player.cx,player.foot_y-90,pu.msg,pu.col,big=True))
    sfx(SND_PU); burst(player.cx,player.foot_y-SPRITE_H//2,pu.col,20)

# ═══════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════
running=True
while running:
    raw_dt=clock.tick(FPS)/1000; dt=min(raw_dt,0.05)

    if _sh_t>0: _sh_t-=dt
    ox,oy=get_offset()
    canvas=pygame.Surface((W,H))

    # ── EVENTS ──────────────────────────────────────────────
    for ev in pygame.event.get():
        if ev.type==pygame.QUIT: running=False

        elif ev.type==pygame.KEYDOWN:

            if state==MENU_S:
                if   ev.key==pygame.K_1: start_game("easy");  mode="free"; state=PLAY_S
                elif ev.key==pygame.K_2: start_game("normal");mode="free"; state=PLAY_S
                elif ev.key==pygame.K_3: start_game("hard");  mode="free"; state=PLAY_S
                elif ev.key==pygame.K_s: story_ch=0;story_line=0;mode="story";state=STORY_S
                elif ev.key==pygame.K_RETURN: start_game("normal");mode="free";state=PLAY_S

            elif state==STORY_S:
                if ev.key==pygame.K_ESCAPE: state=MENU_S
                elif ev.key==pygame.K_SPACE:
                    ch=CHAPTERS[story_ch]
                    if story_line<len(ch['lines'])-1:
                        story_line+=1
                    else:
                        start_game(ch['diff'],ch=story_ch); state=PLAY_S

            elif state==PLAY_S:
                if ev.key==pygame.K_ESCAPE: state=PAUSE_S
                elif ev.key==pygame.K_SPACE: player.jump()
                elif ev.key==pygame.K_BACKSPACE:
                    gv['typed']=gv['typed'][:-1]
                else:
                    ch=ev.unicode
                    if ch and ch.isprintable() and len(gv['typed'])<len(gv['word']):
                        gv['typed']+=ch
                        pos=len(gv['typed'])-1
                        if gv['typed'][pos]!=gv['word'][pos]:
                            gv['typo_count']+=1
                            sfx(SND_TYPO)
                            shake(3,0.08)
                            # Only lose life after exceeding tolerance
                            if gv['typo_count']>gv['typo_tolerance']:
                                sfx(SND_FAIL)
                                shake(8,0.2)
                                lose_life()

            elif state==PAUSE_S:
                if ev.key in (pygame.K_ESCAPE, pygame.K_p): state=PLAY_S
                elif ev.key==pygame.K_q: state=MENU_S

            elif state==BETWEEN_S:
                if ev.key==pygame.K_RETURN:
                    story_ch+=1
                    if story_ch>=len(CHAPTERS): state=OVER_S
                    else: story_line=0; state=STORY_S

            elif state==OVER_S:
                if ev.key==pygame.K_RETURN: state=MENU_S

    # ── DRAW / UPDATE ────────────────────────────────────────
    if state==MENU_S:
        draw_menu(canvas)

    elif state==STORY_S:
        draw_story(canvas,story_ch,story_line)

    elif state==PLAY_S:
        sm=0.5 if gv['slow'] else 1.0
        draw_bg(canvas,gv['sky_top'],gv['sky_bot'],gv['gnd'])
        road_scroll+=gv['speed']*5*sm
        draw_road(canvas,road_scroll,gv['gnd'])

        # Spawn obstacles
        gv['obs_t']+=dt
        if gv['obs_t']>=gv['obs_iv']:
            gv['obs_t']=0; gv['obs_iv']=max(0.9,gv['obs_iv']-0.045)
            gv['obs'].append(Obstacle(gv['speed']))

        # Spawn power-ups
        gv['pu_t']+=dt
        if gv['pu_t']>=gv['pu_iv']:
            gv['pu_t']=0; gv['pus'].append(PowerUp(gv['speed']))

        # Update obstacles
        prect=player.rect()
        for ob in gv['obs'][:]:
            ob.spd=gv['speed']*sm; ob.update(dt); ob.draw(canvas)
            if ob.gone(): gv['obs'].remove(ob)
            elif not player.shield and prect.colliderect(ob.rect()):
                gv['obs'].remove(ob); lose_life(); break

        # Update power-ups
        for pu in gv['pus'][:]:
            pu.spd=gv['speed']*sm; pu.update(dt); pu.draw(canvas)
            if pu.gone(): gv['pus'].remove(pu)
            elif prect.colliderect(pu.rect()):
                apply_pu(pu); gv['pus'].remove(pu)

        # Power-up timers
        if gv['slow']:
            gv['s_t']-=dt
            if gv['s_t']<=0: gv['slow']=False
        if gv['double']:
            gv['d_t']-=dt
            if gv['d_t']<=0: gv['double']=False

        player.update(dt); player.draw(canvas)

        # Grace period countdown
        if gv['grace']>0: gv['grace']-=dt
        else:
            gv['timer']+=dt*sm
            if gv['timer']>=gv['tlimit']:
                lose_life()

        if state==PLAY_S:
            draw_word(canvas,gv['word'],gv['typed'],gv['typo_count'])
            if gv['typed']==gv['word']:
                word_correct()

        # Particles & floats
        for p in particles[:]:
            p.update(dt); p.draw(canvas)
            if p.life<=0: particles.remove(p)
        for ft in floats[:]:
            ft.update(dt); ft.draw(canvas)
            if ft.life<=0: floats.remove(ft)

        if state==PLAY_S:
            draw_hud(canvas,gv)

    elif state==PAUSE_S:
        draw_bg(canvas,gv['sky_top'],gv['sky_bot'],gv['gnd'])
        draw_road(canvas,road_scroll,gv['gnd']); player.draw(canvas)
        draw_hud(canvas,gv); draw_pause(canvas)

    elif state==BETWEEN_S:
        draw_between(canvas,gv,story_ch)

    elif state==OVER_S:
        draw_gameover(canvas,gv)

    # ── BLIT WITH SHAKE ─────────────────────────────────────
    screen.fill(BG); screen.blit(canvas,(ox,oy)); pygame.display.flip()

pygame.quit()
sys.exit()

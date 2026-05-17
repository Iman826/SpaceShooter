import pygame
from random import randint, uniform
import sys
import math

# ─── Setup ─────────────────────────────────────────────────────
pygame.init()

WINDOW_WIDTH  = 1280
WINDOW_HEIGHT = 720

display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Space Shooter")

clock = pygame.time.Clock()

# ─── Colors ────────────────────────────────────────────────────
WHITE     = (255, 255, 255)
RED       = (220, 50,  50)
GREEN     = (80,  220, 100)
YELLOW    = (255, 220, 0)
CYAN      = (0,   220, 255)
DARKGRAY  = (8,   8,   22)
ORANGE    = (255, 140, 0)
PURPLE    = (180, 60,  255)
PINK      = (255, 80,  180)
GOLD      = (255, 200, 0)
HEART_RED = (255, 60,  80)
STEEL     = (160, 180, 200)
DARKSTEEL = (80,  100, 120)
LIGHTBLUE = (120, 180, 255)
EXHAUST   = (100, 180, 255)

# ─── Fonts ─────────────────────────────────────────────────────
pygame.font.init()
FONT_NAMES = ["Courier New", "Courier", "Lucida Console", "Consolas", "monospace"]
def get_font(size, bold=False):
    for name in FONT_NAMES:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f: return f
        except: pass
    return pygame.font.SysFont(None, size, bold=bold)

font_large = get_font(54, bold=True)
font_med   = get_font(26, bold=True)
font_small = get_font(19)
font_tiny  = get_font(15)
font_score = get_font(32, bold=True)

# ─── Level config ──────────────────────────────────────────────
LEVEL_CONFIG = {
    1: {"name":"ROOKIE",    "color":GREEN,  "enemies_total":10, "spawn_interval":50, "speed_y":(1.2,2.0), "speed_x":(-0.6,0.6), "enemy_hp":1, "bullet_speed":4, "shoot_delay":100,"score_mul":1},
    2: {"name":"SOLDIER",   "color":CYAN,   "enemies_total":18, "spawn_interval":40, "speed_y":(2.0,3.2), "speed_x":(-1.2,1.2), "enemy_hp":2, "bullet_speed":6, "shoot_delay":75, "score_mul":2},
    3: {"name":"WARRIOR",   "color":YELLOW, "enemies_total":28, "spawn_interval":30, "speed_y":(3.0,4.5), "speed_x":(-1.8,1.8), "enemy_hp":3, "bullet_speed":7, "shoot_delay":55, "score_mul":3},
    4: {"name":"COMMANDER", "color":ORANGE, "enemies_total":40, "spawn_interval":22, "speed_y":(4.0,6.0), "speed_x":(-2.5,2.5), "enemy_hp":4, "bullet_speed":9, "shoot_delay":40, "score_mul":4},
    5: {"name":"LEGEND",    "color":PURPLE, "enemies_total":55, "spawn_interval":15, "speed_y":(5.5,8.0), "speed_x":(-3.5,3.5), "enemy_hp":5, "bullet_speed":11,"shoot_delay":28, "score_mul":5},
}
MAX_LEVEL = 5

# ─── Draw text ─────────────────────────────────────────────────
def draw_text(surface, text, font, color, x, y, center=False):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(x,y)) if center else surf.get_rect(topleft=(x,y))
    surface.blit(surf, rect)

# ─── Stars ─────────────────────────────────────────────────────
star_position = [(randint(0,WINDOW_WIDTH), randint(0,WINDOW_HEIGHT)) for _ in range(140)]
star_sizes    = [randint(1,3) for _ in range(140)]
star_twinkle  = [randint(0,60) for _ in range(140)]

def update_stars(speed=1):
    global star_position
    star_position = [(sx,(sy+speed)%WINDOW_HEIGHT) for sx,sy in star_position]

def draw_stars(surface, t=0):
    for i,(sx,sy) in enumerate(star_position):
        r   = star_sizes[i]
        tw  = abs(math.sin((t+star_twinkle[i])*0.05))
        alp = int(120 + 135*tw)
        col = (alp,alp,min(255,alp+30))
        pygame.draw.circle(surface, col, (sx,sy), r)

# ─── Particles ─────────────────────────────────────────────────
particles = []

def spawn_explosion(x, y, color=ORANGE, count=20):
    for _ in range(count):
        angle = uniform(0,360)
        speed = uniform(2,7)
        v     = pygame.math.Vector2(speed,0).rotate(angle)
        particles.append([float(x),float(y),v.x,v.y,randint(20,45),list(color)])

def update_particles(surface):
    for p in particles[:]:
        p[0]+=p[2]; p[1]+=p[3]; p[4]-=1
        p[2]*=0.91; p[3]*=0.91
        if p[4]<=0: particles.remove(p); continue
        radius = max(2,int(p[4]/6))
        pygame.draw.circle(surface,tuple(p[5]),(int(p[0]),int(p[1])),radius)

# ─── Score popups ──────────────────────────────────────────────
score_popups = []

def add_score_popup(x, y, pts, color):
    score_popups.append([float(x), float(y), f"+{pts}", color, 45])

def update_score_popups(surface):
    for p in score_popups[:]:
        p[4] -= 1
        p[1] -= 1.0
        if p[4] <= 0: score_popups.remove(p); continue
        draw_text(surface, p[2], font_small, p[3], int(p[0]), int(p[1]), center=True)

# ─── SPACESHIP (player) with astronaut inside ──────────────────
def draw_spaceship(surface, x, y, t=0, tilt=0):
    # Engine glow / exhaust
    flame_h = 18 + int(math.sin(t*0.4)*6)
    for fi in range(4):
        fw  = 14 - fi*3
        fh  = flame_h - fi*3
        fy  = y + 28 + fi*3
        fc  = [ORANGE, YELLOW, WHITE, CYAN][fi]
        if fw > 0 and fh > 0:
            pygame.draw.ellipse(surface, fc, (x-fw//2+tilt, fy, fw, fh))

    # Side boosters
    for sx_off in [-18, 18]:
        bfh = 10 + int(math.sin(t*0.4+1)*3)
        pygame.draw.ellipse(surface, ORANGE, (x+sx_off-4+tilt, y+20, 8, bfh))
        pygame.draw.ellipse(surface, YELLOW, (x+sx_off-3+tilt, y+20, 6, bfh-3))

    # Main body — sleek fuselage
    body_pts = [
        (x+tilt,     y-38),   # nose tip
        (x+14+tilt,  y-10),   # right shoulder
        (x+18+tilt,  y+10),   # right side
        (x+16+tilt,  y+28),   # right tail
        (x-16+tilt,  y+28),   # left tail
        (x-18+tilt,  y+10),   # left side
        (x-14+tilt,  y-10),   # left shoulder
    ]
    pygame.draw.polygon(surface, STEEL, body_pts)
    pygame.draw.polygon(surface, LIGHTBLUE, body_pts, 2)

    # Body panel lines
    pygame.draw.line(surface, DARKSTEEL, (x+tilt, y-35), (x+tilt, y+25), 1)
    pygame.draw.line(surface, DARKSTEEL, (x+8+tilt, y-5), (x+8+tilt, y+20), 1)
    pygame.draw.line(surface, DARKSTEEL, (x-8+tilt, y-5), (x-8+tilt, y+20), 1)

    # Wings
    lwing = [(x-14+tilt, y+5), (x-34+tilt, y+22), (x-28+tilt, y+28), (x-14+tilt, y+18)]
    rwing = [(x+14+tilt, y+5), (x+34+tilt, y+22), (x+28+tilt, y+28), (x+14+tilt, y+18)]
    pygame.draw.polygon(surface, DARKSTEEL, lwing)
    pygame.draw.polygon(surface, LIGHTBLUE, lwing, 1)
    pygame.draw.polygon(surface, DARKSTEEL, rwing)
    pygame.draw.polygon(surface, LIGHTBLUE, rwing, 1)

    # Cockpit bubble — astronaut inside
    pygame.draw.ellipse(surface, (20,50,100),   (x-12+tilt, y-32, 24, 22))  # dark bg
    pygame.draw.ellipse(surface, LIGHTBLUE,     (x-12+tilt, y-32, 24, 22), 2)
    # Shine on cockpit
    pygame.draw.ellipse(surface, (180,220,255), (x-9+tilt,  y-30, 10, 7))

    # Tiny astronaut visible in cockpit
    # Helmet
    pygame.draw.circle(surface, WHITE,      (x+tilt, y-23), 7)
    pygame.draw.circle(surface, (30,60,140),(x+tilt, y-24), 5)   # visor
    pygame.draw.circle(surface, (180,220,255),(x-2+tilt, y-26), 2)  # shine
    # Eyes
    pygame.draw.circle(surface, WHITE, (x-2+tilt, y-23), 1)
    pygame.draw.circle(surface, WHITE, (x+2+tilt, y-23), 1)

    # Nose cone tip glow
    pygame.draw.circle(surface, CYAN, (x+tilt, y-38), 3)

    # Wing tip lights
    pygame.draw.circle(surface, RED,  (x-33+tilt, y+22), 3)
    pygame.draw.circle(surface, GREEN,(x+33+tilt, y+22), 3)

# ─── FIGHTER JET enemy ─────────────────────────────────────────
def draw_fighter_jet(surface, x, y, color, t=0, tilt=0):
    # Exhaust
    exhaust_h = 10 + int(math.sin(t*0.5)*4)
    pygame.draw.ellipse(surface, color,  (x-5+tilt, y-30, 10, exhaust_h))
    pygame.draw.ellipse(surface, WHITE,  (x-3+tilt, y-30, 6,  exhaust_h-4))

    # Fuselage (pointing DOWN — enemy comes from top)
    body_pts = [
        (x+tilt,     y+30),   # nose (bottom)
        (x+10+tilt,  y+8),
        (x+12+tilt,  y-10),
        (x+10+tilt,  y-22),
        (x-10+tilt,  y-22),
        (x-12+tilt,  y-10),
        (x-10+tilt,  y+8),
    ]
    # Dark body with level color accent
    dark_col = (max(0,color[0]-80), max(0,color[1]-80), max(0,color[2]-80))
    pygame.draw.polygon(surface, dark_col, body_pts)
    pygame.draw.polygon(surface, color,    body_pts, 2)

    # Center stripe
    pygame.draw.line(surface, color, (x+tilt, y+28), (x+tilt, y-20), 1)

    # Wings (swept back)
    lwing = [
        (x-10+tilt, y+0),
        (x-32+tilt, y+18),
        (x-30+tilt, y+26),
        (x-14+tilt, y+16),
    ]
    rwing = [
        (x+10+tilt, y+0),
        (x+32+tilt, y+18),
        (x+30+tilt, y+26),
        (x+14+tilt, y+16),
    ]
    pygame.draw.polygon(surface, dark_col, lwing)
    pygame.draw.polygon(surface, color,    lwing, 2)
    pygame.draw.polygon(surface, dark_col, rwing)
    pygame.draw.polygon(surface, color,    rwing, 2)

    # Tail fins
    ltail = [(x-8+tilt, y-18), (x-18+tilt, y-28), (x-8+tilt, y-26)]
    rtail = [(x+8+tilt, y-18), (x+18+tilt, y-28), (x+8+tilt, y-26)]
    pygame.draw.polygon(surface, dark_col, ltail)
    pygame.draw.polygon(surface, color,    ltail, 1)
    pygame.draw.polygon(surface, dark_col, rtail)
    pygame.draw.polygon(surface, color,    rtail, 1)

    # Cockpit (enemy pilot)
    pygame.draw.ellipse(surface, (20,20,50),  (x-8+tilt, y+8, 16, 14))
    pygame.draw.ellipse(surface, color,       (x-8+tilt, y+8, 16, 14), 1)
    # Tiny evil eyes
    pygame.draw.circle(surface, RED, (x-3+tilt, y+14), 2)
    pygame.draw.circle(surface, RED, (x+3+tilt, y+14), 2)

    # Wing cannons
    pygame.draw.rect(surface, DARKSTEEL, (x-30+tilt, y+10, 14, 4), border_radius=2)
    pygame.draw.rect(surface, DARKSTEEL, (x+16+tilt, y+10, 14, 4), border_radius=2)

    # Afterburner glow
    pygame.draw.circle(surface, color, (x-30+tilt, y+12), 3)
    pygame.draw.circle(surface, color, (x+30+tilt, y+12), 3)

    # HP bar
    pass  # drawn in Enemy.draw()

# ─── Heart ─────────────────────────────────────────────────────
def draw_heart(surface, cx, cy, size=14, filled=True):
    col = HEART_RED if filled else (50,50,70)
    r   = size//2
    pygame.draw.circle(surface, col, (cx-r//2, cy-r//3), r//2+2)
    pygame.draw.circle(surface, col, (cx+r//2, cy-r//3), r//2+2)
    pts = [(cx-r, cy-r//3), (cx+r, cy-r//3), (cx, cy+r)]
    pygame.draw.polygon(surface, col, pts)
    if filled:
        pygame.draw.circle(surface, (255,160,180),(cx-r//2+1,cy-r//3-1),r//4)

# ─── Player ────────────────────────────────────────────────────
class Player:
    def __init__(self):
        self.x           = float(WINDOW_WIDTH//2)
        self.y           = float(WINDOW_HEIGHT - 100)
        self.speed       = 7
        self.health      = 3
        self.shoot_cd    = 0
        self.shoot_delay = 12
        self.invincible  = 0
        self.t           = 0
        self.tilt        = 0
        self.rect        = pygame.Rect(0,0,36,60)

    def update(self, keys):
        moving_left  = keys[pygame.K_LEFT]  or keys[pygame.K_a]
        moving_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]

        if moving_left:  self.x -= self.speed
        if moving_right: self.x += self.speed
        if keys[pygame.K_UP]   or keys[pygame.K_w]: self.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: self.y += self.speed

        # Smooth tilt when turning
        target_tilt = -5 if moving_left else (5 if moving_right else 0)
        self.tilt  += (target_tilt - self.tilt) * 0.2

        self.x = max(40, min(WINDOW_WIDTH-40, self.x))
        self.y = max(40, min(WINDOW_HEIGHT-40, self.y))
        self.rect = pygame.Rect(int(self.x)-16, int(self.y)-30, 32, 58)

        if self.shoot_cd   > 0: self.shoot_cd   -= 1
        if self.invincible > 0: self.invincible  -= 1
        self.t += 1

    def shoot(self):
        if self.shoot_cd == 0:
            self.shoot_cd = self.shoot_delay
            # Twin cannons
            b1 = Bullet(int(self.x)-10, int(self.y)-35, -17, CYAN,   player=True)
            b2 = Bullet(int(self.x)+10, int(self.y)-35, -17, LIGHTBLUE, player=True)
            return [b1, b2]
        return []

    def draw(self, surface):
        if self.invincible % 4 < 2:
            draw_spaceship(surface, int(self.x), int(self.y), self.t, int(self.tilt))

    def hit(self):
        if self.invincible == 0:
            self.health    -= 1
            self.invincible = 70
            spawn_explosion(self.x, self.y, RED, 14)
            return True
        return False

# ─── Bullet ────────────────────────────────────────────────────
class Bullet:
    def __init__(self, x, y, speed, color, player=False):
        w = 6 if player else 8
        h = 22 if player else 16
        self.rect   = pygame.Rect(x-w//2, y-h//2, w, h)
        self.speed  = speed
        self.color  = color
        self.player = player
        self.t      = 0

    def update(self):
        self.rect.y += self.speed
        self.t      += 1

    def draw(self, surface):
        cx = self.rect.centerx
        cy = self.rect.centery
        # Glow core
        pygame.draw.ellipse(surface, self.color, self.rect)
        pygame.draw.ellipse(surface, WHITE, self.rect, 1)
        # Trail
        for i in range(1,5):
            trail_y = cy + i*5 if self.speed < 0 else cy - i*5
            a = max(0, 160-i*38)
            ts = pygame.Surface((5,4), pygame.SRCALPHA)
            pygame.draw.ellipse(ts, (*self.color[:3],a),(0,0,5,4))
            surface.blit(ts,(cx-2, trail_y))

    def off_screen(self):
        return self.rect.bottom < 0 or self.rect.top > WINDOW_HEIGHT

# ─── Enemy (fighter jet) ───────────────────────────────────────
class Enemy:
    def __init__(self, cfg, level_color):
        self.x        = float(randint(50, WINDOW_WIDTH-50))
        self.y        = float(-80)
        self.speed_y  = uniform(*cfg["speed_y"])
        self.speed_x  = uniform(*cfg["speed_x"])
        self.health   = cfg["enemy_hp"]
        self.max_hp   = self.health
        self.shoot_cd = randint(0, max(1, cfg["shoot_delay"] - 30)) + 30
        self.shoot_delay = cfg["shoot_delay"]
        self.bspeed   = cfg["bullet_speed"]
        self.color    = level_color
        self.t        = randint(0,60)
        self.tilt     = 0
        self.bob      = uniform(0,360)
        self.rect     = pygame.Rect(0,0,44,56)

    def update(self):
        prev_x = self.x
        self.x += self.speed_x
        self.y += self.speed_y

        # Tilt when turning
        dx = self.x - prev_x
        self.tilt += (dx*2 - self.tilt)*0.15

        if self.x < 50 or self.x > WINDOW_WIDTH-50:
            self.speed_x *= -1

        self.rect = pygame.Rect(int(self.x)-22, int(self.y)-20, 44, 56)
        self.t   += 1
        if self.shoot_cd > 0: self.shoot_cd -= 1

    def shoot(self):
        if self.shoot_cd == 0:
            self.shoot_cd = self.shoot_delay
            return Bullet(int(self.x), int(self.y)+32, self.bspeed, RED, player=False)
        return None

    def draw(self, surface):
        draw_fighter_jet(surface, int(self.x), int(self.y), self.color, self.t, int(self.tilt))
        # HP bar above jet
        if self.max_hp > 1:
            bw     = 44
            filled = int(bw * self.health / self.max_hp)
            pygame.draw.rect(surface,(60,0,0),(int(self.x)-22,int(self.y)-38,bw,5),border_radius=2)
            pygame.draw.rect(surface,self.color,(int(self.x)-22,int(self.y)-38,filled,5),border_radius=2)

    def off_screen(self):
        return self.y > WINDOW_HEIGHT + 60

# ─── HUD ───────────────────────────────────────────────────────
def draw_hud(surface, score, level, killed, total, t, player_health):
    cfg    = LEVEL_CONFIG[level]
    lcolor = cfg["color"]

    # Score
    score_surf = font_score.render(f"SCORE  {score}", True, WHITE)
    surface.blit(score_surf, (15,10))

    # Level
    draw_text(surface, f"LV{level}  {cfg['name']}", font_med, lcolor, 15, 50)

    # Bottom progress bar
    bar_x,bar_y,bar_w,bar_h = 0, WINDOW_HEIGHT-20, WINDOW_WIDTH, 20
    prog   = killed/total if total>0 else 0
    fill_w = int(bar_w*prog)

    pygame.draw.rect(surface,(15,15,30),(bar_x,bar_y,bar_w,bar_h))
    if fill_w > 0:
        pygame.draw.rect(surface, lcolor, (bar_x,bar_y,fill_w,bar_h))
        # Shimmer
        sx = (t*4)%fill_w if fill_w>2 else 0
        ss = pygame.Surface((50,bar_h), pygame.SRCALPHA)
        ss.fill((255,255,255,35))
        surface.blit(ss,(bar_x+sx, bar_y))

    pygame.draw.rect(surface,(60,60,90),(bar_x,bar_y,bar_w,bar_h),1)

    # Bar text
    kt = font_tiny.render(f"{killed} / {total}  jets down", True, WHITE)
    surface.blit(kt,(bar_x+bar_w//2-kt.get_width()//2, bar_y+3))
    pt = font_tiny.render(f"{int(prog*100)}%", True, WHITE)
    surface.blit(pt,(bar_x+bar_w-pt.get_width()-8, bar_y+3))

    # Jet icon on bar progress edge
    if 0 < fill_w < bar_w:
        pygame.draw.polygon(surface, WHITE, [
            (bar_x+fill_w, bar_y+10),
            (bar_x+fill_w-8, bar_y+3),
            (bar_x+fill_w-8, bar_y+17),
        ])

    # Hearts
    for i in range(3):
        draw_heart(surface, WINDOW_WIDTH-28-i*38, 52, size=24, filled=i < player_health)

    # Level dots
    for i in range(MAX_LEVEL):
        col = LEVEL_CONFIG[i+1]["color"] if i+1 <= level else (35,35,55)
        rx  = WINDOW_WIDTH-16-i*28
        ry  = 18
        pygame.draw.circle(surface, col, (rx,ry), 8)
        if i+1 < level:
            pygame.draw.circle(surface, WHITE,(rx,ry),8,2)
        elif i+1 == level:
            pulse = int(2+math.sin(t*0.1)*2)
            pygame.draw.circle(surface, WHITE,(rx,ry),8+pulse,2)

# ─── Screens ───────────────────────────────────────────────────
def start_screen():
    t = 0
    while True:
        display_surface.fill(DARKGRAY)
        update_stars(1)
        draw_stars(display_surface, t)

        # Demo spaceship
        bob = int(math.sin(t*0.04)*14)
        draw_spaceship(display_surface, WINDOW_WIDTH//2-180, 320+bob, t, int(math.sin(t*0.04)*4))

        # Demo enemy jet
        draw_fighter_jet(display_surface, WINDOW_WIDTH//2+180, 310-bob, GREEN, t, int(math.sin(t*0.04)*-3))

        draw_text(display_surface, "SPACE SHOOTER",          font_large, CYAN,   WINDOW_WIDTH//2, 115, center=True)
        draw_text(display_surface, "5 LEVELS  |  SURVIVE ALL", font_small, YELLOW, WINDOW_WIDTH//2, 178, center=True)

        for i,(lvl,cfg) in enumerate(LEVEL_CONFIG.items()):
            draw_text(display_surface,
                f"Lv{lvl}  {cfg['name']}  —  {cfg['enemies_total']} fighters",
                font_tiny, cfg["color"], WINDOW_WIDTH//2, 222+i*22, center=True)

        draw_text(display_surface, "WASD / Arrows = Move     SPACE = Shoot", font_small, WHITE, WINDOW_WIDTH//2, 355, center=True)
        draw_text(display_surface, "[ ENTER TO START ]", font_med, GREEN, WINDOW_WIDTH//2, 402, center=True)

        if (t//30) % 2 == 0:
            draw_text(display_surface, "▼", font_small, GREEN, WINDOW_WIDTH//2, 438, center=True)

        pygame.display.update()
        clock.tick(60)
        t += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN: return

def level_banner(level):
    cfg   = LEVEL_CONFIG[level]
    color = cfg["color"]
    for frame in range(120):
        display_surface.fill(DARKGRAY)
        update_stars(2+level)
        draw_stars(display_surface, frame)

        # Flying jet on banner
        jx = int(WINDOW_WIDTH//2 + math.sin(frame*0.08)*180)
        draw_fighter_jet(display_surface, jx, WINDOW_HEIGHT//2+80, color, frame)

        scale = 1.0 + 0.05*abs((frame%30)-15)/15
        txt   = font_large.render(f"LEVEL  {level}", True, color)
        txt   = pygame.transform.rotozoom(txt, 0, scale)
        rect  = txt.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2-40))
        display_surface.blit(txt, rect)

        draw_text(display_surface, cfg["name"],                    font_med,   WHITE,  WINDOW_WIDTH//2, WINDOW_HEIGHT//2+22, center=True)
        draw_text(display_surface, f"{cfg['enemies_total']} fighters incoming!", font_small, YELLOW, WINDOW_WIDTH//2, WINDOW_HEIGHT//2+58, center=True)

        pygame.display.update()
        clock.tick(60)

def game_over_screen(score):
    t = 0
    while True:
        display_surface.fill(DARKGRAY)
        draw_stars(display_surface, t)

        draw_text(display_surface, "MISSION FAILED",       font_large, RED,    WINDOW_WIDTH//2, 190, center=True)
        draw_text(display_surface, f"SCORE : {score}",     font_med,   WHITE,  WINDOW_WIDTH//2, 295, center=True)
        draw_text(display_surface, "ENTER = TRY AGAIN",    font_med,   GREEN,  WINDOW_WIDTH//2, 400, center=True)
        draw_text(display_surface, "ESC = QUIT",           font_small, YELLOW, WINDOW_WIDTH//2, 448, center=True)

        # Damaged spaceship
        bob = int(math.sin(t*0.04)*4)
        draw_spaceship(display_surface, WINDOW_WIDTH//2, 550+bob, t, int(math.sin(t*0.1)*8))

        pygame.display.update()
        clock.tick(60)
        t += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN: return
                if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()

def congrats_screen(score):
    all_colors = [CYAN,YELLOW,GREEN,ORANGE,PURPLE,PINK,WHITE,GOLD]
    t = 0
    while True:
        display_surface.fill(DARKGRAY)
        update_stars(3)
        draw_stars(display_surface, t)

        if t % 3 == 0:
            spawn_explosion(randint(0,WINDOW_WIDTH), randint(0,WINDOW_HEIGHT//3), all_colors[t%len(all_colors)], 10)
        update_particles(display_surface)

        col = all_colors[(t//18)%len(all_colors)]
        draw_text(display_surface, "MISSION COMPLETE!",       font_large, col,   WINDOW_WIDTH//2, 130, center=True)
        draw_text(display_surface, "You beat all 5 levels!",  font_med,   WHITE, WINDOW_WIDTH//2, 212, center=True)
        draw_text(display_surface, "You are a LEGEND!",       font_med,   GOLD,  WINDOW_WIDTH//2, 250, center=True)
        draw_text(display_surface, f"FINAL SCORE : {score}",  font_med,   CYAN,  WINDOW_WIDTH//2, 300, center=True)

        stars_earned = 5 if score>4500 else 4 if score>3200 else 3 if score>2000 else 2 if score>1000 else 1
        for i in range(5):
            sc = GOLD if i < stars_earned else (40,40,58)
            draw_text(display_surface, "★", font_large, sc, WINDOW_WIDTH//2-104+i*54, 368, center=True)

        # Two victory spaceships
        bob = int(math.sin(t*0.08)*18)
        draw_spaceship(display_surface, WINDOW_WIDTH//2-170, 510+bob, t,  5)
        draw_spaceship(display_surface, WINDOW_WIDTH//2+170, 510-bob, t, -5)

        draw_text(display_surface, "ENTER = PLAY AGAIN", font_med,   GREEN,  WINDOW_WIDTH//2, 575, center=True)
        draw_text(display_surface, "ESC = QUIT",         font_small, YELLOW, WINDOW_WIDTH//2, 614, center=True)

        pygame.display.update()
        clock.tick(60)
        t += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN: return
                if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()

# ─── Main Game ─────────────────────────────────────────────────
def run_game():
    player        = Player()
    bullets       = []
    enemy_bullets = []
    enemies       = []
    particles.clear()
    score_popups.clear()

    score      = 0
    level      = 1
    cfg        = LEVEL_CONFIG[level]
    spawned    = 0
    killed     = 0
    spawn_timer= 0
    flash_timer= 0
    flash_color= WHITE
    t          = 0
    # Level complete
    if spawned >= cfg["enemies_total"] and len(enemies) == 0:
            score += 200 * level
            if level <= MAX_LEVEL:
                level  += 1
                cfg     = LEVEL_CONFIG[level]
                spawned = killed = spawn_timer = 0
                bullets.clear(); enemy_bullets.clear()
                level_banner(level)
            elif level> MAX_LEVEL:
                #Level 5 complete — WIN!
                return ("win", score)

    level_banner(level)

    while True:
        clock.tick(60)
        keys = pygame.key.get_pressed()
        t   += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()

        # Shoot — twin cannons
        if keys[pygame.K_SPACE]:
            new_bullets = player.shoot()
            bullets.extend(new_bullets)

        # Spawn enemies
        if spawned < cfg["enemies_total"]:
            spawn_timer += 1
            if spawn_timer >= cfg["spawn_interval"]:
                enemies.append(Enemy(cfg, cfg["color"]))
                spawned    += 1
                spawn_timer = 0

        # Update
        player.update(keys)
        update_stars(1+level)

        for b in bullets[:]:
            b.update()
            if b.off_screen(): bullets.remove(b)

        for e in enemies[:]:
            e.update()
            eb = e.shoot()
            if eb: enemy_bullets.append(eb)
            if e.off_screen():
                enemies.remove(e)
                score = max(0, score-5)

        for eb in enemy_bullets[:]:
            eb.update()
            if eb.off_screen(): enemy_bullets.remove(eb)

        # Collisions: player bullets vs enemies
        for b in bullets[:]:
            for e in enemies[:]:
                if b.rect.colliderect(e.rect):
                    if b in bullets: bullets.remove(b)
                    e.health -= 1
                    spawn_explosion(e.x, e.y, ORANGE, 8)
                    if e.health <= 0:
                        spawn_explosion(e.x, e.y, e.color, 28)
                        spawn_explosion(e.x, e.y, ORANGE, 14)
                        if e in enemies: enemies.remove(e)
                        pts    = 10 * cfg["score_mul"]
                        score += pts
                        killed+= 1
                        add_score_popup(int(e.x), int(e.y)-30, pts, cfg["color"])
                        flash_timer = 3
                        flash_color = cfg["color"]
                    break

        # Collisions: enemy bullets vs player
        for eb in enemy_bullets[:]:
            if eb.rect.colliderect(player.rect):
                enemy_bullets.remove(eb)
                if player.hit():
                    flash_timer = 9
                    flash_color = RED

        # Collisions: enemy vs player
        for e in enemies[:]:
            if e.rect.colliderect(player.rect):
                if e in enemies: enemies.remove(e)
                if player.hit():
                    flash_timer = 12
                    flash_color = RED

        # Level complete
        if spawned >= cfg["enemies_total"] and len(enemies) == 0:
            score += 200 * level
            if level < MAX_LEVEL:
                level  += 1
                cfg     = LEVEL_CONFIG[level]
                spawned = killed = spawn_timer = 0
                bullets.clear(); enemy_bullets.clear()
                level_banner(level)
            else:
                return ("win", score)

        # Game over
        if player.health <= 0:
            spawn_explosion(player.x, player.y, CYAN,   30)
            spawn_explosion(player.x, player.y, ORANGE, 20)
            return ("lose", score)

        # ── Draw ──────────────────────────────────────
        display_surface.fill(DARKGRAY)
        draw_stars(display_surface, t)
        update_particles(display_surface)

        for e  in enemies:       e.draw(display_surface)
        for b  in bullets:       b.draw(display_surface)
        for eb in enemy_bullets: eb.draw(display_surface)
        player.draw(display_surface)
        update_score_popups(display_surface)

        if flash_timer > 0:
            ov = pygame.Surface((WINDOW_WIDTH,WINDOW_HEIGHT))
            ov.set_alpha(60)
            ov.fill(flash_color)
            display_surface.blit(ov,(0,0))
            flash_timer -= 1

        draw_hud(display_surface, score, level, killed, cfg["enemies_total"], t, player.health)
        pygame.display.update()


# ─── Entry ────────────────────────────────────────────────────
start_screen()
while True:
    result, final_score = run_game()
    if result == "win":
        congrats_screen(final_score)
        # congrats ke baad phir game shuru
    else:
        game_over_screen(final_score)
        # game over ke baad phir game shuru
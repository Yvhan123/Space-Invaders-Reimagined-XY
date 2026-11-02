"""
Sprites for Space Invaders - Retro Edition:
- Green Pixel-Art X-Wing (4-directional movement)
- Multi-colored Pixel-Art Aliens with unpredictable movement patterns
- Lasers & Explosion Particles
"""

import math
import random
import pygame
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    SPRITE_SCALE,
    ALIEN_SCALE,
    PLAYER_SPEED,
    PLAYER_SHOOT_COOLDOWN,
    BULLET_SPEED,
    GREEN,
    DARK_GREEN,
    WHITE,
    YELLOW,
)

# 19x16 multi-palette pixel art for a Green X-Wing Starfighter!
XWING_PIXEL_MAP = [
    ".........L.........",  # Nose cone tip
    "........LGL........",
    " #......GGG......# ",  # Wingtip laser cannon tips ('#' = bright laser tips)
    " L......GDG......L ",  # Wingtip laser barrels
    " L......GGG......L ",
    " L......GCG......L ",  # Cockpit front
    " L.....GGCGG.....L ",  # Cockpit canopy
    " D....GGGGGGG....D ",
    " DG..GGGGWGGGG..GD ",  # R2 unit ('W') behind cockpit + inner wing roots
    " DGGGGGGGDGGGGGGGD ",  # Main S-foil wings
    " GGGGGDDGGGDDGGGGG ",  # Wing squadron stripes ('D')
    " GGGGDDDDGDDDDGGGG ",
    " GG..DDGGGGGGDD.GG ",  # Twin engine intakes
    " .....DGG.GGD..... ",
    " .....GG...GG..... ",  # Rear fuselage & twin engines
    " .....OO...OO..... ",  # Twin thruster glow
]


class Player(pygame.sprite.Sprite):
    """The player's pixelated Green X-Wing starfighter with full 4-directional flight."""

    def __init__(self):
        super().__init__()
        self.scale = SPRITE_SCALE
        self.image = self._build_xwing_surface()
        self.rect = self.image.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 65))
        self.fx = float(self.rect.centerx)
        self.fy = float(self.rect.centery)
        self.speed = PLAYER_SPEED
        self.last_shot = 0
        self.invulnerable_until = 0

    def _build_xwing_surface(self) -> pygame.Surface:
        palette = {
            "G": GREEN,
            "D": DARK_GREEN,
            "L": (150, 255, 170),
            "#": YELLOW,
            "W": WHITE,
            "C": (80, 235, 255),
            "O": (255, 145, 40),
        }
        rows = len(XWING_PIXEL_MAP)
        cols = len(XWING_PIXEL_MAP[0])
        surf = pygame.Surface((cols * self.scale, rows * self.scale), pygame.SRCALPHA)
        for r, row_str in enumerate(XWING_PIXEL_MAP):
            for c, ch in enumerate(row_str):
                if ch in palette:
                    pygame.draw.rect(
                        surf,
                        palette[ch],
                        (c * self.scale, r * self.scale, self.scale, self.scale),
                    )
        return surf

    def update(self):
        keys = pygame.key.get_pressed()
        dx = 0.0
        dy = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1.0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1.0
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1.0

        # Normalize diagonal speed so flying diagonally isn't overly fast
        if dx != 0.0 and dy != 0.0:
            dx *= 0.7071
            dy *= 0.7071

        self.fx += dx * self.speed
        self.fy += dy * self.speed

        # Keep player within the screen arena (between top HUD and bottom status bar)
        half_w = self.rect.width // 2
        half_h = self.rect.height // 2
        self.fx = max(16 + half_w, min(SCREEN_WIDTH - 16 - half_w, self.fx))
        self.fy = max(55 + half_h, min(SCREEN_HEIGHT - 55 - half_h, self.fy))
        self.rect.center = (int(self.fx), int(self.fy))

    def can_shoot(self, now: int) -> bool:
        return now - self.last_shot >= PLAYER_SHOOT_COOLDOWN

    def shoot(self, now: int, all_sprites: pygame.sprite.Group, bullets: pygame.sprite.Group):
        self.last_shot = now
        b = Bullet(self.rect.centerx, self.rect.top, vx=0.0, vy=-BULLET_SPEED, color=GREEN)
        all_sprites.add(b)
        bullets.add(b)


# 11x8 pixel art patterns for 3 classic alien designs (2 animation frames each)
ALIEN_PATTERNS = [
    # Type 0 (Squid style)
    [
        [
            "....###....",
            "...#####...",
            "..#######..",
            ".##.###.##.",
            ".#########.",
            "...#...#...",
            "..#.#.#.#..",
            ".#...#...#.",
        ],
        [
            "....###....",
            "...#####...",
            "..#######..",
            ".##.###.##.",
            ".#########.",
            "..#..#..#..",
            ".#.......#.",
            "..#.....#..",
        ],
    ],
    # Type 1 (Crab style)
    [
        [
            "..#.....#..",
            "...#...#...",
            "..#######..",
            ".##.###.##.",
            "###########",
            "#.#######.#",
            "#.#.....#.#",
            "...##.##...",
        ],
        [
            "..#.....#..",
            "#..#...#..#",
            "#.#######.#",
            "###.###.###",
            "###########",
            ".#########.",
            "..#.....#..",
            ".#.......#.",
        ],
    ],
    # Type 2 (Octopus style)
    [
        [
            "...#####...",
            ".#########.",
            "###########",
            "###.###.###",
            "###########",
            "..##...##..",
            ".##.##.##..",
            "##.......##",
        ],
        [
            "...#####...",
            ".#########.",
            "###########",
            "###.###.###",
            "###########",
            "...##.##...",
            "..##...##..",
            "...#...#...",
        ],
    ],
]


class Alien(pygame.sprite.Sprite):
    """
    Space Invader alien that spawns in random locations and uses unpredictable movement:
    - 'weaver': snakes downward in erratic sine/cosine waves
    - 'zigzag': darts diagonally and unpredictably flips direction at random intervals
    - 'swooper': cruises horizontally while periodically making sudden speed dives
    """

    BEHAVIORS = ("weaver", "zigzag", "swooper")

    def __init__(self, x: int, y: int, color: tuple, wave: int = 1):
        super().__init__()
        self.color = color
        self.wave = wave
        pattern_idx = random.randrange(len(ALIEN_PATTERNS))
        self.score_value = (3 - pattern_idx) * 15

        self.frames = [
            self._render_pattern(ALIEN_PATTERNS[pattern_idx][0], color),
            self._render_pattern(ALIEN_PATTERNS[pattern_idx][1], color),
        ]
        self.frame_index = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))
        self.fx = float(x)
        self.fy = float(y)

        # Unpredictable movement parameters (smooth & fair to hit)
        self.behavior = random.choice(self.BEHAVIORS)
        speed_scale = 1.0 + (wave - 1) * 0.07
        self.vx = random.choice([-1, 1]) * random.uniform(0.8, 1.7) * speed_scale
        self.vy = random.uniform(0.45, 1.05) * speed_scale
        self.phase = random.uniform(0, math.tau)
        self.phase_speed = random.uniform(0.02, 0.05)
        self.wave_amp = random.uniform(0.9, 2.0)

        now = pygame.time.get_ticks()
        self.next_juke_time = now + random.randint(1100, 2600)
        self.next_anim_time = now + random.randint(200, 380)

    @staticmethod
    def _render_pattern(grid: list[str], color: tuple) -> pygame.Surface:
        scale = ALIEN_SCALE
        w = len(grid[0]) * scale
        h = len(grid) * scale
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for r, line in enumerate(grid):
            for c, ch in enumerate(line):
                if ch == "#":
                    pygame.draw.rect(surf, color, (c * scale, r * scale, scale, scale))
        return surf

    def update(self):
        now = pygame.time.get_ticks()

        # Animate legs/arms
        if now >= self.next_anim_time:
            self.next_anim_time = now + random.randint(220, 400)
            self.frame_index = 1 - self.frame_index
            self.image = self.frames[self.frame_index]

        # Periodically change direction or speed smoothly
        if now >= self.next_juke_time:
            self.next_juke_time = now + random.randint(1200, 2800)
            speed_scale = 1.0 + (self.wave - 1) * 0.07
            if self.behavior == "zigzag":
                self.vx = -self.vx * random.uniform(0.9, 1.1)
                self.vy = random.uniform(0.45, 1.15) * speed_scale
            elif self.behavior == "swooper":
                if random.random() < 0.35:
                    self.vy = random.uniform(1.3, 2.0) * speed_scale
                    self.vx = random.uniform(-0.9, 0.9) * speed_scale
                else:
                    self.vy = random.uniform(0.4, 0.9) * speed_scale
                    self.vx = random.choice([-1, 1]) * random.uniform(1.0, 1.9) * speed_scale
            else:  # weaver
                self.wave_amp = random.uniform(0.9, 2.1)
                self.phase_speed = random.uniform(0.02, 0.05)
                if random.random() < 0.4:
                    self.vx = -self.vx

        # Apply velocity based on behavior
        self.phase += self.phase_speed
        if self.behavior == "weaver":
            self.fx += math.sin(self.phase) * self.wave_amp + self.vx * 0.35
            self.fy += self.vy + math.cos(self.phase * 0.7) * 0.4
        else:
            self.fx += self.vx
            self.fy += self.vy

        # Bounce off left/right screen borders
        margin = 28
        if self.fx < margin:
            self.fx = float(margin)
            self.vx = abs(self.vx)
        elif self.fx > SCREEN_WIDTH - margin:
            self.fx = float(SCREEN_WIDTH - margin)
            self.vx = -abs(self.vx)

        # If an alien flies past the bottom, warp it back to the top at a random X!
        if self.fy > SCREEN_HEIGHT - 55:
            self.fy = random.uniform(-60, -20)
            self.fx = float(random.randint(50, SCREEN_WIDTH - 50))

        self.rect.center = (int(self.fx), int(self.fy))


class Bullet(pygame.sprite.Sprite):
    """Laser projectile fired by the player or aliens."""

    def __init__(self, x: float, y: float, vx: float = 0.0, vy: float = -BULLET_SPEED, color=GREEN):
        super().__init__()
        self.image = pygame.Surface((6, 16), pygame.SRCALPHA)
        pygame.draw.rect(self.image, color, (0, 0, 6, 16), border_radius=2)
        pygame.draw.rect(self.image, WHITE, (1, 2, 4, 10), border_radius=1)
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        self.fx = float(x)
        self.fy = float(y)
        self.vx = vx
        self.vy = vy

    def update(self):
        self.fx += self.vx
        self.fy += self.vy
        self.rect.center = (int(self.fx), int(self.fy))
        if (
            self.rect.bottom < 0
            or self.rect.top > SCREEN_HEIGHT - 55
            or self.rect.right < 0
            or self.rect.left > SCREEN_WIDTH
        ):
            self.kill()


class Particle(pygame.sprite.Sprite):
    """Pixel spark for retro explosion effects."""

    def __init__(self, x: int, y: int, color):
        super().__init__()
        size = random.randint(2, 4)
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.2, 4.8)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.fx = float(x)
        self.fy = float(y)
        self.life = random.randint(14, 26)

    def update(self):
        self.fx += self.vx
        self.fy += self.vy
        self.rect.center = (int(self.fx), int(self.fy))
        self.life -= 1
        if self.life <= 0:
            self.kill()

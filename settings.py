"""
Game configuration and constants for Space Invaders - Retro Edition.
"""

# Window settings (zoomed-out wider arena)
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
FPS = 60
TITLE = "Space Invaders Reimagined XY"

# Pixel scale for sprites
SPRITE_SCALE = 2
ALIEN_SCALE = 3  # Larger aliens so they are easy to see and satisfying to hit!

# Colors (R, G, B)
BG_COLOR = (8, 10, 18)
WHITE = (245, 248, 255)
GREEN = (50, 255, 80)          # Classic green player X-Wing
DARK_GREEN = (20, 160, 45)
RED = (255, 65, 85)
ORANGE = (255, 155, 45)
YELLOW = (255, 235, 60)
CYAN = (50, 235, 255)
PURPLE = (200, 95, 255)
PINK = (255, 105, 210)
GRAY = (110, 120, 145)

# Vibrant colors for the aliens
ALIEN_COLORS = [
    RED,
    ORANGE,
    YELLOW,
    CYAN,
    PURPLE,
    PINK,
]

# Player settings
PLAYER_SPEED = 5.5
PLAYER_LIVES = 3
PLAYER_SHOOT_COOLDOWN = 200  # milliseconds between shots

# Bullet settings
BULLET_SPEED = 11.5
ENEMY_BULLET_SPEED = 5.0

# Wave settings
BASE_ALIENS_PER_WAVE = 18

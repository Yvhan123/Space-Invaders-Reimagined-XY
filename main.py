"""
Space Invaders - Retro Edition
Featuring a zoomed-out arena, 4-directional green X-Wing,
and colorful aliens with random spawning & unpredictable movement!
Run with: python main.py
"""

import random
import sys
import pygame
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    TITLE,
    BG_COLOR,
    WHITE,
    GREEN,
    RED,
    YELLOW,
    CYAN,
    GRAY,
    ALIEN_COLORS,
    PLAYER_LIVES,
    ENEMY_BULLET_SPEED,
    BASE_ALIENS_PER_WAVE,
)
from sprites import Player, Alien, Bullet, Particle
from sounds import SoundManager


class Game:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.sounds = SoundManager()

        self.font_lg = pygame.font.SysFont("consolas", 44, bold=True)
        self.font_md = pygame.font.SysFont("consolas", 20, bold=True)
        self.font_sm = pygame.font.SysFont("consolas", 15)

        # Twinkling background stars across the wider zoomed-out arena
        self.stars = [
            [
                random.randint(0, SCREEN_WIDTH),
                random.randint(0, SCREEN_HEIGHT - 55),
                random.choice([0.4, 0.9, 1.5]),
                random.choice([1, 1, 2]),
            ]
            for _ in range(95)
        ]

        self.high_score = 0
        self.state = "PLAYING"
        self.reset_game()

    def reset_game(self):
        self.all_sprites = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()

        self.player = Player()
        self.all_sprites.add(self.player)

        self.score = 0
        self.lives = PLAYER_LIVES
        self.wave = 1

        self._spawn_alien_wave()
        self.sounds.start_music()

    def _spawn_alien_wave(self):
        """Spawns aliens in a randomized scatter pattern with different colors and behaviors."""
        for b in list(self.bullets):
            b.kill()
        for b in list(self.enemy_bullets):
            b.kill()

        count = BASE_ALIENS_PER_WAVE + (self.wave - 1) * 4
        placed_positions = []

        for _ in range(count):
            # Pick a random spawn spot in the upper half / above the top of the screen
            for _attempt in range(20):
                x = random.randint(50, SCREEN_WIDTH - 50)
                y = random.randint(-140, 200)
                if all((x - px) ** 2 + (y - py) ** 2 >= 38 ** 2 for px, py in placed_positions):
                    break
            placed_positions.append((x, y))

            color = random.choice(ALIEN_COLORS)
            alien = Alien(x, y, color=color, wave=self.wave)
            self.all_sprites.add(alien)
            self.aliens.add(alien)

        now = pygame.time.get_ticks()
        self.last_alien_shot = now
        self.last_march_pulse = now

    def spawn_explosion(self, x: int, y: int, color, count: int = 16):
        for _ in range(count):
            p = Particle(x, y, color)
            self.all_sprites.add(p)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == "PLAYING":
                        self.state = "PAUSED"
                    elif self.state == "PAUSED":
                        self.state = "PLAYING"
                    else:
                        pygame.quit()
                        sys.exit()

                elif event.key == pygame.K_p and self.state in ("PLAYING", "PAUSED"):
                    self.state = "PAUSED" if self.state == "PLAYING" else "PLAYING"

                elif event.key == pygame.K_m:
                    self.sounds.toggle_music()

                elif event.key == pygame.K_RETURN and self.state == "GAMEOVER":
                    self.reset_game()
                    self.state = "PLAYING"

    def _update_aliens_combat(self, now: int):
        if not self.aliens:
            self.wave += 1
            self.sounds.play_wave_clear()
            self._spawn_alien_wave()
            return

        # Keep the classic Space Invaders bass pulse beating in the background
        remaining = len(self.aliens)
        total = BASE_ALIENS_PER_WAVE + (self.wave - 1) * 4
        pulse_interval = max(140, int(520 * (remaining / max(1, total))))
        if now - self.last_march_pulse >= pulse_interval:
            self.last_march_pulse = now
            self.sounds.play_march_step()

        # Aliens shooting back (only aliens currently visible on screen can shoot)
        shot_cooldown = max(350, 950 - self.wave * 75)
        if now - self.last_alien_shot >= shot_cooldown:
            visible_aliens = [a for a in self.aliens if a.rect.top >= 35]
            if visible_aliens:
                self.last_alien_shot = now
                shooter = random.choice(visible_aliens)
                # Slight random angle on alien shots to keep you on your toes!
                vx = random.uniform(-0.9, 0.9)
                b = Bullet(
                    shooter.rect.centerx,
                    shooter.rect.bottom,
                    vx=vx,
                    vy=ENEMY_BULLET_SPEED,
                    color=shooter.color,
                )
                self.all_sprites.add(b)
                self.enemy_bullets.add(b)
                self.sounds.play_alien_shoot()

    def _damage_player(self, now: int):
        self.lives -= 1
        self.player.invulnerable_until = now + 1400
        self.spawn_explosion(self.player.rect.centerx, self.player.rect.centery, GREEN, count=28)
        if self.lives <= 0:
            self.state = "GAMEOVER"
            self.sounds.stop_music()
            self.sounds.play_player_die()
        else:
            self.sounds.play_player_hit()

    def update(self):
        # Slowly drift background stars downward
        for star in self.stars:
            star[1] += star[2]
            if star[1] > SCREEN_HEIGHT - 55:
                star[0] = random.randint(0, SCREEN_WIDTH)
                star[1] = 0

        if self.state != "PLAYING":
            return

        now = pygame.time.get_ticks()

        # Player shooting (Spacebar)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and self.player.can_shoot(now):
            self.player.shoot(now, self.all_sprites, self.bullets)
            self.sounds.play_player_shoot()

        self.all_sprites.update()
        self._update_aliens_combat(now)

        # Player bullets hitting aliens
        hits = pygame.sprite.groupcollide(self.aliens, self.bullets, True, True)
        for alien in hits:
            self.score += alien.score_value
            self.high_score = max(self.high_score, self.score)
            self.spawn_explosion(alien.rect.centerx, alien.rect.centery, alien.color, count=18)
            self.sounds.play_alien_killed()

        # Enemy bullets or aliens hitting the player's green X-Wing
        if now >= self.player.invulnerable_until:
            if pygame.sprite.spritecollide(self.player, self.enemy_bullets, True):
                self._damage_player(now)
            else:
                crashed_aliens = pygame.sprite.spritecollide(self.player, self.aliens, True)
                if crashed_aliens:
                    for alien in crashed_aliens:
                        self.spawn_explosion(alien.rect.centerx, alien.rect.centery, alien.color, count=20)
                    self._damage_player(now)

    def draw_hud(self):
        # Score & Wave at top
        score_txt = self.font_md.render(f"SCORE: {self.score:04d}", True, WHITE)
        high_txt = self.font_md.render(f"HI-SCORE: {self.high_score:04d}", True, YELLOW)
        wave_txt = self.font_md.render(f"WAVE {self.wave}  ({len(self.aliens)} LEFT)", True, CYAN)

        self.screen.blit(score_txt, (20, 14))
        self.screen.blit(high_txt, (SCREEN_WIDTH // 2 - high_txt.get_width() // 2, 14))
        self.screen.blit(wave_txt, (SCREEN_WIDTH - wave_txt.get_width() - 20, 14))

        # Bottom line & Controls/Lives indicator
        pygame.draw.line(self.screen, GREEN, (20, SCREEN_HEIGHT - 48), (SCREEN_WIDTH - 20, SCREEN_HEIGHT - 48), 2)
        music_status = "OFF" if self.sounds.music_muted else "ON"
        lives_txt = self.font_sm.render(
            f"LIVES: {self.lives}   |   Move (4-Way): WASD or Arrow Keys   |   Shoot: SPACE   |   Music(M): {music_status}   |   Pause: P",
            True,
            GREEN,
        )
        self.screen.blit(lives_txt, (20, SCREEN_HEIGHT - 32))

    def draw_center_overlay(self, title: str, title_color, lines: list[tuple[str, tuple]]):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 10, 18, 195))
        self.screen.blit(overlay, (0, 0))

        title_surf = self.font_lg.render(title, True, title_color)
        self.screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60)))

        for i, (text, color) in enumerate(lines):
            surf = self.font_md.render(text, True, color)
            self.screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 38)))

    def draw(self):
        self.screen.fill(BG_COLOR)

        # Draw stars
        for x, y, _, r in self.stars:
            pygame.draw.circle(self.screen, GRAY, (int(x), int(y)), r)

        # Blink player while briefly invulnerable after taking a hit
        now = pygame.time.get_ticks()
        for sprite in self.all_sprites:
            if sprite is self.player and now < self.player.invulnerable_until and (now // 100) % 2 == 0:
                continue
            self.screen.blit(sprite.image, sprite.rect)

        self.draw_hud()

        if self.state == "PAUSED":
            self.draw_center_overlay(
                "PAUSED",
                YELLOW,
                [("Press P or ESC to Resume", WHITE)],
            )
        elif self.state == "GAMEOVER":
            self.draw_center_overlay(
                "GAME OVER",
                RED,
                [
                    (f"Final Score: {self.score}   (Wave {self.wave})", WHITE),
                    (f"High Score: {self.high_score}", YELLOW),
                    ("", WHITE),
                    ("Press ENTER to Play Again", GREEN),
                ],
            )

        pygame.display.flip()

    def run(self):
        while True:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()


if __name__ == "__main__":
    Game().run()

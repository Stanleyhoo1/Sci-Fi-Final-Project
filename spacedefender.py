import pygame
import sys
import random
import math
import os

# Load an image from assets/ folder
def load_image(name, scale=None):
    path = os.path.join("assets", name)
    try:
        image = pygame.image.load(path).convert_alpha()
    except pygame.error as e:
        print(f"Cannot load image: {path}\n{e}")
        sys.exit(1)

    if scale is not None:
        image = pygame.transform.scale(image, scale)
    return image

# --- SETTINGS ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Player settings
PLAYER_SPEED = 5
PLAYER_LIVES = 5
PLAYER_COOLDOWN = 150        # ms between auto‐shots
PLAYER_INVULNERABILITY = 1000  # ms after being hit

PLAYER_BULLET_SPEED = -8
PLAYER_BULLET_DAMAGE = 1

# Enemy bullet speeds & damages
ENEMY_BULLET_FAST_SPEED = 8    # thin, fast
ENEMY_BULLET_FAST_DAMAGE = 1
ENEMY_BULLET_SLOW_SPEED = 2    # big, slow
ENEMY_BULLET_SLOW_DAMAGE = 2

# Homing bullet settings
HOMING_STRENGTH = 0.05  # how strongly it curves each frame
HOMING_SPEED = 5
HOMING_DAMAGE = 1
HOMING_SIZE = (6, 12)
HOMING_COLOR = (0, 200, 200)

# Kamikaze settings (rusher)
KAMIKAZE_SPEED = 14        # constant rush speed
EXPLOSION_DURATION = 2000  # ms

# Sniper settings
SNIPER_BULLET_SPEED = 20
SNIPER_BULLET_DAMAGE = 2
SNIPER_SHOOT_DELAY = 3000   # ms between sniper shots
TANK_HEALTH = 15
TANK_SHOOT_DELAY = 2500     # ms between tank shots

# Wave timings
WAVE_DELAY = 1500  # ms before next wave

# Laser settings (boss & LaserShip)
LASER_WARNING_DURATION = 1000   # ms warning before laser fires
LASER_ACTIVE_DURATION = 1000    # ms active laser time
LASER_DELAY = 5000              # ms between boss lasers
LANE_WIDTH = 80                 # vertical lanes for boss
HORIZONTAL_LANE_HEIGHT = 60     # height of a horizontal band for LaserShip

# Colors
COLOR_BG = (10, 10, 30)
COLOR_PLAYER = (50, 200, 50)
COLOR_PLAYER_BULLET = (200, 200, 50)
COLOR_ENEMY = (200, 50, 50)
COLOR_HEAVY_ENEMY = (150, 50, 150)
COLOR_FAST_SHOOTER = (255, 100, 0)
COLOR_SLOW_SHOOTER = (200, 200, 0)
COLOR_HOMING_SHOOTER = (0, 200, 200)
COLOR_KAMIKAZE = (255, 0, 0)
COLOR_SNIPER = (255, 255, 255)
COLOR_TANK = (100, 100, 100)
COLOR_LASER_SHIP = (100, 200, 200)
COLOR_BOSS = (150, 50, 200)
COLOR_ENEMY_BULLET_FAST = (255, 100, 0)
COLOR_ENEMY_BULLET_SLOW = (200, 200, 0)
COLOR_HEALTH_BG = (80, 80, 80)
COLOR_HEALTH_FORE = (50, 255, 50)
COLOR_PAUSED = (255, 255, 255)
COLOR_PLAYER_FLASH = (255, 0, 0)
COLOR_LASER_WARNING = (255, 0, 0)
COLOR_LASER_ACTIVE = (255, 0, 200)
COLOR_HORIZONTAL_LASER = (255, 0, 100)
COLOR_EXPLOSION = (255, 150, 0)

# ----------------------------------------------------------------------
# EXPLOSION CLASS (simple circle that expands and fades)
# ----------------------------------------------------------------------
class Explosion(pygame.sprite.Sprite):
    def __init__(self, centerx, centery):
        super().__init__()
        self.image = pygame.Surface((0, 0), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(centerx, centery))
        self.start_time = pygame.time.get_ticks()
        self.duration = EXPLOSION_DURATION
        self.max_radius = 300
        self.center = (centerx, centery)

    def update(self, now, paused):
        if paused:
            return
        # If duration elapsed, remove
        if now - self.start_time >= self.duration:
            self.kill()

    def draw(self, surface):
        now = pygame.time.get_ticks()
        elapsed = now - self.start_time
        if elapsed >= self.duration:
            return
        # Interpolate radius from 0 to max_radius
        t = elapsed / self.duration
        radius = int(self.max_radius * t)
        alpha = int(255 * (1 - t))  # fade out
        if radius > 0:
            temp_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surf, (COLOR_EXPLOSION[0], COLOR_EXPLOSION[1], COLOR_EXPLOSION[2], alpha),
                               (radius, radius), radius)
            surface.blit(temp_surf, (self.center[0] - radius, self.center[1] - radius))


# ----------------------------------------------------------------------
# PLAYER CLASS
# ----------------------------------------------------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.base_image = load_image("player.png", scale=(60, 50)).convert_alpha()
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20))
        self.speed = PLAYER_SPEED
        self.last_shot = 0
        self.lives = PLAYER_LIVES
        self.invulnerable = False
        self.invuln_start = 0

    def update(self, now, paused):
        if paused or game_state["game_over"] or (game_state["wave"] == 10 and game_state["boss_dead"]):
            return

        # Handle invulnerability red flashing
        if self.invulnerable:
            if now - self.invuln_start >= PLAYER_INVULNERABILITY:
                self.invulnerable = False
                self.image = self.base_image.copy()
            else:
                if ((now - self.invuln_start) // 100) % 2 == 0:
                    self.image.fill(COLOR_PLAYER_FLASH)
                else:
                    self.image = self.base_image.copy()

        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.speed

        self.rect.x += dx
        self.rect.y += dy
        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

        # Auto‐shoot
        if now - self.last_shot >= PLAYER_COOLDOWN:
            self.shoot()
            self.last_shot = now

    def shoot(self):
        bullet = Bullet(self.rect.centerx, self.rect.top,
                        PLAYER_BULLET_SPEED, PLAYER_BULLET_DAMAGE,
                        COLOR_PLAYER_BULLET, size=(6, 12))
        all_sprites.add(bullet)
        player_bullets.add(bullet)

    def hit(self):
        if not self.invulnerable:
            self.lives -= 1
            if self.lives <= 0:
                game_state["game_over"] = True
            else:
                self.invulnerable = True
                self.invuln_start = pygame.time.get_ticks()


# ----------------------------------------------------------------------
# BULLET CLASS (player, enemy, homing)
# ----------------------------------------------------------------------
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, damage, color, size=(6,12), is_slow=False):
        super().__init__()
        self.image = pygame.Surface(size)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed
        self.damage = damage
        self.velocity = None  # For angled/homing bullets

        if is_slow:
            # draw a circle
            radius = size[0] // 2
            # create a square Surface just big enough to hold the circle, with per‐pixel alpha
            self.image = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            # draw a filled circle of color "color"
            pygame.draw.circle(self.image, color, (radius, radius), radius)
            # center the circle at (x, y)
            self.rect = self.image.get_rect(center=(x, y))
        else:
            # default rectangular bullet
            self.image = pygame.Surface(size)
            self.image.fill(color)
            self.rect = self.image.get_rect(center=(x, y))

    def update(self, paused):
        if paused:
            return

        if self.velocity:
            self.rect.x += int(self.velocity.x)
            self.rect.y += int(self.velocity.y)
            if isinstance(self, HomingBullet):
                self.adjust_homing()
        else:
            self.rect.y += self.speed

        # Kill if off‐screen
        if (self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or
            self.rect.right < 0 or self.rect.left > SCREEN_WIDTH):
            self.kill()

    def adjust_homing(self):
        dir_to_player = pygame.Vector2(
            player.rect.centerx - self.rect.centerx,
            player.rect.centery - self.rect.centery
        )
        if dir_to_player.length() != 0:
            dir_to_player = dir_to_player.normalize() * HOMING_SPEED
            self.velocity = (self.velocity * (1 - HOMING_STRENGTH) +
                             dir_to_player * HOMING_STRENGTH).normalize() * HOMING_SPEED


# ----------------------------------------------------------------------
# HOMING BULLET CLASS
# ----------------------------------------------------------------------
class HomingBullet(Bullet):
    def __init__(self, x, y):
        super().__init__(x, y, 0, HOMING_DAMAGE, HOMING_COLOR, size=HOMING_SIZE)
        self.velocity = pygame.Vector2(0, HOMING_SPEED)


# ----------------------------------------------------------------------
# BASE ENEMY CLASS (dodging logic)
# ----------------------------------------------------------------------
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, health, speed, color):
        super().__init__()
        self.health = health
        self.max_health = health
        self.speed = speed
        self.color = color

        # Image
        self.base_image = load_image("enemy_base.png", scale=(60, 50))
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(x, y))

        angle = random.uniform(0, 2 * math.pi)
        self.vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * self.speed

        self.last_shot = 0
        self.shoot_delay = random.randint(1200, 2000)

    def update(self, now, paused):
        if paused or game_state["game_over"]:
            return

        # Dodging: if a player bullet is near and moving toward, sidestep
        for b in player_bullets:
            if b.rect.centery < self.rect.centery:
                if abs(b.rect.centerx - self.rect.centerx) < 40:
                    if b.rect.centerx < self.rect.centerx:
                        self.rect.x += self.speed * 2
                    else:
                        self.rect.x -= self.speed * 2

        # Move & bounce within the top half
        self.rect.x += int(self.vel.x)
        self.rect.y += int(self.vel.y)
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.vel.x *= -1
            self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - self.rect.width))
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT // 2:
            self.vel.y *= -1
            self.rect.y = max(0, min(self.rect.y, SCREEN_HEIGHT // 2 - self.rect.height))

        # By default, 80% chance to shoot a regular bullet, 20% chance homing
        if now - self.last_shot >= self.shoot_delay:
            self.last_shot = now
            if random.random() < 0.2:
                hb = HomingBullet(self.rect.centerx, self.rect.bottom)
                all_sprites.add(hb)
                enemy_bullets.add(hb)
            else:
                self.shoot_regular()

    def shoot_regular(self):
        if random.random() < 0.5:
            b = Bullet(self.rect.centerx, self.rect.bottom,
                       ENEMY_BULLET_FAST_SPEED, ENEMY_BULLET_FAST_DAMAGE,
                       COLOR_ENEMY_BULLET_FAST, size=(4, 10))
        else:
            b = Bullet(self.rect.centerx, self.rect.bottom,
                       ENEMY_BULLET_SLOW_SPEED, ENEMY_BULLET_SLOW_DAMAGE,
                       COLOR_ENEMY_BULLET_SLOW, size=(24, 24), is_slow=True)
        all_sprites.add(b)
        enemy_bullets.add(b)

    def draw_health_bar(self, surface):
        bar_width = self.rect.width
        bar_height = 4
        ratio = max(0, self.health / self.max_health)
        x = self.rect.left
        y = self.rect.top - bar_height - 2
        pygame.draw.rect(surface, COLOR_HEALTH_BG, (x, y, bar_width, bar_height))
        pygame.draw.rect(surface, COLOR_HEALTH_FORE, (x, y, bar_width * ratio, bar_height))


# ----------------------------------------------------------------------
# FAST SHOOTER: fires ONLY fast bullets
# ----------------------------------------------------------------------
class FastShooter(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, health=2, speed=3, color=COLOR_FAST_SHOOTER)
        # ─── Override the base “enemy_base.png” with the “enemy_fast.png” sprite ───
        self.base_image = load_image("enemy_fast.png", scale=(60, 50))
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.shoot_delay = random.randint(1000, 1800)

    def update(self, now, paused):
        if paused or game_state["game_over"]:
            return

        # Move & bounce as usual
        self.rect.x += int(self.vel.x)
        self.rect.y += int(self.vel.y)
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.vel.x *= -1
            self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - self.rect.width))
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT // 2:
            self.vel.y *= -1
            self.rect.y = max(0, min(self.rect.y, SCREEN_HEIGHT // 2 - self.rect.height))

        if now - self.last_shot >= self.shoot_delay:
            self.last_shot = now
            b = Bullet(self.rect.centerx, self.rect.bottom,
                       ENEMY_BULLET_FAST_SPEED, ENEMY_BULLET_FAST_DAMAGE,
                       COLOR_ENEMY_BULLET_FAST, size=(4, 10))
            all_sprites.add(b)
            enemy_bullets.add(b)


# ----------------------------------------------------------------------
# SLOW SHOOTER: fires ONLY slow bullets
# ----------------------------------------------------------------------
class SlowShooter(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, health=4, speed=2, color=COLOR_SLOW_SHOOTER)
        self.base_image = load_image("enemy_slow.png", scale=(60, 50))
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.shoot_delay = random.randint(1500, 2500)

    def update(self, now, paused):
        if paused or game_state["game_over"]:
            return

        # Move & bounce as usual
        self.rect.x += int(self.vel.x)
        self.rect.y += int(self.vel.y)
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.vel.x *= -1
            self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - self.rect.width))
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT // 2:
            self.vel.y *= -1
            self.rect.y = max(0, min(self.rect.y, SCREEN_HEIGHT // 2 - self.rect.height))

        if now - self.last_shot >= self.shoot_delay:
            self.last_shot = now
            b = Bullet(self.rect.centerx, self.rect.bottom,
                       ENEMY_BULLET_SLOW_SPEED, ENEMY_BULLET_SLOW_DAMAGE,
                       COLOR_ENEMY_BULLET_SLOW, size=(24, 24), is_slow=True)
            all_sprites.add(b)
            enemy_bullets.add(b)


# ----------------------------------------------------------------------
# HOMING SHOOTER: fires ONLY homing bullets
# ----------------------------------------------------------------------
class HomingShooter(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, health=3, speed=2, color=COLOR_HOMING_SHOOTER)
        self.base_image = load_image("enemy_homing.png", scale=(60, 50))
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.shoot_delay = random.randint(1200, 2000)

    def update(self, now, paused):
        if paused or game_state["game_over"]:
            return

        # Move & bounce as usual
        self.rect.x += int(self.vel.x)
        self.rect.y += int(self.vel.y)
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.vel.x *= -1
            self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - self.rect.width))
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT // 2:
            self.vel.y *= -1
            self.rect.y = max(0, min(self.rect.y, SCREEN_HEIGHT // 2 - self.rect.height))

        if now - self.last_shot >= self.shoot_delay:
            self.last_shot = now
            hb = HomingBullet(self.rect.centerx, self.rect.bottom)
            all_sprites.add(hb)
            enemy_bullets.add(hb)


# ----------------------------------------------------------------------
# HEAVY ENEMY (slower, higher HP, dodging + mixed fire)
# ----------------------------------------------------------------------
class HeavyEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, health=8, speed=2, color=COLOR_HEAVY_ENEMY)
        self.base_image = load_image("alien_heavy.png", scale=(60, 50))
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.shoot_delay = random.randint(2000, 3500)


# ----------------------------------------------------------------------
# KAMIKAZE (rusher): spawn top or sides, rush straight toward player
# ----------------------------------------------------------------------
class Kamikaze(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = load_image("kamakaze.png", scale=(40, 40))
        self.rect = self.image.get_rect(center=(0,0))  # temp; we’ll overwrite center soon

        # Spawn logic:
        spawn_edge = random.choice(["top", "left", "right"])
        if spawn_edge == "top":
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = -20
        elif spawn_edge == "left":
            x = -20
            y = random.randint(50, SCREEN_HEIGHT // 2 - 50)
        else:  # "right"
            x = SCREEN_WIDTH + 20
            y = random.randint(50, SCREEN_HEIGHT // 2 - 50)

        self.rect.center = (x, y)

        dir_vec = pygame.Vector2(
            player.rect.centerx - self.rect.centerx,
            player.rect.centery - self.rect.centery
        )
        if dir_vec.length() != 0:
            self.velocity = dir_vec.normalize() * KAMIKAZE_SPEED
        else:
            self.velocity = pygame.Vector2(0, KAMIKAZE_SPEED)

    def update(self, now, paused):
        if paused or game_state["game_over"]:
            return

        # Move straight along the initial velocity
        self.rect.x += int(self.velocity.x)
        self.rect.y += int(self.velocity.y)

        # Check collision with player
        if self.rect.colliderect(player.rect):
            # Spawn an explosion at the collision point
            explosion = Explosion(player.rect.centerx, player.rect.centery)
            all_sprites.add(explosion)
            explosion_sprites.add(explosion)
            player.lives = 1  # Player dies on Kamikaze hit
            player.hit()
            self.kill()
            return

        # If Kamikaze goes off‐screen, just remove it
        if (self.rect.top > SCREEN_HEIGHT + 50 or self.rect.left > SCREEN_WIDTH + 50 or
            self.rect.right < -50 or self.rect.bottom < -50):
            self.kill()


# ----------------------------------------------------------------------
# TANK: high HP, periodically fire a slow large bullet at player
# ----------------------------------------------------------------------
class Tank(pygame.sprite.Sprite):
    def __init__(self, x, y, sniper):
        super().__init__()
        self.image = load_image("enemy_tank.png", scale=(60, 40))
        self.rect = self.image.get_rect(center=(x, y))
        self.health = TANK_HEALTH
        self.max_health = TANK_HEALTH
        self.sniper = sniper
        self.last_shot = 0
        self.shoot_delay = TANK_SHOOT_DELAY

    def update(self, now, paused):
        if paused or game_state["game_over"]:
            return

        # Tank slowly moves left/right at the top half
        self.rect.x += 1 if (now // 100) % 2 == 0 else -1
        # Keep tank within a horizontal range
        if self.rect.left < 50:
            self.rect.left = 50
        if self.rect.right > SCREEN_WIDTH - 50:
            self.rect.right = SCREEN_WIDTH - 50

        # If tank dies, sniper becomes vulnerable
        if self.health <= 0 and self.sniper:
            self.sniper.protected = False

        # Periodically fire a slow, large projectile targeted at the player
        if now - self.last_shot >= self.shoot_delay:
            self.last_shot = now
            direction = pygame.Vector2(
                player.rect.centerx - self.rect.centerx,
                player.rect.centery - self.rect.centery
            )
            if direction.length() != 0:
                direction = direction.normalize()
            b = Bullet(self.rect.centerx, self.rect.bottom,
                       0, ENEMY_BULLET_SLOW_DAMAGE, COLOR_ENEMY_BULLET_SLOW, size=(24, 24), is_slow=True)
            b.velocity = direction * ENEMY_BULLET_SLOW_SPEED
            all_sprites.add(b)
            enemy_bullets.add(b)

    def draw_health_bar(self, surface):
        bar_width = self.rect.width
        bar_height = 4
        ratio = max(0, self.health / self.max_health)
        x = self.rect.left
        y = self.rect.top - bar_height - 2
        pygame.draw.rect(surface, COLOR_HEALTH_BG, (x, y, bar_width, bar_height))
        pygame.draw.rect(surface, COLOR_HEALTH_FORE, (x, y, bar_width * ratio, bar_height))


# ----------------------------------------------------------------------
# SNIPER: fires a fast targeted bullet at the player
# ----------------------------------------------------------------------
class Sniper(pygame.sprite.Sprite):
    def __init__(self, x, y, tank_ref):
        super().__init__()
        self.image = load_image("enemy_sniper.png", scale=(40, 40))
        self.rect = self.image.get_rect(center=(x, y))
        self.health = 3
        self.max_health = 3
        self.last_shot = 0
        self.shoot_delay = SNIPER_SHOOT_DELAY
        self.protected = True
        self.tank_ref = tank_ref

    def update(self, now, paused):
        if paused or game_state["game_over"]:
            return

        # Keep shooting: every SNIPER_SHOOT_DELAY ms, fire a fast, targeted bullet
        if now - self.last_shot >= self.shoot_delay:
            self.last_shot = now
            direction = pygame.Vector2(
                player.rect.centerx - self.rect.centerx,
                player.rect.centery - self.rect.centery
            )
            if direction.length() != 0:
                direction = direction.normalize()
            b = Bullet(self.rect.centerx, self.rect.bottom,
                       0, SNIPER_BULLET_DAMAGE, COLOR_ENEMY_BULLET_FAST, size=(6, 12))
            b.velocity = direction * SNIPER_BULLET_SPEED
            all_sprites.add(b)
            enemy_bullets.add(b)

        # Only become vulnerable once the tank is dead
        if self.tank_ref is not None and self.tank_ref.health <= 0:
            self.protected = False

    def draw_health_bar(self, surface):
        if self.protected:
            return
        bar_width = self.rect.width
        bar_height = 4
        ratio = max(0, self.health / self.max_health)
        x = self.rect.left
        y = self.rect.top - bar_height - 2
        pygame.draw.rect(surface, COLOR_HEALTH_BG, (x, y, bar_width, bar_height))
        pygame.draw.rect(surface, COLOR_HEALTH_FORE, (x, y, bar_width * ratio, bar_height))


# ----------------------------------------------------------------------
# SIDE‐SHIP: appears at left or right, warns/fires horizontal laser, then exits
# ----------------------------------------------------------------------
class SideLaserShip(pygame.sprite.Sprite):
    def __init__(self, from_left=True):
        super().__init__()
        self.image = load_image("enemy_side.png", scale=(50, 50))
        self.from_left = from_left

        self.phase = "entering"
        self.spawn_time = pygame.time.get_ticks()

        dock_x = 100 if from_left else SCREEN_WIDTH - 100
        dock_y = random.randint(SCREEN_HEIGHT // 2, SCREEN_HEIGHT - 100)

        if from_left:
            self.rect = self.image.get_rect(center=(-50, dock_y))
            self.dock_pos = (dock_x, dock_y)
            self.speed = 5
        else:
            self.rect = self.image.get_rect(center=(SCREEN_WIDTH + 50, dock_y))
            self.dock_pos = (dock_x, dock_y)
            self.speed = -5

        self.laser_warning = False
        self.laser_warning_start = 0
        self.laser_active = False
        self.laser_active_start = 0
        self.laser_row = self.dock_pos[1] // HORIZONTAL_LANE_HEIGHT

    def update(self, now, paused):
        if paused or game_state["game_over"]:
            return

        if self.phase == "entering":
            # Move horizontally toward dock_x
            self.rect.x += self.speed
            # Check if we've reached (or passed) the dock X
            if ((self.from_left and self.rect.centerx >= self.dock_pos[0]) or
                (not self.from_left and self.rect.centerx <= self.dock_pos[0])):
                # Snap exactly to dock position
                self.rect.centerx = self.dock_pos[0]
                self.rect.centery = self.dock_pos[1]
                # Start the warning phase
                self.phase = "firing"
                self.laser_warning = True
                self.laser_warning_start = now

        elif self.phase == "firing":
            # (1) Warning period
            if self.laser_warning:
                if now - self.laser_warning_start >= LASER_WARNING_DURATION:
                    self.laser_warning = False
                    self.laser_active = True
                    self.laser_active_start = now
            # (2) Active period
            elif self.laser_active:
                if now - self.laser_active_start >= LASER_ACTIVE_DURATION:
                    # Done firing → move to exiting phase
                    self.laser_active = False
                    self.phase = "exiting"
                    # Reverse speed so we fly back off from the same side
                    self.speed = -self.speed
                else:
                    # While active, damage the player if in that horizontal band
                    y0 = self.laser_row * HORIZONTAL_LANE_HEIGHT
                    if y0 <= player.rect.centery <= y0 + HORIZONTAL_LANE_HEIGHT:
                        player.lives = 1 # Lasers also insta kills player (vaporizes them)
                        player.hit()

        elif self.phase == "exiting":
            # Fly straight off‐screen again
            self.rect.x += self.speed
            # If fully offscreen, remove
            if (self.rect.right < -60) or (self.rect.left > SCREEN_WIDTH + 60):
                self.kill()

    def draw_horizontal_laser(self, surface):
        now = pygame.time.get_ticks()
        y0 = self.laser_row * HORIZONTAL_LANE_HEIGHT

        if self.laser_warning and self.phase == "firing":
            # Flash a warning band
            if ((now - self.laser_warning_start) // 200) % 2 == 0:
                pygame.draw.rect(surface, COLOR_LASER_WARNING,
                                 (0, y0, SCREEN_WIDTH, HORIZONTAL_LANE_HEIGHT), border_radius=4)

        elif self.laser_active and self.phase == "firing":
            # Solid horizontal laser band
            pygame.draw.rect(surface, COLOR_HORIZONTAL_LASER,
                             (0, y0, SCREEN_WIDTH, HORIZONTAL_LANE_HEIGHT), border_radius=4)


# ----------------------------------------------------------------------
# BOSS CLASS (random wander + side ships + spawning tanks/snipers + new patterns)
# ----------------------------------------------------------------------
class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.health = 150
        self.max_health = 150

        self.image = load_image("boss.png", scale=(400, 200))
        self.rect = self.image.get_rect(midtop=(SCREEN_WIDTH // 2, -200))
        self.state = "entering"

        # --- Wandering logic ---
        self.speed_x = 0
        self.next_wander_time = 0
        self.wander_interval = 2000  # every 2 s choose a new horizontal speed

        # --- Firing patterns ---
        self.last_shot = 0
        self.shoot_delay = 800       # base delay between pattern bursts
        self.pattern_index = 0

        # --- Laser lanes ---
        self.last_laser = 0
        self.laser_delay = LASER_DELAY
        self.laser_warning = False
        self.laser_warning_start = 0
        self.laser_active = False
        self.laser_active_start = 0
        self.laser_lanes = []

        # --- Side‐ship spawn logic ---
        self.last_side_spawn = 0
        self.side_spawn_delay = 7000  # spawn SideLaserShip every ~7 s

        # --- New: Boss spawns Tanks/Snipers behind him ---
        self.last_enemy_spawn = 0
        self.enemy_spawn_interval = 5000  # every 5 s, spawn a random enemy behind the boss

    def update(self, now, paused):
        if paused or game_state["game_over"]:
            return

        if self.state == "entering":
            # Move down until y = 50, then switch to “fighting”
            if self.rect.top < 50:
                self.rect.y += 2
            else:
                self.state = "fighting"
                self.next_wander_time = now + self.wander_interval
                self.last_side_spawn = now + 3000
                self.last_enemy_spawn = now + 2000

        elif self.state == "fighting":
            # (1) Random Wander
            if now >= self.next_wander_time:
                self.speed_x = random.choice([-2, 0, 2])
                self.next_wander_time = now + self.wander_interval

            self.rect.x += self.speed_x
            self.rect.left = max(0, self.rect.left)
            self.rect.right = min(SCREEN_WIDTH, self.rect.right)

            # (2) Periodically spawn a SideLaserShip on boss’s nearest side
            if now - self.last_side_spawn >= self.side_spawn_delay:
                from_left = (self.rect.centerx < SCREEN_WIDTH // 2)
                side_ship = SideLaserShip(from_left=from_left)
                all_sprites.add(side_ship)
                laser_sprites.add(side_ship)
                # next spawn in 4–8 s
                self.last_side_spawn = now + random.randint(4000, 8000)

            # (3) Periodically spawn a random “behind” enemy directly beneath boss
            if now - self.last_enemy_spawn >= self.enemy_spawn_interval:
                self.last_enemy_spawn = now + random.randint(4000, 6000)

                # Choose either a Tank or Sniper at boss’s x, just below the boss
                spawn_x = self.rect.centerx
                spawn_y = self.rect.bottom + 20

                if random.random() < 0.5:
                    # Spawn a Tank (which itself protects a Sniper)
                    sniper = Sniper(spawn_x, spawn_y - 40, None)
                    tank = Tank(spawn_x, spawn_y, sniper)
                    sniper.tank_ref = tank
                    all_sprites.add(tank); tank_sprites.add(tank)
                    all_sprites.add(sniper); sniper_sprites.add(sniper)
                else:
                    # Spawn just a lone Sniper
                    sniper = Sniper(spawn_x, spawn_y, None)
                    all_sprites.add(sniper); sniper_sprites.add(sniper)

            # (4) Laser warning & bullet patterns
            # —— Laser warning sequence ——
            if (not self.laser_warning and not self.laser_active
                and now - self.last_laser >= self.laser_delay):
                self.laser_warning = True
                self.laser_warning_start = now
                self.pick_laser_lanes()

            if self.laser_warning:
                if now - self.laser_warning_start >= LASER_WARNING_DURATION:
                    self.laser_warning = False
                    self.laser_active = True
                    self.laser_active_start = now

            elif self.laser_active:
                if now - self.laser_active_start >= LASER_ACTIVE_DURATION:
                    self.laser_active = False
                    self.last_laser = now

            else:
                # (5) Fire one of several patterns
                if now - self.last_shot >= self.shoot_delay:
                    self.last_shot = now
                    self.fire_pattern()
                    self.pattern_index = (self.pattern_index + 1) % 5  # now 5 patterns

            if self.health <= 0:
                self.state = "dying"

        elif self.state == "dying":
            self.rect.y -= 4
            if self.rect.bottom < 0:
                self.kill()
                game_state["boss_dead"] = True

    def pick_laser_lanes(self):
        total_lanes = SCREEN_WIDTH // LANE_WIDTH
        k = random.randint(1, 3)
        all_idx = list(range(total_lanes))
        self.laser_lanes = random.sample(all_idx, k)

    def fire_pattern(self):
        """
        We now have 5 different patterns (pattern_index from 0 to 4):

        0: Wide-arc spread of fast bullets
        1: Triple-slow bullets straight down
        2: Homing missile volley
        3: Rapid “spiral” of fast bullets
        4: Mixed “zig-zag” pairs
        """
        idx = self.pattern_index

        if idx == 0:
            # Wide-arc spread (fast bullets, angled outward)
            angles = [-0.8, -0.6, -0.4, -0.2, 0, 0.2, 0.4, 0.6, 0.8]
            for ang in angles:
                direction = pygame.Vector2(ang, 1).normalize()
                b = Bullet(self.rect.centerx, self.rect.bottom,
                           0, 1, COLOR_ENEMY_BULLET_FAST, size=(4, 10))
                b.velocity = direction * ENEMY_BULLET_FAST_SPEED
                all_sprites.add(b)
                enemy_bullets.add(b)

        elif idx == 1:
            # Triple slow bullets straight down (clustered)
            offsets = [-40, 0, 40]
            for off in offsets:
                b = Bullet(self.rect.centerx + off, self.rect.bottom,
                           ENEMY_BULLET_SLOW_SPEED, 2, COLOR_ENEMY_BULLET_SLOW, size=(24, 24), is_slow=True)
                all_sprites.add(b)
                enemy_bullets.add(b)

        elif idx == 2:
            # Homing missile volley: 4 homing bullets at once
            for dx in [-60, -20, 20, 60]:
                hb = HomingBullet(self.rect.centerx + dx, self.rect.bottom)
                all_sprites.add(hb)
                enemy_bullets.add(hb)

        elif idx == 3:
            # Rapid spiral: spawn 12 bullets in a rotating circle, once
            for i in range(12):
                angle = i * (2 * math.pi / 12) + (pygame.time.get_ticks() / 500.0)
                direction = pygame.Vector2(math.cos(angle), math.sin(angle)).normalize()
                b = Bullet(self.rect.centerx, self.rect.centery,
                           0, 1, COLOR_ENEMY_BULLET_FAST, size=(4, 10))
                b.velocity = direction * ENEMY_BULLET_FAST_SPEED
                all_sprites.add(b)
                enemy_bullets.add(b)

        elif idx == 4:
            # Zig-zag pairs: two fast bullets that alternate left/right
            for sign in [-1, 1]:
                direction = pygame.Vector2(sign * 0.3, 1).normalize()
                b = Bullet(self.rect.centerx, self.rect.bottom,
                           0, 1, COLOR_ENEMY_BULLET_FAST, size=(4, 10))
                b.velocity = direction * ENEMY_BULLET_FAST_SPEED
                all_sprites.add(b)
                enemy_bullets.add(b)

    def draw_health_bar(self, surface):
        bar_width = self.rect.width
        bar_height = 8
        ratio = max(0, self.health / self.max_health)
        x = self.rect.left
        y = self.rect.top - bar_height - 4
        pygame.draw.rect(surface, COLOR_HEALTH_BG, (x, y, bar_width, bar_height))
        pygame.draw.rect(surface, COLOR_HEALTH_FORE, (x, y, bar_width * ratio, bar_height))

    def draw_laser(self, surface):
        now = pygame.time.get_ticks()
        if self.laser_warning:
            for lane in self.laser_lanes:
                x0 = lane * LANE_WIDTH
                if ((now - self.laser_warning_start) // 200) % 2 == 0:
                    pygame.draw.rect(surface, COLOR_LASER_WARNING, (x0, 0, LANE_WIDTH, SCREEN_HEIGHT))
        elif self.laser_active:
            for lane in self.laser_lanes:
                x0 = lane * LANE_WIDTH
                pygame.draw.rect(surface, COLOR_LASER_ACTIVE, (x0, 0, LANE_WIDTH, SCREEN_HEIGHT))
                if x0 <= player.rect.centerx <= x0 + LANE_WIDTH:
                    player.lives = 1 # Player dies instantly to laser
                    player.hit()


# ----------------------------------------------------------------------
# INITIALIZE PYGAME AND GROUPS
# ----------------------------------------------------------------------
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Alien Invasion Defender – 10 Waves + Boss")
clock = pygame.time.Clock()

all_sprites = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
enemy_sprites = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
kamikaze_sprites = pygame.sprite.Group()
tank_sprites = pygame.sprite.Group()
sniper_sprites = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()
boss_group = pygame.sprite.Group()
explosion_sprites = pygame.sprite.Group()

# ----------------------------------------------------------------------
# SET UP PLAYER
# ----------------------------------------------------------------------
player = Player()
all_sprites.add(player)

# Player heart icon
HEART_SIZE = (30, 30)
heart_full_img  = load_image("heart_full.png", scale=HEART_SIZE)
heart_empty_img = load_image("heart_empty.png", scale=HEART_SIZE)

# ----------------------------------------------------------------------
# GAME STATE
# ----------------------------------------------------------------------
game_state = {
    "wave": 0,
    "wave_start_time": pygame.time.get_ticks(),
    "boss_dead": False,
    "game_over": False,
    "victory": False,
    "paused": False,
    "last_laser_spawn": pygame.time.get_ticks(),
}

game_started = False
font_title = pygame.font.SysFont("Consolas", 24)

def draw_text(surface, text, color, rect, font, line_spacing=1.2):
    """
    Draw each paragraph (split on '\n') as its own line, centered inside rect.
    """
    x, y, max_w, max_h = rect
    paragraphs = text.split("\n")
    line_height = font.get_linesize()
    draw_y = y

    for i in range(len(paragraphs)):
        para = paragraphs[i]
        if para == "":
            # Blank line
            draw_y += int(line_height * line_spacing)
        else:
            # Render the entire paragraph onto one surface
            rendered = font.render(para, True, color)
            rw = rendered.get_width()

            # Center this rendered line within rect horizontally
            screen_x = x + (max_w - rw) // 2
            surface.blit(rendered, (screen_x, draw_y))

            # Move down for the next line
            draw_y += int(line_height * line_spacing)


# ----------------------------------------------------------------------
# START NEXT WAVE (1–10)
# ----------------------------------------------------------------------
def start_wave(n):
    now = pygame.time.get_ticks()
    game_state["wave_start_time"] = now

    # Clear any leftover LaserShips from previous wave
    for ls in laser_sprites:
        ls.kill()

    if n == 1:
        # Wave 1: 3 FastShooters
        for _ in range(3):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(20, SCREEN_HEIGHT // 2 - 50)
            e = FastShooter(x, y)
            all_sprites.add(e); enemy_sprites.add(e)

    elif n == 2:
        # Wave 2: 3 SlowShooters + 1 Kamikaze
        for _ in range(3):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(20, SCREEN_HEIGHT // 2 - 50)
            e = SlowShooter(x, y)
            all_sprites.add(e); enemy_sprites.add(e)
        k = Kamikaze()
        all_sprites.add(k); kamikaze_sprites.add(k)

    elif n == 3:
        # Wave 3: 4 HomingShooters
        for _ in range(4):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(20, SCREEN_HEIGHT // 2 - 50)
            e = HomingShooter(x, y)
            all_sprites.add(e); enemy_sprites.add(e)

    elif n == 4:
        # Wave 4: 2 Sniper/Tank pairs + 2 FastShooters
        for i in range(2):
            tx = random.randint(100, SCREEN_WIDTH - 100)
            ty = random.randint(50, SCREEN_HEIGHT // 2 - 50)
            sniper = Sniper(tx, ty - 50, None)
            tank = Tank(tx, ty, sniper)
            sniper.tank_ref = tank
            all_sprites.add(tank); tank_sprites.add(tank)
            all_sprites.add(sniper); sniper_sprites.add(sniper)
        for _ in range(2):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(20, SCREEN_HEIGHT // 2 - 50)
            e = FastShooter(x, y)
            all_sprites.add(e); enemy_sprites.add(e)

    elif n == 5:
        # Wave 5: 3 Kamikaze + 2 SlowShooters + 1 LaserShip
        for _ in range(3):
            k = Kamikaze()
            all_sprites.add(k); kamikaze_sprites.add(k)
        for _ in range(2):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(20, SCREEN_HEIGHT // 2 - 50)
            e = SlowShooter(x, y)
            all_sprites.add(e); enemy_sprites.add(e)
        ls = SideLaserShip(from_left=bool(random.getrandbits(1)))
        all_sprites.add(ls); laser_sprites.add(ls)

    elif n == 6:
        # Wave 6: 5 Mixed shooters (fast/slow/homing) + 2 Sniper/Tank + 1 LaserShip
        for _ in range(2):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(20, SCREEN_HEIGHT // 2 - 50)
            e = FastShooter(x, y)
            all_sprites.add(e); enemy_sprites.add(e)
        for _ in range(2):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(20, SCREEN_HEIGHT // 2 - 50)
            e = SlowShooter(x, y)
            all_sprites.add(e); enemy_sprites.add(e)
        for _ in range(1):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(20, SCREEN_HEIGHT // 2 - 50)
            e = HomingShooter(x, y)
            all_sprites.add(e); enemy_sprites.add(e)
        for i in range(2):
            tx = random.randint(100, SCREEN_WIDTH - 100)
            ty = random.randint(50, SCREEN_HEIGHT // 2 - 50)
            sniper = Sniper(tx, ty - 50, None)
            tank = Tank(tx, ty, sniper)
            sniper.tank_ref = tank
            all_sprites.add(tank); tank_sprites.add(tank)
            all_sprites.add(sniper); sniper_sprites.add(sniper)
        ls = SideLaserShip(from_left=bool(random.getrandbits(1)))
        all_sprites.add(ls); laser_sprites.add(ls)

    elif n == 7:
        # Wave 7: 4 HomingShooters + 3 Kamikaze + 1 LaserShip
        for _ in range(4):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(20, SCREEN_HEIGHT // 2 - 50)
            e = HomingShooter(x, y)
            all_sprites.add(e); enemy_sprites.add(e)
        for _ in range(3):
            k = Kamikaze()
            all_sprites.add(k); kamikaze_sprites.add(k)
        ls = SideLaserShip(from_left=bool(random.getrandbits(1)))
        all_sprites.add(ls); laser_sprites.add(ls)

    elif n == 8:
        # Wave 8: 3 FastShooters + 3 SlowShooters + 3 HomingShooters + 1 LaserShip
        for _ in range(3):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(20, SCREEN_HEIGHT // 2 - 50)
            e = FastShooter(x, y)
            all_sprites.add(e); enemy_sprites.add(e)
        for _ in range(3):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(20, SCREEN_HEIGHT // 2 - 50)
            e = SlowShooter(x, y)
            all_sprites.add(e); enemy_sprites.add(e)
        for _ in range(3):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(20, SCREEN_HEIGHT // 2 - 50)
            e = HomingShooter(x, y)
            all_sprites.add(e); enemy_sprites.add(e)
        ls = SideLaserShip(from_left=bool(random.getrandbits(1)))
        all_sprites.add(ls); laser_sprites.add(ls)

    elif n == 9:
        # Wave 9: 5 HeavyEnemies + 4 Kamikaze + 2 Sniper/Tank + 1 LaserShip
        for _ in range(5):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(20, SCREEN_HEIGHT // 2 - 50)
            he = HeavyEnemy(x, y)
            all_sprites.add(he); enemy_sprites.add(he)
        for _ in range(4):
            k = Kamikaze()
            all_sprites.add(k); kamikaze_sprites.add(k)
        for i in range(2):
            tx = random.randint(100, SCREEN_WIDTH - 100)
            ty = random.randint(50, SCREEN_HEIGHT // 2 - 50)
            sniper = Sniper(tx, ty - 50, None)
            tank = Tank(tx, ty, sniper)
            sniper.tank_ref = tank
            all_sprites.add(tank); tank_sprites.add(tank)
            all_sprites.add(sniper); sniper_sprites.add(sniper)
        ls = SideLaserShip(from_left=bool(random.getrandbits(1)))
        all_sprites.add(ls); laser_sprites.add(ls)

    elif n == 10:
        # Wave 10: Boss fight
        boss = Boss()
        all_sprites.add(boss)
        boss_group.add(boss)

# ----------------------------------------------------------------------
# RESET GAME FUNCTION
# ----------------------------------------------------------------------
def reset_game():
    global player, game_started
    # Clear all sprite groups
    all_sprites.empty()
    player_bullets.empty()
    enemy_bullets.empty()
    enemy_sprites.empty()
    kamikaze_sprites.empty()
    tank_sprites.empty()
    sniper_sprites.empty()
    laser_sprites.empty()
    boss_group.empty()
    explosion_sprites.empty()

    # Recreate the player
    player = Player()
    all_sprites.add(player)

    # Reset state
    game_state.update({
        "wave": 0,
        "wave_start_time": pygame.time.get_ticks(),
        "boss_dead": False,
        "game_over": False,
        "victory": False,
        "paused": False,
        "last_laser_spawn": pygame.time.get_ticks(),
    })
    game_started = False


# ----------------------------------------------------------------------
# MAIN GAME LOOP
# ----------------------------------------------------------------------
running = True
while running:
    dt = clock.tick(FPS)
    now = pygame.time.get_ticks()

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            # If game hasn't started, pressing 'S' begins the game
            if not game_started and event.key == pygame.K_s:
                game_started = True

            # Only once the game has started we exit using ESC, pause with 'P', or reset with 'R' (once game is over)
            elif game_started:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_p:
                    game_state["paused"] = not game_state["paused"]
                elif event.key == pygame.K_r and (game_state["game_over"] or game_state["victory"]):
                    reset_game()

    # If the game hasn’t started, display welcome message:
    if not game_started:
        screen.fill(COLOR_BG)
        title_rect = pygame.Rect(
            50,
            SCREEN_HEIGHT // 4,
            SCREEN_WIDTH - 100,
            SCREEN_HEIGHT // 3
        )

        title_text = (
            "Welcome to Alien Invasion Defender!\n"
            "You are humanity's last hope to defeat the aliens\n"
            "trying to invade our planet.\n"
            "Survive 10 waves of enemies to take down\n"
            "their leader and save Earth!\n"
            "\n"
            "Do you have what it takes?\n"
            "\n"
            "Press S to Start"
        )

        draw_text(screen, title_text, (255, 255, 255), title_rect, font_title)
        pygame.display.flip()
        continue
    
    # --- Occasionally spawn a LaserShip during Waves 1–9 ---
    if (not game_state["paused"]
        and 1 <= game_state["wave"] <= 9
        and len(laser_sprites) == 0
        and now - game_state["last_laser_spawn"] > random.randint(5000, 10000)):
        ls = SideLaserShip(from_left=bool(random.getrandbits(1)))
        all_sprites.add(ls); laser_sprites.add(ls)
        game_state["last_laser_spawn"] = now

    # --- Manage Waves ---
    if not (game_state["game_over"] or game_state["victory"] or game_state["paused"]):
        wave = game_state["wave"]
        elapsed = now - game_state["wave_start_time"]

        if wave == 0 and elapsed > WAVE_DELAY:
            game_state["wave"] = 1
            start_wave(1)

        elif wave == 1 and len(enemy_sprites) == 0 and elapsed > WAVE_DELAY:
            game_state["wave"] = 2
            start_wave(2)

        elif wave == 2 and len(enemy_sprites) + len(kamikaze_sprites) == 0 and elapsed > WAVE_DELAY:
            game_state["wave"] = 3
            start_wave(3)

        elif wave == 3 and len(enemy_sprites) == 0 and elapsed > WAVE_DELAY:
            game_state["wave"] = 4
            start_wave(4)

        elif wave == 4 and (len(enemy_sprites) + len(kamikaze_sprites) + len(tank_sprites) + len(sniper_sprites)) == 0 and elapsed > WAVE_DELAY:
            game_state["wave"] = 5
            start_wave(5)

        elif wave == 5 and (len(enemy_sprites) + len(kamikaze_sprites)) == 0 and elapsed > WAVE_DELAY:
            game_state["wave"] = 6
            start_wave(6)

        elif wave == 6 and (len(enemy_sprites) + len(kamikaze_sprites) + len(sniper_sprites)) == 0 and elapsed > WAVE_DELAY:
            game_state["wave"] = 7
            start_wave(7)

        elif wave == 7 and (len(enemy_sprites) + len(kamikaze_sprites)) == 0 and elapsed > WAVE_DELAY:
            game_state["wave"] = 8
            start_wave(8)

        elif wave == 8 and (len(enemy_sprites) + len(kamikaze_sprites)) == 0 and elapsed > WAVE_DELAY:
            game_state["wave"] = 9
            start_wave(9)

        elif wave == 9 and (len(enemy_sprites) + len(kamikaze_sprites) + len(tank_sprites) + len(sniper_sprites)) == 0 and elapsed > WAVE_DELAY:
            game_state["wave"] = 10
            start_wave(10)

    # --- Update All Sprites ---
    player.update(now, game_state["paused"])
    for b in player_bullets:
        b.update(game_state["paused"])
    for b in enemy_bullets:
        b.update(game_state["paused"])
    for e in enemy_sprites:
        e.update(now, game_state["paused"])
    for k in kamikaze_sprites:
        k.update(now, game_state["paused"])
    for t in tank_sprites:
        t.update(now, game_state["paused"])
    for s in sniper_sprites:
        s.update(now, game_state["paused"])
    for ls in laser_sprites:
        ls.update(now, game_state["paused"])
    for bobj in boss_group:
        bobj.update(now, game_state["paused"])
    for ex in explosion_sprites:
        ex.update(now, game_state["paused"])

    # --- Collision Detection ---
    if not (game_state["paused"] or game_state["game_over"] or game_state["victory"]):
        # player.invulnerable = True
        # 1) Player bullets → regular enemies
        for e in enemy_sprites:
            hits = pygame.sprite.spritecollide(e, player_bullets, True)
            for b in hits:
                e.health -= b.damage
                if e.health <= 0:
                    e.kill()

        # 2) Player bullets → Tanks
        for t in tank_sprites:
            hits = pygame.sprite.spritecollide(t, player_bullets, True)
            for b in hits:
                t.health -= b.damage
                if t.health <= 0:
                    t.kill()

        # 3) Player bullets → Snipers (always vulnerable now)
        for s in sniper_sprites:
            hits = pygame.sprite.spritecollide(s, player_bullets, True)
            for b in hits:
                s.health -= b.damage
                if s.health <= 0:
                    s.kill()

        # 4) Player bullets → Boss (wave 10)
        for bullet in player_bullets:
            boss_hits = pygame.sprite.spritecollide(bullet, boss_group, False)
            for boss_obj in boss_hits:
                bullet.kill()
                boss_obj.health -= bullet.damage
                if boss_obj.health <= 0 and boss_obj.state == "fighting":
                    boss_obj.state = "dying"

        # 5) Enemy bullets → Player
        hits = pygame.sprite.spritecollide(player, enemy_bullets, True)
        if hits:
            for bullet in hits:
                if bullet.damage > 1:
                    player.lives -= bullet.damage - 1
            player.hit()

        # 6) Enemy ships → Player (collision damage)
        hits = pygame.sprite.spritecollide(player, enemy_sprites, False)
        if hits:
            for e in hits:
                e.kill()
            player.hit()

        # 7) Kamikaze vs. Player handled in Kamikaze.update

        # 8) Sniper/Tank ships vs. Player
        hits = pygame.sprite.spritecollide(player, tank_sprites, False)
        if hits:
            for t in hits:
                t.health = 0  # instant tank “break” on contact
            player.hit()
        hits = pygame.sprite.spritecollide(player, sniper_sprites, False)
        if hits:
            for s in hits:
                s.health = 0
                s.kill()
            player.hit()

        # 9) Horizontal lasers from LaserShip (damage handled in update/draw)

        # 10) Boss vs. Player
        hits = pygame.sprite.spritecollide(player, boss_group, False)
        if hits:
            player.hit()

        # 11) Victory check
        if game_state["wave"] == 10 and game_state["boss_dead"] and len(boss_group) == 0:
            game_state["victory"] = True

    # --- DRAW EVERYTHING ---
    screen.fill(COLOR_BG)

    # Draw all sprites (player, bullets, enemies, etc.)
    for sprite in all_sprites:
        screen.blit(sprite.image, sprite.rect)

    # Draw per‐entity health bars
    for e in enemy_sprites:
        e.draw_health_bar(screen)
    for t in tank_sprites:
        t.draw_health_bar(screen)
    for s in sniper_sprites:
        s.draw_health_bar(screen)
    for bobj in boss_group:
        bobj.draw_health_bar(screen)

    # Draw LaserShip lasers
    for ls in laser_sprites:
        ls.draw_horizontal_laser(screen)

    # Draw Explosions
    for ex in explosion_sprites:
        ex.draw(screen)

    # Draw player lives (hearts)
    heart = pygame.Surface((20, 20))
    heart.fill(COLOR_PLAYER)
    font = pygame.font.SysFont("Consolas", 24)
    # instead of creating a Surface and fill, just blit heart images:
    for i in range(player.lives):
        screen.blit(heart_full_img, (10 + i * (HEART_SIZE[0] + 5), 10))
    for i in range(player.lives, PLAYER_LIVES):
        screen.blit(heart_empty_img, (10 + i * (HEART_SIZE[0] + 5), 10))

    # Draw wave indicator
    wave_text = f"Wave {game_state['wave'] if game_state['wave'] <= 10 else 10}"
    wave_surf = font.render(wave_text, True, (255, 255, 0))
    screen.blit(wave_surf, (SCREEN_WIDTH - 150, 10))

    # Draw paused / game over / victory messages
    if game_state["paused"]:
        pause_surf = font.render("PAUSED - Press P to Resume", True, COLOR_PAUSED)
        screen.blit(pause_surf, (SCREEN_WIDTH // 2 - pause_surf.get_width() // 2,
                                 SCREEN_HEIGHT // 2 - pause_surf.get_height() // 2))
    if game_state["game_over"]:
        over_surf = font.render("GAME OVER - Press Esc to Quit or R to Restart", True, (255, 50, 50))
        screen.blit(over_surf, (SCREEN_WIDTH // 2 - over_surf.get_width() // 2,
                                SCREEN_HEIGHT // 2 - over_surf.get_height() // 2))
    if game_state["victory"]:
        win_surf = font.render("YOU WIN! - Press Esc to Quit or R to Restart", True, (50, 255, 50))
        screen.blit(win_surf, (SCREEN_WIDTH // 2 - win_surf.get_width() // 2,
                               SCREEN_HEIGHT // 2 - win_surf.get_height() // 2))

    pygame.display.flip()

pygame.quit()
sys.exit()

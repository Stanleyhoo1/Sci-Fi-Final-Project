import pygame
import sys
import random
import math

# --- SETTINGS ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Player settings
PLAYER_SPEED = 5
PLAYER_LIVES = 3
PLAYER_COOLDOWN = 150      # reduced for more frequent shooting
PLAYER_INVULNERABILITY = 1000  # ms after hit

PLAYER_BULLET_SPEED = -8
PLAYER_BULLET_DAMAGE = 1

# Enemy bullet types
ENEMY_BULLET_FAST_SPEED = 8   # thin, fast
ENEMY_BULLET_FAST_DAMAGE = 1
ENEMY_BULLET_SLOW_SPEED = 3   # big, slow
ENEMY_BULLET_SLOW_DAMAGE = 2

# Homing bullet settings
HOMING_STRENGTH = 0.05  # how strongly it steers each frame
HOMING_SPEED = 5
HOMING_DAMAGE = 1
HOMING_SIZE = (6, 12)
HOMING_COLOR = (0, 200, 200)

# Kamikaze settings
KAMIKAZE_SPEED_DESCEND = 2    # initial downward
KAMIKAZE_SPEED_HOME = 4       # homing speed

# Wave timings
WAVE_DELAY = 1500  # ms before next wave

# Laser settings
LASER_WARNING_DURATION = 1000  # ms warning
LASER_ACTIVE_DURATION = 1000   # ms active
LASER_DELAY = 5000             # ms between lasers
LANE_WIDTH = 80                # 10 lanes

# Colors
COLOR_BG = (10, 10, 30)
COLOR_PLAYER = (50, 200, 50)
COLOR_PLAYER_BULLET = (200, 200, 50)
COLOR_ENEMY = (200, 50, 50)
COLOR_HEAVY_ENEMY = (150, 50, 150)
COLOR_KAMIKAZE = (255, 0, 0)
COLOR_BOSS = (150, 50, 200)
COLOR_ENEMY_BULLET_FAST = (255, 100, 0)
COLOR_ENEMY_BULLET_SLOW = (200, 200, 0)
COLOR_HEALTH_BG = (80, 80, 80)
COLOR_HEALTH_FORE = (50, 255, 50)
COLOR_PAUSED = (255, 255, 255)
COLOR_PLAYER_FLASH = (255, 0, 0)
COLOR_LASER_WARNING = (255, 0, 0)
COLOR_LASER_ACTIVE = (255, 0, 200)

# ----------------------------------------------------------------------
# PLAYER CLASS
# ----------------------------------------------------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.base_image = pygame.Surface((40, 30))
        self.base_image.fill(COLOR_PLAYER)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20))
        self.speed = PLAYER_SPEED
        self.last_shot = 0
        self.lives = PLAYER_LIVES
        self.invulnerable = False
        self.invuln_start = 0

    def update(self, now, paused):
        if paused or game_state["game_over"] or (game_state["wave"] == 4 and game_state["boss_dead"]):
            return

        # Handle invulnerability flashing
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
    def __init__(self, x, y, speed, damage, color, size=(6, 12)):
        super().__init__()
        self.image = pygame.Surface(size)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed
        self.damage = damage
        self.velocity = None  # For angled/homing

    def update(self, paused):
        if paused:
            return

        if self.velocity:
            self.rect.x += int(self.velocity.x)
            self.rect.y += int(self.velocity.y)
            # Homing adjustment
            if isinstance(self, HomingBullet):
                self.adjust_homing()
        else:
            self.rect.y += self.speed

        if (self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or
            self.rect.right < 0 or self.rect.left > SCREEN_WIDTH):
            self.kill()

    def adjust_homing(self):
        # Slightly adjust velocity toward player
        dir_to_player = pygame.Vector2(
            player.rect.centerx - self.rect.centerx,
            player.rect.centery - self.rect.centery
        )
        if dir_to_player.length() != 0:
            dir_to_player = dir_to_player.normalize() * HOMING_SPEED
            # Blend current velocity with dir_to_player
            self.velocity = (self.velocity * (1 - HOMING_STRENGTH) +
                             dir_to_player * HOMING_STRENGTH).normalize() * HOMING_SPEED

# ----------------------------------------------------------------------
# HOMING BULLET CLASS
# ----------------------------------------------------------------------
class HomingBullet(Bullet):
    def __init__(self, x, y):
        super().__init__(x, y, 0, HOMING_DAMAGE, HOMING_COLOR, size=HOMING_SIZE)
        # Start with downward
        self.velocity = pygame.Vector2(0, HOMING_SPEED)

# ----------------------------------------------------------------------
# ENEMY CLASS (dodging logic)
# ----------------------------------------------------------------------
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, health, speed, color):
        super().__init__()
        self.health = health
        self.max_health = health
        self.speed = speed
        self.color = color

        self.image = pygame.Surface((34, 28))
        self.image.fill(color)
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

        # Move & bounce within top half
        self.rect.x += int(self.vel.x)
        self.rect.y += int(self.vel.y)
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.vel.x *= -1
            self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - self.rect.width))
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT // 2:
            self.vel.y *= -1
            self.rect.y = max(0, min(self.rect.y, SCREEN_HEIGHT // 2 - self.rect.height))

        # Auto‐shoot: 80% chance normal, 20% homing
        if now - self.last_shot >= self.shoot_delay:
            self.last_shot = now
            if random.random() < 0.2:
                # Fire homing bullet
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
                       COLOR_ENEMY_BULLET_SLOW, size=(12, 24))
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
# HEAVY ENEMY (slower, higher HP, dodging + homing chance)
# ----------------------------------------------------------------------
class HeavyEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, health=8, speed=2, color=COLOR_HEAVY_ENEMY)
        self.shoot_delay = random.randint(2000, 3500)

# ----------------------------------------------------------------------
# KAMIKAZE SHIP (dive then home)
# ----------------------------------------------------------------------
class Kamikaze(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(COLOR_KAMIKAZE)
        self.rect = self.image.get_rect(center=(x, y))
        self.state = "descending"
        self.speed_descend = KAMIKAZE_SPEED_DESCEND
        self.speed_home = KAMIKAZE_SPEED_HOME

    def update(self, now, paused):
        if paused or game_state["game_over"]:
            return

        if self.state == "descending":
            self.rect.y += self.speed_descend
            if self.rect.y >= SCREEN_HEIGHT // 4:
                self.state = "homing"
        elif self.state == "homing":
            dir_vec = pygame.Vector2(
                player.rect.centerx - self.rect.centerx,
                player.rect.centery - self.rect.centery
            )
            if dir_vec.length() != 0:
                dir_vec = dir_vec.normalize()
                self.rect.x += int(dir_vec.x * self.speed_home)
                self.rect.y += int(dir_vec.y * self.speed_home)

            if self.rect.colliderect(player.rect):
                player.hit()
                self.kill()

        if (self.rect.top > SCREEN_HEIGHT or self.rect.left > SCREEN_WIDTH or
            self.rect.right < 0 or self.rect.bottom < 0):
            self.kill()

# ----------------------------------------------------------------------
# BOSS CLASS (vertical lasers + more health)
# ----------------------------------------------------------------------
class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.health = 120
        self.max_health = 120
        self.image = pygame.Surface((400, 200))
        self.image.fill(COLOR_BOSS)
        self.rect = self.image.get_rect(midtop=(SCREEN_WIDTH // 2, -200))
        self.state = "entering"
        self.speed_x = 2
        self.last_shot = 0
        self.shoot_delay = 1000  # ms

        # Laser logic
        self.last_laser = 0
        self.laser_delay = LASER_DELAY
        self.laser_warning = False
        self.laser_warning_start = 0
        self.laser_active = False
        self.laser_active_start = 0
        self.laser_lanes = []

        self.pattern_index = 0

    def update(self, now, paused):
        if paused or game_state["game_over"]:
            return

        if self.state == "entering":
            if self.rect.top < 50:
                self.rect.y += 2
            else:
                self.state = "fighting"

        elif self.state == "fighting":
            self.rect.x += self.speed_x
            if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
                self.speed_x *= -1

            # Laser warning
            if not self.laser_warning and not self.laser_active and now - self.last_laser >= self.laser_delay:
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
                if now - self.last_shot >= self.shoot_delay:
                    self.last_shot = now
                    self.fire_pattern()
                    self.pattern_index = (self.pattern_index + 1) % 3

            if self.health <= 0:
                self.state = "dying"

        elif self.state == "dying":
            self.rect.y -= 4
            if self.rect.bottom < 0:
                self.kill()
                game_state["boss_dead"] = True

    def pick_laser_lanes(self):
        total_lanes = SCREEN_WIDTH // LANE_WIDTH  # 10 lanes of 80px
        k = random.randint(1, 3)
        all_idx = list(range(total_lanes))
        self.laser_lanes = random.sample(all_idx, k)

    def fire_pattern(self):
        if self.pattern_index == 0:
            angles = [-0.6, -0.4, -0.2, 0, 0.2, 0.4, 0.6]
            for ang in angles:
                direction = pygame.Vector2(ang, 1).normalize()
                b = Bullet(self.rect.centerx, self.rect.bottom,
                           0, 1, COLOR_ENEMY_BULLET_FAST, size=(4, 10))
                b.velocity = direction * ENEMY_BULLET_FAST_SPEED
                all_sprites.add(b)
                enemy_bullets.add(b)

        elif self.pattern_index == 1:
            offsets = [-80, 0, 80]
            for off in offsets:
                b = Bullet(self.rect.centerx + off, self.rect.bottom,
                           ENEMY_BULLET_SLOW_SPEED, 2, COLOR_ENEMY_BULLET_SLOW, size=(12, 24))
                all_sprites.add(b)
                enemy_bullets.add(b)

        elif self.pattern_index == 2:
            for i in range(12):
                angle = (i * (2 * math.pi / 12)) + math.pi / 2
                direction = pygame.Vector2(math.cos(angle), math.sin(angle)).normalize()
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
                    player.hit()

# ----------------------------------------------------------------------
# INITIALIZE PYGAME AND GROUPS
# ----------------------------------------------------------------------
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Alien Invasion Defender – Vertical Lasers & Diving Kamikaze")
clock = pygame.time.Clock()

all_sprites = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
enemy_sprites = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
kamikaze_sprites = pygame.sprite.Group()
boss_group = pygame.sprite.Group()

# ----------------------------------------------------------------------
# SET UP PLAYER
# ----------------------------------------------------------------------
player = Player()
all_sprites.add(player)

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
}

# ----------------------------------------------------------------------
# START NEXT WAVE
# ----------------------------------------------------------------------
def start_wave(n):
    now = pygame.time.get_ticks()
    game_state["wave_start_time"] = now

    if n == 1:
        # Wave 1: 6 enemies + 2 kamikaze
        for _ in range(6):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(20, SCREEN_HEIGHT // 2 - 50)
            e = Enemy(x, y, health=2, speed=2, color=COLOR_ENEMY)
            all_sprites.add(e)
            enemy_sprites.add(e)
        for _ in range(2):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = -20
            k = Kamikaze(x, y)
            all_sprites.add(k)
            kamikaze_sprites.add(k)

    elif n == 2:
        # Wave 2: 4 heavy + 4 regular + 3 kamikaze
        for _ in range(4):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(20, SCREEN_HEIGHT // 2 - 50)
            he = HeavyEnemy(x, y)
            all_sprites.add(he)
            enemy_sprites.add(he)
        for _ in range(4):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(20, SCREEN_HEIGHT // 2 - 50)
            e = Enemy(x, y, health=2, speed=3, color=COLOR_ENEMY)
            all_sprites.add(e)
            enemy_sprites.add(e)
        for _ in range(3):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = -20
            k = Kamikaze(x, y)
            all_sprites.add(k)
            kamikaze_sprites.add(k)

    elif n == 3:
        # Wave 3: 8 fast scouts + 4 kamikaze
        for _ in range(8):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(20, SCREEN_HEIGHT // 2 - 50)
            e = Enemy(x, y, health=1, speed=4, color=COLOR_ENEMY)
            all_sprites.add(e)
            enemy_sprites.add(e)
        for _ in range(4):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = -20
            k = Kamikaze(x, y)
            all_sprites.add(k)
            kamikaze_sprites.add(k)

    elif n == 4:
        # Wave 4: boss
        boss = Boss()
        all_sprites.add(boss)
        boss_group.add(boss)

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
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_p:
                game_state["paused"] = not game_state["paused"]

    # --- Manage Waves ---
    if not (game_state["game_over"] or game_state["victory"] or game_state["paused"]):
        wave = game_state["wave"]
        elapsed = now - game_state["wave_start_time"]
        if wave == 0 and elapsed > WAVE_DELAY:
            game_state["wave"] = 1
            start_wave(1)
        elif wave == 1 and len(enemy_sprites) + len(kamikaze_sprites) == 0 and elapsed > WAVE_DELAY:
            game_state["wave"] = 2
            start_wave(2)
        elif wave == 2 and len(enemy_sprites) + len(kamikaze_sprites) == 0 and elapsed > WAVE_DELAY:
            game_state["wave"] = 3
            start_wave(3)
        elif wave == 3 and len(enemy_sprites) + len(kamikaze_sprites) == 0 and elapsed > WAVE_DELAY:
            game_state["wave"] = 4
            start_wave(4)

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
    for bobj in boss_group:
        bobj.update(now, game_state["paused"])

    # --- Collision Detection ---
    if not (game_state["paused"] or game_state["game_over"] or game_state["victory"]):
        # Player bullets vs. enemies
        for e in enemy_sprites:
            hits = pygame.sprite.spritecollide(e, player_bullets, True)
            for b in hits:
                e.health -= b.damage
                if e.health <= 0:
                    e.kill()

        # Player bullets vs. boss
        for bullet in player_bullets:
            boss_hits = pygame.sprite.spritecollide(bullet, boss_group, False)
            for boss_obj in boss_hits:
                bullet.kill()
                boss_obj.health -= bullet.damage
                if boss_obj.health <= 0 and boss_obj.state == "fighting":
                    boss_obj.state = "dying"

        # Enemy bullets vs. player
        hits = pygame.sprite.spritecollide(player, enemy_bullets, True)
        if hits:
            player.hit()

        # Enemy ships vs. player
        hits = pygame.sprite.spritecollide(player, enemy_sprites, False)
        if hits:
            for e in hits:
                e.kill()
            player.hit()

        # Kamikaze vs. player handled in Kamikaze.update

        # Boss vs. player
        hits = pygame.sprite.spritecollide(player, boss_group, False)
        if hits:
            player.hit()

        # Victory check
        if game_state["wave"] == 4 and game_state["boss_dead"] and len(boss_group) == 0:
            game_state["victory"] = True

    # --- DRAW EVERYTHING ---
    screen.fill(COLOR_BG)

    for sprite in all_sprites:
        screen.blit(sprite.image, sprite.rect)

    for e in enemy_sprites:
        e.draw_health_bar(screen)
    for bobj in boss_group:
        bobj.draw_health_bar(screen)
        bobj.draw_laser(screen)

    heart = pygame.Surface((20, 20))
    heart.fill(COLOR_PLAYER)
    font = pygame.font.SysFont("Consolas", 24)
    for i in range(player.lives):
        screen.blit(heart, (10 + i * 30, 10))
    for i in range(player.lives, PLAYER_LIVES):
        outline_rect = pygame.Rect(10 + i * 30, 10, 20, 20)
        pygame.draw.rect(screen, COLOR_HEALTH_BG, outline_rect, 2)

    wave_text = f"Wave {game_state['wave'] if game_state['wave'] < 5 else 4}"
    wave_surf = font.render(wave_text, True, (255, 255, 0))
    screen.blit(wave_surf, (SCREEN_WIDTH - 150, 10))

    if game_state["paused"]:
        pause_surf = font.render("PAUSED – Press P to Resume", True, COLOR_PAUSED)
        screen.blit(pause_surf, (SCREEN_WIDTH // 2 - pause_surf.get_width() // 2,
                                 SCREEN_HEIGHT // 2 - pause_surf.get_height() // 2))
    if game_state["game_over"]:
        over_surf = font.render("GAME OVER – Press Esc to Quit", True, (255, 50, 50))
        screen.blit(over_surf, (SCREEN_WIDTH // 2 - over_surf.get_width() // 2,
                                SCREEN_HEIGHT // 2 - over_surf.get_height() // 2))
    if game_state["victory"]:
        win_surf = font.render("YOU WIN! – Press Esc to Quit", True, (50, 255, 50))
        screen.blit(win_surf, (SCREEN_WIDTH // 2 - win_surf.get_width() // 2,
                               SCREEN_HEIGHT // 2 - win_surf.get_height() // 2))

    pygame.display.flip()

pygame.quit()
sys.exit()

import pygame
import asyncio
import platform
import math
import random
import time

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
WORLD_WIDTH, WORLD_HEIGHT = 2400, 1600
FPS = 60
PLAYER_RADIUS = 10
HEAD_RADIUS = 5
SHIELD_RADIUS = 15
PLAYER_SPEED = 200
BULLET_SPEED = 300
FIRE_RATE = 0.2
BLOCK_SIZE = 40
BLOCK_SPEED = 100
RED_CIRCLE_RADIUS = 15
RED_CIRCLE_SPEED = 100
TRIANGLE_SIZE = 20
TRIANGLE_SPEED = 50
TRIANGLE_FIRE_RATE = 3
INITIAL_BLOCKS = 16
MAX_BLOCKS = 30
SPAWN_INTERVAL = 5
SHIELD_DURATION = 5
MAX_SHIELDS = 5
NUM_TRIANGLES = 2
POWERUP_SIZE = 20
POWERUP_SPAWN_INTERVAL = 10
MAX_POWERUPS = 2
PARTICLE_LIFETIME = 0.5
GRID_SIZE = 50

# Colors
ORANGE = (255, 165, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GRAY = (100, 100, 100)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)

# Setup display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("2D Circle Game")
clock = pygame.time.Clock()

# Fonts
font = pygame.font.SysFont(None, 24)
ui_font = pygame.font.SysFont(None, 36)

# Player
player_pos = [WORLD_WIDTH / 2, WORLD_HEIGHT / 2]
player_velocity = [0, 0]
last_direction = [1, 0]
shield_active = False
shield_timer = 0
shield_uses = MAX_SHIELDS
speed_boost_active = False
speed_boost_timer = 0
current_player_speed = PLAYER_SPEED
score = 0

# Bullets
class Bullet:
    def __init__(self, x, y, direction):
        self.pos = [x, y]
        self.velocity = [direction[0] * BULLET_SPEED, direction[1] * BULLET_SPEED]
        self.text = font.render("->", True, WHITE)
        self.rect = self.text.get_rect(center=(x, y))

# Enemy Bullets
class EnemyBullet:
    def __init__(self, x, y, direction):
        self.pos = [x, y]
        self.velocity = [direction[0] * BULLET_SPEED, direction[1] * BULLET_SPEED]
        self.text = font.render("<=", True, WHITE)
        self.rect = self.text.get_rect(center=(x, y))

# Blocks
class Block:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)
        self.hit_points = 5
        self.direction = random.randint(0, 3)
        self.velocity = [
            [0, -BLOCK_SPEED], [0, BLOCK_SPEED],
            [-BLOCK_SPEED, 0], [BLOCK_SPEED, 0]
        ][self.direction]

# Red Circles
class RedCircle:
    def __init__(self, x, y):
        self.pos = [x, y]
        self.radius = RED_CIRCLE_RADIUS
        self.rect = pygame.Rect(x - RED_CIRCLE_RADIUS, y - RED_CIRCLE_RADIUS,
                               RED_CIRCLE_RADIUS * 2, RED_CIRCLE_RADIUS * 2)

# Triangles
class Triangle:
    def __init__(self, x, y):
        self.pos = [x, y]
        self.direction = random.randint(0, 3)
        self.velocity = [
            [0, -TRIANGLE_SPEED], [0, TRIANGLE_SPEED],
            [-TRIANGLE_SPEED, 0], [TRIANGLE_SPEED, 0]
        ][self.direction]
        self.rect = pygame.Rect(x - TRIANGLE_SIZE / 2, y - TRIANGLE_SIZE / 2,
                               TRIANGLE_SIZE, TRIANGLE_SIZE)
        self.fire_timer = random.uniform(0, TRIANGLE_FIRE_RATE)

# Power-Ups
class PowerUp:
    def __init__(self, x, y, type):
        self.pos = [x, y]
        self.type = type  # "speed" or "shield"
        self.rect = pygame.Rect(x - POWERUP_SIZE / 2, y - POWERUP_SIZE / 2,
                               POWERUP_SIZE, POWERUP_SIZE)

# Particles
class Particle:
    def __init__(self, x, y):
        self.pos = [x, y]
        self.velocity = [random.uniform(-50, 50), random.uniform(-50, 50)]
        self.lifetime = PARTICLE_LIFETIME
        self.radius = random.randint(2, 4)

# Game state
bullets = []
enemy_bullets = []
blocks = []
red_circles = []
triangles = []
powerups = []
particles = []
game_over = False
fire_timer = 0
spawn_timer = 0
powerup_spawn_timer = 0
start_time = time.time()
survival_time = 0

def get_camera_offset():
    offset_x = player_pos[0] - SCREEN_WIDTH / 2
    offset_y = player_pos[1] - SCREEN_HEIGHT / 2
    offset_x = max(0, min(offset_x, WORLD_WIDTH - SCREEN_WIDTH))
    offset_y = max(0, min(offset_y, WORLD_HEIGHT - SCREEN_HEIGHT))
    return offset_x, offset_y

def spawn_blocks(count):
    for _ in range(count):
        if len(blocks) >= MAX_BLOCKS:
            return
        while True:
            x = random.randint(0, WORLD_WIDTH - BLOCK_SIZE)
            y = random.randint(0, WORLD_HEIGHT - BLOCK_SIZE)
            new_rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)
            player_rect = pygame.Rect(player_pos[0] - PLAYER_RADIUS, player_pos[1] - PLAYER_RADIUS,
                                     PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)
            if not new_rect.colliderect(player_rect):
                blocks.append(Block(x, y))
                break

def spawn_red_circles():
    target_count = len(blocks) // 2
    red_circles.clear()
    for _ in range(target_count):
        while True:
            x = random.randint(0, WORLD_WIDTH - RED_CIRCLE_RADIUS * 2)
            y = random.randint(0, WORLD_HEIGHT - RED_CIRCLE_RADIUS * 2)
            new_rect = pygame.Rect(x, y, RED_CIRCLE_RADIUS * 2, RED_CIRCLE_RADIUS * 2)
            player_rect = pygame.Rect(player_pos[0] - PLAYER_RADIUS, player_pos[1] - PLAYER_RADIUS,
                                     PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)
            if not new_rect.colliderect(player_rect):
                red_circles.append(RedCircle(x + RED_CIRCLE_RADIUS, y + RED_CIRCLE_RADIUS))
                break

def spawn_triangles():
    while len(triangles) < NUM_TRIANGLES:
        while True:
            x = random.randint(0, WORLD_WIDTH - TRIANGLE_SIZE)
            y = random.randint(0, WORLD_HEIGHT - TRIANGLE_SIZE)
            new_rect = pygame.Rect(x, y, TRIANGLE_SIZE, TRIANGLE_SIZE)
            player_rect = pygame.Rect(player_pos[0] - PLAYER_RADIUS, player_pos[1] - PLAYER_RADIUS,
                                     PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)
            if not new_rect.colliderect(player_rect):
                triangles.append(Triangle(x + TRIANGLE_SIZE / 2, y + TRIANGLE_SIZE / 2))
                break

def spawn_powerup():
    if len(powerups) >= MAX_POWERUPS:
        return
    while True:
        x = random.randint(0, WORLD_WIDTH - POWERUP_SIZE)
        y = random.randint(0, WORLD_HEIGHT - POWERUP_SIZE)
        new_rect = pygame.Rect(x, y, POWERUP_SIZE, POWERUP_SIZE)
        player_rect = pygame.Rect(player_pos[0] - PLAYER_RADIUS, player_pos[1] - PLAYER_RADIUS,
                                 PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)
        if not new_rect.colliderect(player_rect):
            type = random.choice(["speed", "shield"])
            powerups.append(PowerUp(x + POWERUP_SIZE / 2, y + POWERUP_SIZE / 2, type))
            break

def spawn_particles(x, y, count=5):
    for _ in range(count):
        particles.append(Particle(x, y))

def setup():
    global screen, clock, player_pos, game_over, fire_timer, spawn_timer, powerup_spawn_timer, start_time, survival_time
    global shield_active, shield_timer, shield_uses, speed_boost_active, speed_boost_timer, current_player_speed, score
    global bullets, enemy_bullets, blocks, red_circles, triangles, powerups, particles, last_direction
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2D Circle Game")
    clock = pygame.time.Clock()
    player_pos = [WORLD_WIDTH / 2, WORLD_HEIGHT / 2]
    last_direction = [1, 0]
    game_over = False
    fire_timer = 0
    spawn_timer = 0
    powerup_spawn_timer = 0
    start_time = time.time()
    survival_time = 0
    shield_active = False
    shield_timer = 0
    shield_uses = MAX_SHIELDS
    speed_boost_active = False
    speed_boost_timer = 0
    current_player_speed = PLAYER_SPEED
    score = 0
    bullets.clear()
    enemy_bullets.clear()
    blocks.clear()
    red_circles.clear()
    triangles.clear()
    powerups.clear()
    particles.clear()
    spawn_blocks(INITIAL_BLOCKS)
    spawn_red_circles()
    spawn_triangles()
    spawn_powerup()

def get_head_position():
    offset = PLAYER_RADIUS + HEAD_RADIUS
    head_x = player_pos[0] + last_direction[0] * offset
    head_y = player_pos[1] + last_direction[1] * offset
    return (head_x, head_y)

def update_loop():
    global player_pos, player_velocity, fire_timer, game_over, bullets, enemy_bullets, blocks, red_circles, triangles
    global last_direction, spawn_timer, powerup_spawn_timer, survival_time, shield_active, shield_timer, shield_uses
    global speed_boost_active, speed_boost_timer, current_player_speed, score, powerups, particles

    # Delta time
    delta_time = clock.tick(FPS) / 1000.0

    # Update survival time
    if not game_over:
        survival_time = time.time() - start_time

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            return
        if event.type == pygame.KEYDOWN:
            if game_over and event.key == pygame.K_r:
                setup()  # Restart game
            if not game_over and event.key == pygame.K_p and shield_uses > 0:
                shield_active = True
                shield_timer = SHIELD_DURATION
                shield_uses -= 1

    if not game_over:
        # Update shield
        if shield_active:
            shield_timer -= delta_time
            if shield_timer <= 0:
                shield_active = False

        # Update speed boost
        if speed_boost_active:
            speed_boost_timer -= delta_time
            if speed_boost_timer <= 0:
                speed_boost_active = False
                current_player_speed = PLAYER_SPEED

        # Handle input for 360-degree movement
        player_velocity = [0, 0]
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_RIGHT]:
            dx += 1

        # Calculate movement direction
        if dx != 0 or dy != 0:
            angle = math.atan2(dy, dx)
            player_velocity = [math.cos(angle) * current_player_speed, math.sin(angle) * current_player_speed]
            last_direction = [math.cos(angle), math.sin(angle)]
        else:
            player_velocity = [0, 0]

        # Move player
        player_pos[0] += player_velocity[0] * delta_time
        player_pos[1] += player_velocity[1] * delta_time

        # Keep player in world bounds
        player_pos[0] = max(PLAYER_RADIUS, min(WORLD_WIDTH - PLAYER_RADIUS, player_pos[0]))
        player_pos[1] = max(PLAYER_RADIUS, min(WORLD_HEIGHT - PLAYER_RADIUS, player_pos[1]))

        # Shooting from head
        fire_timer += delta_time
        if keys[pygame.K_SPACE] and fire_timer >= FIRE_RATE:
            head_pos = get_head_position()
            bullet = Bullet(head_pos[0], head_pos[1], last_direction)
            bullets.append(bullet)
            fire_timer = 0

        # Update bullets
        bullets = [b for b in bullets if 0 <= b.pos[0] <= WORLD_WIDTH and 0 <= b.pos[1] <= WORLD_HEIGHT]
        for bullet in bullets:
            bullet.pos[0] += bullet.velocity[0] * delta_time
            bullet.pos[1] += bullet.velocity[1] * delta_time
            bullet.rect.center = bullet.pos

        # Update enemy bullets
        enemy_bullets = [b for b in enemy_bullets if 0 <= b.pos[0] <= WORLD_WIDTH and 0 <= b.pos[1] <= WORLD_HEIGHT]
        for bullet in enemy_bullets:
            bullet.pos[0] += bullet.velocity[0] * delta_time
            bullet.pos[1] += bullet.velocity[1] * delta_time
            bullet.rect.center = bullet.pos

        # Update blocks
        spawn_timer += delta_time
        if spawn_timer >= SPAWN_INTERVAL:
            spawn_blocks(1)
            spawn_red_circles()
            spawn_timer = 0

        for block in blocks:
            block.rect.x += block.velocity[0] * delta_time
            block.rect.y += block.velocity[1] * delta_time
            if block.rect.left < 0:
                block.rect.left = 0
                block.velocity[0] = -block.velocity[0]
            elif block.rect.right > WORLD_WIDTH:
                block.rect.right = WORLD_WIDTH
                block.velocity[0] = -block.velocity[0]
            if block.rect.top < 0:
                block.rect.top = 0
                block.velocity[1] = -block.velocity[1]
            elif block.rect.bottom > WORLD_HEIGHT:
                block.rect.bottom = WORLD_HEIGHT
                block.velocity[1] = -block.velocity[1]

        # Update red circles
        for circle in red_circles:
            dx = player_pos[0] - circle.pos[0]
            dy = player_pos[1] - circle.pos[1]
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 0:
                circle.pos[0] += (dx / distance) * RED_CIRCLE_SPEED * delta_time
                circle.pos[1] += (dy / distance) * RED_CIRCLE_SPEED * delta_time
            circle.rect.center = circle.pos

        # Update triangles
        for triangle in triangles:
            triangle.rect.x += triangle.velocity[0] * delta_time
            triangle.rect.y += triangle.velocity[1] * delta_time
            if triangle.rect.left < 0:
                triangle.rect.left = 0
                triangle.velocity[0] = -triangle.velocity[0]
            elif triangle.rect.right > WORLD_WIDTH:
                triangle.rect.right = WORLD_WIDTH
                triangle.velocity[0] = -triangle.velocity[0]
            if triangle.rect.top < 0:
                triangle.rect.top = 0
                triangle.velocity[1] = -triangle.velocity[1]
            elif triangle.rect.bottom > WORLD_HEIGHT:
                triangle.rect.bottom = WORLD_HEIGHT
                triangle.velocity[1] = -triangle.velocity[1]
            triangle.fire_timer += delta_time
            if triangle.fire_timer >= TRIANGLE_FIRE_RATE:
                dx = player_pos[0] - triangle.pos[0]
                dy = player_pos[1] - triangle.pos[1]
                distance = math.sqrt(dx**2 + dy**2)
                if distance > 0:
                    direction = [dx / distance, dy / distance]
                    enemy_bullets.append(EnemyBullet(triangle.pos[0], triangle.pos[1], direction))
                triangle.fire_timer = 0

        # Update power-ups
        powerup_spawn_timer += delta_time
        if powerup_spawn_timer >= POWERUP_SPAWN_INTERVAL:
            spawn_powerup()
            powerup_spawn_timer = 0

        # Update particles
        particles[:] = [p for p in particles if p.lifetime > 0]
        for particle in particles:
            particle.pos[0] += particle.velocity[0] * delta_time
            particle.pos[1] += particle.velocity[1] * delta_time
            particle.lifetime -= delta_time

        # Respawn triangles
        spawn_triangles()

        # Collision detection: player with blocks, red circles, triangles, enemy bullets, and power-ups
        player_rect = pygame.Rect(player_pos[0] - PLAYER_RADIUS, player_pos[1] - PLAYER_RADIUS,
                                 PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)
        if not shield_active:
            for block in blocks:
                if player_rect.colliderect(block.rect):
                    game_over = True
            for circle in red_circles:
                if player_rect.colliderect(circle.rect):
                    game_over = True
            for triangle in triangles:
                if player_rect.colliderect(triangle.rect):
                    game_over = True
            for bullet in enemy_bullets:
                if player_rect.colliderect(bullet.rect):
                    game_over = True

        for powerup in powerups[:]:
            if player_rect.colliderect(powerup.rect):
                if powerup.type == "speed":
                    speed_boost_active = True
                    speed_boost_timer = 5
                    current_player_speed = PLAYER_SPEED * 1.5
                elif powerup.type == "shield" and shield_uses < MAX_SHIELDS:
                    shield_uses += 1
                powerups.remove(powerup)

        # Collision detection: player bullets with blocks, red circles, and triangles
        for bullet in bullets[:]:
            hit = False
            for block in blocks[:]:
                if bullet.rect.colliderect(block.rect):
                    block.hit_points -= 1
                    if block.hit_points <= 0:
                        spawn_particles(block.rect.centerx, block.rect.centery)
                        score += 100
                    bullets.remove(bullet)
                    hit = True
                    break
            if not hit:
                for circle in red_circles[:]:
                    if bullet.rect.colliderect(circle.rect):
                        spawn_particles(circle.pos[0], circle.pos[1])
                        red_circles.remove(circle)
                        bullets.remove(bullet)
                        score += 50
                        hit = True
                        break
            if not hit:
                for triangle in triangles[:]:
                    if bullet.rect.colliderect(triangle.rect):
                        spawn_particles(triangle.pos[0], triangle.pos[1])
                        triangles.remove(triangle)
                        bullets.remove(bullet)
                        score += 75
                        break
        blocks = [b for b in blocks if b.hit_points > 0]

    # Render
    screen.fill(BLACK)
    offset_x, offset_y = get_camera_offset()

    # Draw background grid
    for x in range(0, WORLD_WIDTH, GRID_SIZE):
        pygame.draw.line(screen, GRAY, (x - offset_x, 0), (x - offset_x, SCREEN_HEIGHT), 1)
    for y in range(0, WORLD_HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, GRAY, (0, y - offset_y), (SCREEN_WIDTH, y - offset_y), 1)

    # Draw player body, head, and shield
    player_screen_pos = (player_pos[0] - offset_x, player_pos[1] - offset_y)
    pygame.draw.circle(screen, ORANGE, player_screen_pos, PLAYER_RADIUS)
    head_pos = get_head_position()
    head_screen_pos = (head_pos[0] - offset_x, head_pos[1] - offset_y)
    pygame.draw.circle(screen, ORANGE, head_screen_pos, HEAD_RADIUS)
    if shield_active:
        pygame.draw.circle(screen, CYAN, player_screen_pos, SHIELD_RADIUS, 2)

    # Draw bullets
    for bullet in bullets:
        screen_pos = (bullet.pos[0] - offset_x, bullet.pos[1] - offset_y)
        screen.blit(bullet.text, bullet.text.get_rect(center=screen_pos))
    for bullet in enemy_bullets:
        screen_pos = (bullet.pos[0] - offset_x, bullet.pos[1] - offset_y)
        screen.blit(bullet.text, bullet.text.get_rect(center=screen_pos))

    # Draw blocks and health bars
    for block in blocks:
        screen_rect = pygame.Rect(block.rect.x - offset_x, block.rect.y - offset_y,
                                 block.rect.width, block.rect.height)
        pygame.draw.rect(screen, GREEN, screen_rect)
        health_width = (block.hit_points / 5) * BLOCK_SIZE
        health_rect = pygame.Rect(block.rect.x - offset_x, block.rect.y - offset_y - 10,
                                 health_width, 5)
        pygame.draw.rect(screen, RED, health_rect)
        pygame.draw.rect(screen, GRAY, (block.rect.x - offset_x, block.rect.y - offset_y - 10,
                                        BLOCK_SIZE, 5), 1)

    # Draw red circles
    for circle in red_circles:
        screen_pos = (circle.pos[0] - offset_x, circle.pos[1] - offset_y)
        pygame.draw.circle(screen, RED, screen_pos, RED_CIRCLE_RADIUS)

    # Draw triangles
    for triangle in triangles:
        screen_pos = (triangle.pos[0] - offset_x, triangle.pos[1] - offset_y)
        points = [
            (screen_pos[0], screen_pos[1] - TRIANGLE_SIZE / 2),
            (screen_pos[0] - TRIANGLE_SIZE / 2, screen_pos[1] + TRIANGLE_SIZE / 2),
            (screen_pos[0] + TRIANGLE_SIZE / 2, screen_pos[1] + TRIANGLE_SIZE / 2)
        ]
        pygame.draw.polygon(screen, RED, points)

    # Draw power-ups
    for powerup in powerups:
        screen_rect = pygame.Rect(powerup.pos[0] - offset_x - POWERUP_SIZE / 2,
                                 powerup.pos[1] - offset_y - POWERUP_SIZE / 2,
                                 POWERUP_SIZE, POWERUP_SIZE)
        pygame.draw.rect(screen, BLUE, screen_rect)
        text = font.render("S" if powerup.type == "speed" else "P", True, WHITE)
        screen.blit(text, text.get_rect(center=screen_rect.center))

    # Draw particles
    for particle in particles:
        screen_pos = (particle.pos[0] - offset_x, particle.pos[1] - offset_y)
        alpha = int(255 * (particle.lifetime / PARTICLE_LIFETIME))
        color = (WHITE[0], WHITE[1], WHITE[2], alpha)
        pygame.draw.circle(screen, color, screen_pos, particle.radius)

    # Draw UI (fixed to screen)
    if game_over:
        text = ui_font.render(f"Game Over - Score: {score} - Survived: {int(survival_time)}s - Press R to Restart", True, RED)
        text_rect = text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        screen.blit(text, text_rect)
    else:
        score_text = ui_font.render(f"Score: {score}", True, WHITE)
        survival_text = ui_font.render(f"Survival Time: {int(survival_time)}s", True, WHITE)
        shield_text = ui_font.render(f"Shields: {shield_uses}", True, WHITE)
        screen.blit(score_text, (10, 40))
        screen.blit(survival_text, (10, 70))
        screen.blit(shield_text, (10, 100))
    move_text = ui_font.render("Use ARROWS to Move", True, WHITE)
    shoot_text = ui_font.render("Press SPACE to Shoot", True, WHITE)
    shield_text = ui_font.render("Press P for Shield", True, WHITE)
    screen.blit(move_text, (10, 10))
    screen.blit(shoot_text, (10, 130))
    screen.blit(shield_text, (10, 160))
    pygame.display.flip()

async def main():
    setup()
    while True:
        update_loop()
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())

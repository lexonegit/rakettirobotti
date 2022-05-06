"""Rakettirobotti-peli"""
# SOURCE CODE: https://github.com/lexonegit/rakettirobotti
# Made by Leevi (Lexone)

# Controls: 
# WASD/Arrow keys to move
# Mouse to aim and shoot

# NOTE: You need to fly in order to move sideways



import pygame
import random
import math
import sys
import time
from pygame.locals import *

pygame.init()
pygame.font.init()

WINDOW_SIZE = (1600, 900)

display = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption("Game of the year")

# Score variables
totalEnemyKills = 0
gameOver = False


class Player:
    position = pygame.Vector2(0, 0)
    grounded = False
    fuel = 100.0

    def __init__(self, image, startPos):
        self.bodyRect = image.get_rect(center=self.position)
        self.bodyRect.move_ip(startPos)  # Move to starting position
        self.position = startPos

    def rotate_gun(self):
        angle = get_rotation(pygame.math.Vector2(
            pygame.mouse.get_pos()), self.position)

        self.cannonImage = pygame.transform.rotate(img_cannon, int(angle))
        self.cannonRect = self.cannonImage.get_rect(center=self.position)

    def set_position(self, pos):
        self.bodyRect.move_ip(pos)
        self.position = pos
        self.cannonRect = self.cannonImage.get_rect(center=self.position)

    def move(self, movement):
        movement *= playerSpeed  # Apply speed

        if player.grounded:
            movement.x = 0  # Can't move on ground
            player.fuel += 0.75

        if movement != (0, 0):  # Drain fuel if moving
            player.fuel -= 0.4

        if movement.y == 0:  # Apply "gravity"
            movement.y += gravity

        player.fuel = max(min(player.fuel, 100), 0)  # Clamp to 0-100 range

        # Convert to integers, otherwise everything breaks :)
        movement.x = int(movement.x)
        movement.y = int(movement.y)

        player.grounded = move_and_collide(
            player.bodyRect, player.position, movement)
        player.rotate_gun()

        # Exhaust fire "animation"
        if (abs(movement.y) >= playerSpeed or abs(movement.x) >= playerSpeed):
            fire = random.choice(fires)
            rect = fire.get_rect()
            rect.center = player.position - pygame.Vector2(0, -30)
            display.blit(fire, rect)

        self.rotate_gun()


class Explosion:
    position = pygame.Vector2(0, 0)
    lifeTimeCounter = 0

    def __init__(self, image, position):
        self.position = pygame.Vector2(position.x, position.y)
        self.rect = image.get_rect(center=position)


class Bullet:
    position = pygame.Vector2(0, 0)

    def __init__(self, image, position, target, bulletDamage, bulletSpeed, isEnemyBullet):
        self.position = pygame.Vector2(position.x, position.y)
        self.isEnemyBullet = isEnemyBullet

        # Bullet random spread
        spread = 2
        mag = (target - self.position).magnitude() / 20
        target.x += mag * random.randrange(-spread, spread)
        target.y += mag * random.randrange(-spread, spread)

        # Rotate bullet image
        angle = get_rotation(target, position)
        self.image = pygame.transform.rotate(image, int(angle))
        self.rect = self.image.get_rect(center=position)

        # Set flying direction (speed)
        distance = target - self.position
        self.speed = distance.normalize() * bulletSpeed

        # Set bullet damage
        self.bulletDamage = bulletDamage

    def move(self):
        self.position += self.speed
        self.rect.center = self.position

        if self.isEnemyBullet:
            if hit_player(self.rect, self.bulletDamage):
                bullets.remove(self)
                return
        else:
            if hit_enemy(self.rect, self.bulletDamage):
                bullets.remove(self)
                return

        if len(get_collisions(self.rect)) > 0:
            bullets.remove(self)  # Hit static collider

        if (self.position - pygame.Vector2(0, 0)).magnitude() > 3000:
            # Bullet is far off the game screen -> Remove it
            bullets.remove(self)


class Enemy:
    position = pygame.Vector2(0, 0)

    def __init__(self, image, startPos, health, speed, shootRate, bulletSpeed):
        self.image = image
        self.bodyRect = image.get_rect(center=self.position)
        self.bodyRect.move_ip(startPos)  # Move to starting position
        self.position = startPos

        self.movement = pygame.Vector2(0, 0)
        self.speed = speed
        self.maxHealth = health
        self.health = self.maxHealth
        self.shootRate = 10 * random.randrange(shootRate, shootRate + 5)
        self.bulletSpeed = bulletSpeed

    def shoot(self):
        bullets.append(Bullet(img_enemybullet, self.position, pygame.math.Vector2(
            player.position), 10, self.bulletSpeed, True))

    directionChangeTicks = 0
    shootTicks = -75

    def move(self):
        # Check if dead
        if self.health <= 0:
            enemies.remove(self)
            # Death explosion "animation"
            explosions.append(Explosion(random.choice(exp), self.position))

            global totalEnemyKills
            if not gameOver:
                totalEnemyKills += 1  # Add 1 kill to score
            return

        if self.directionChangeTicks % 20 == 0:
            self.movement = pygame.Vector2(
                random.randrange(-1, 2), random.randrange(-1, 2)) * self.speed
            self.directionChangeTicks = 0

        if self.shootTicks % self.shootRate == 0 and not gameOver:
            self.shoot()
            self.shootTicks = 0

        # Health text
        f = round(self.health / self.maxHealth, 2)
        display.blit(font.render(str(int(self.health)), True, Color(255, 0, 0).lerp(
            Color(0, 255, 0), f)), self.position + pygame.Vector2(54, -16))

        move_and_collide(self.bodyRect, self.position, self.movement)

        self.directionChangeTicks += 1
        self.shootTicks += 1
        self.rotate_gun()

    def rotate_gun(self):
        angle = get_rotation(player.position, self.position)

        if gameOver:
            angle = 0

        self.cannonImage = pygame.transform.rotate(img_cannon, int(angle))
        self.cannonRect = self.cannonImage.get_rect(center=self.position)

# FUNCTIONS


def hit_enemy(rect, damage):
    for enemy in enemies:
        if rect.colliderect(enemy.bodyRect):
            enemy.health -= damage
            return True

    return False


def hit_player(rect, damage):
    global gameOver

    if gameOver:  # lazy code to prevent enemies hitting the player after game over
        return

    if rect.colliderect(player.bodyRect):
        gameOver = True
        # Death explosion "animation"
        explosions.append(Explosion(random.choice(exp), player.position))
        # Create 4 more to create a huge explosion
        explosions.append(Explosion(random.choice(
            exp), player.position + pygame.Vector2(60, 0)))
        explosions.append(Explosion(random.choice(
            exp), player.position + pygame.Vector2(-60, 0)))
        explosions.append(Explosion(random.choice(
            exp), player.position + pygame.Vector2(0, 60)))
        explosions.append(Explosion(random.choice(
            exp), player.position + pygame.Vector2(0, -60)))
        return True

    return False


def get_rotation(start, target):
    rel = pygame.math.Vector2(target.x - start.x, target.y - start.y)
    return (180 / math.pi) * -math.atan2(rel.y, rel.x) - 90


def game_bounds(rect):

    if rect.top < 0:
        rect.top = 0
    elif rect.bottom > WINDOW_SIZE[1]:
        rect.bottom = WINDOW_SIZE[1]

    if rect.left < 0:
        rect.left = 0
    elif rect.right > WINDOW_SIZE[0]:
        rect.right = WINDOW_SIZE[0]


def move_and_collide(rect, position, movement):
    grounded = False

    # Move X axis
    rect.move_ip(movement.x, 0)
    # Check collisions (X axis)
    collisions = get_collisions(rect)
    for col in collisions:
        if movement.x < 0:
            rect.left = col.right
            position.x = col.right + rect.width / 2
            movement.x = 0
        elif movement.x > 0:
            rect.right = col.left
            position.x = col.left - rect.width / 2
            movement.x = 0

    # Move Y axis
    rect.move_ip(0, movement.y)
    # Check collisions (Y axis)
    collisions = get_collisions(rect)
    for col in collisions:
        if movement.y < 0:
            rect.top = col.bottom
            position.y = col.bottom + rect.height / 2
            movement.y = 0
        elif movement.y > 0:
            grounded = True  # Grounded
            rect.bottom = col.top
            position.y = col.top - rect.height / 2
            movement.y = 0

    # Check bounds
    if rect.top < 0:
        rect.top = 0
        position.y = 0 + rect.height / 2
    elif rect.bottom > WINDOW_SIZE[1]:
        rect.bottom = WINDOW_SIZE[1]
        position.y = WINDOW_SIZE[1] - rect.height / 2

    if rect.left < 0:
        rect.left = 0
        position.x = 0 + rect.width / 2
    elif rect.right > WINDOW_SIZE[0]:
        rect.right = WINDOW_SIZE[0]
        position.x = WINDOW_SIZE[0] - rect.width / 2

    position += movement

    return grounded


def get_collisions(rect):
    collisions = []
    for collider in colliderObjects:
        if rect.colliderect(collider):
            collisions.append(collider)

    return collisions


def player_controls():
    if gameOver:
        return

    movement = pygame.math.Vector2(0, 0)

    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN:
            bullets.append(Bullet(img_bullet, player.position, pygame.math.Vector2(
                pygame.mouse.get_pos()), 15, 15, False))

    # Movement keys (Arrow keys or WASD)
    if player.fuel > 0:  # No fuel = can't move
        if pressedKeys[K_LEFT] or pressedKeys[K_a]:
            movement.x = -1
        if pressedKeys[K_RIGHT] or pressedKeys[K_d]:
            movement.x = 1
        if pressedKeys[K_UP] or pressedKeys[K_w]:
            movement.y = -1
        if pressedKeys[K_DOWN] or pressedKeys[K_s]:
            movement.y = 1

    player.move(movement)


def exit_controls():
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()


def gameOverScreen():
    # Multiply with some number to make score (aka. killcount) look less boring
    score = str(totalEnemyKills * 18)
    display.blit(gameOverFont.render("GAME OVER! Pisteet: " +
                 score, True, (255, 255, 255)), (425, 350))


# Level enemy amount + extraEnemies
levels = [
    1, 2, 4
]

levelCounter = -1
enemyHealth = 20
enemySpeed = 2
enemyBulletSpeed = 4
enemyShootRate = 3
extraEnemies = 0


def levelManager():
    if len(enemies) <= 0:  # All enemies destroyed -> next level
        global levelCounter, enemyHealth, enemySpeed, extraEnemies, enemyShootRate, enemyBulletSpeed

        if levelCounter >= len(levels) - 1:  # No more levels
            enemyHealth += 20

            if enemySpeed < 6:
                enemySpeed += 1

            if enemyBulletSpeed < 8:
                enemyBulletSpeed += 1

            if enemyShootRate > 2:
                enemyShootRate -= 1

            extraEnemies += 1
            levelCounter = -1

        levelCounter += 1  # Next level

        if extraEnemies == 1:
            img = img_enemybody2
        elif extraEnemies == 2:
            img = img_enemybody3
        elif extraEnemies >= 3:
            img = img_enemybody4
        else:
            img = img_enemybody

        for i in range(levels[levelCounter] + extraEnemies):  # Spawn enemies
            enemies.append(Enemy(img, pygame.Vector2(random.randrange(
                100, WINDOW_SIZE[0]), 0), enemyHealth, enemySpeed, enemyShootRate, enemyBulletSpeed))


events = None
pressedKeys = None
pressedMouseKeys = None

img_cannon = pygame.image.load("assets/cannon.png").convert_alpha()
img_playerbody = pygame.image.load("assets/player.png").convert_alpha()

img_enemybody = pygame.image.load("assets/enemy.png").convert_alpha()
img_enemybody2 = pygame.image.load("assets/enemy2.png").convert_alpha()
img_enemybody3 = pygame.image.load("assets/enemy3.png").convert_alpha()
img_enemybody4 = pygame.image.load("assets/enemy4.png").convert_alpha()

# Fire
img_fire1 = pygame.image.load("assets/fire1.png").convert_alpha()
img_fire2 = pygame.image.load("assets/fire2.png").convert_alpha()
fires = [img_fire1, img_fire2]

# Explosion
img_explosion1 = pygame.image.load("assets/explosion1.png").convert_alpha()
img_explosion2 = pygame.image.load("assets/explosion2.png").convert_alpha()
exp = [img_explosion1, img_explosion2]


img_surface = pygame.image.load("assets/surface.png").convert()
rect_surface = img_surface.get_rect()
rect_surface.bottom = WINDOW_SIZE[1]

img_platform = pygame.image.load("assets/platform.png").convert()
rect_platform = img_platform.get_rect()
rect_platform.bottom = 675
rect_platform.right = WINDOW_SIZE[1] - 350

rect_platform2 = img_platform.get_rect()
rect_platform2.bottom = 675
rect_platform2.right = WINDOW_SIZE[1] + 450

img_bullet = pygame.image.load("assets/bullet.png").convert_alpha()
img_enemybullet = pygame.image.load("assets/enemybullet.png").convert_alpha()
img_background = pygame.image.load("assets/bg.jpg").convert()

font = pygame.font.SysFont("Arial", 32, bold=True)
gameOverFont = pygame.font.SysFont("Arial", 64, bold=True)

# Game variables
player = Player(
    img_playerbody, pygame.Vector2(740, 775)
)
colliderObjects = [rect_surface, rect_platform, rect_platform2]
playerSpeed = 6
gravity = 4
bullets = []
enemies = []
explosions = []

# GAME LOOP
while True:
    events = pygame.event.get()
    pressedKeys = pygame.key.get_pressed()
    pressedMouseKeys = pygame.mouse.get_pressed()

    display.fill((28, 28, 28))
    display.blit(img_background, (0, 0))
    

    exit_controls()
    player_controls()

    for bullet in reversed(bullets):
        bullet.move()
        display.blit(bullet.image, bullet.rect)

    for enemy in reversed(enemies):
        enemy.move()
        display.blit(enemy.image, enemy.bodyRect)
        display.blit(enemy.cannonImage, enemy.cannonRect)

    for explosion in reversed(explosions):
        if explosion.lifeTimeCounter > 45:
            explosions.remove(explosion)
            continue

        display.blit(random.choice(exp), explosion.rect)
        explosion.lifeTimeCounter += 1

    if not gameOver:
        levelManager()

        display.blit(img_playerbody, player.bodyRect)
        display.blit(player.cannonImage, player.cannonRect)
        f = round(player.fuel / 100, 2)
        display.blit(font.render(str(int(player.fuel)), True, Color(255, 0, 0).lerp(
            Color(0, 255, 0), f)), player.position + pygame.Vector2(54, -16))

    if gameOver:
        gameOverScreen()

    display.blit(img_surface, rect_surface)
    display.blit(img_platform, rect_platform)
    display.blit(img_platform, rect_platform2)

    display.blit(font.render(
        "WASD to move, MOUSE to aim and shoot ", True, (255, 255, 255)), (10, 10))

    pygame.time.Clock().tick(60)  # Limit FPS to 60
    pygame.display.flip()

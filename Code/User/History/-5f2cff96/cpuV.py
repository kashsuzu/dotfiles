import pygame
from pygame import Rect

GRAVITY = 1500
JUMP_SPEED = -600
MOVE_SPEED = 220
WIDTH, HEIGHT = 40, 40

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()

        self.stay = pygame.transform.scale(pygame.image.load('assets/pig_stay.png').convert_alpha(), (WIDTH, HEIGHT))

        self.run_left = [
            pygame.transform.scale(pygame.image.load('assets/pig_left_1.png').convert_alpha(), (WIDTH, HEIGHT)),
            pygame.transform.scale(pygame.image.load('assets/pig_left_2.png').convert_alpha(), (WIDTH, HEIGHT))
        ]

        self.run_right = [
            pygame.transform.scale(pygame.image.load('assets/pig_right_1.png').convert_alpha(), (WIDTH, HEIGHT)),
            pygame.transform.scale(pygame.image.load('assets/pig_right_2.png').convert_alpha(), (WIDTH, HEIGHT))
        ]

        self.jump_left = pygame.transform.scale(pygame.image.load('assets/pig_jump_left.png').convert_alpha(), (WIDTH, HEIGHT))
        self.jump_right = pygame.transform.scale(pygame.image.load('assets/pig_jump_right.png').convert_alpha(), (WIDTH, HEIGHT))

        self.image = self.stay
        self.rect = Rect(x, y, WIDTH, HEIGHT)

        self.vx = 0
        self.vy = 0
        self.on_ground = False

        self.anim_timer = 0
        self.anim_frame = 0
        self.facing_right = True

    def collide(self, dx, dy, platforms):
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if dx > 0:
                    self.rect.right = p.rect.left
                    self.vx = 0
                if dx < 0:
                    self.rect.left = p.rect.right
                    self.vx = 0
                if dy > 0:
                    self.rect.bottom = p.rect.top
                    self.vy = 0
                    self.on_ground = True
                if dy < 0:
                    self.rect.top = p.rect.bottom
                    self.vy = 0

def update(self, left, right, up, platforms, dt):
    target = 0
    if left:
        target = -1
    if right:
        target = 1

    self.vx = target * MOVE_SPEED

    if target < 0:
        self.facing_right = False
    if target > 0:
        self.facing_right = True

    if up and self.on_ground:
        self.vy = JUMP_SPEED
        self.on_ground = False

    self.vy += GRAVITY * dt

    dy = self.vy * dt
    self.rect.y += dy
    self.collide(0, dy, platforms)

    dx = self.vx * dt
    self.rect.x += dx
    self.collide(dx, 0, platforms)

    if not self.on_ground:
        self.image = self.jump_right if self.facing_right else self.jump_left
    elif target == 0:
        self.image = self.stay
    else:
        self.anim_timer += dt
        if self.anim_timer > 0.12:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 2
        self.image = self.run_right[self.anim_frame] if self.facing_right else self.run_left[self.anim_frame]

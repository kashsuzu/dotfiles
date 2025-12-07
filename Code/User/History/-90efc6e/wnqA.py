import pygame
from player import Player
from blocks import Platform
from camera import Camera

pygame.init()
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Super Pig')
CLOCK = pygame.time.Clock()
FPS = 60
PLATFORM_W = 32
PLATFORM_H = 32

LEVELS = [
    [
        '                                ',
        '                                ',
        '                                ',
        '      ---       ----            ',
        '                                ',
        '               ---              ',
        '   ----                       --',
        '                                ',
        '        -------     -----       ',
        '------------------------------  ',
    ],
    [
        '                                ',
        '                                ',
        '     ---       ---              ',
        '                                ',
        '                                ',
        '   ------            ---        ',
        '                                ',
        '          ------                ',
        '    ---              -------    ',
        '------------------------------  ',
    ],
    [
        '                                ',
        '       ----                     ',
        '                                ',
        '   ---        ---        ---    ',
        '                                ',
        '                                ',
        '      ----        -------       ',
        '                                ',
        '   -------       ----           ',
        '------------------------------  ',
    ]
]


LEVEL_INDEX = 0

def build_level(level_map, group, platforms):
    for y, row in enumerate(level_map):
        for x, ch in enumerate(row):
            if ch == '-':
                px = x * PLATFORM_W
                py = y * PLATFORM_H
                p = Platform(px, py, PLATFORM_W, PLATFORM_H)
                group.add(p)
                platforms.append(p)

def main():
    global LEVEL_INDEX
    running = True
    entities = pygame.sprite.Group()
    platforms = []
    player = Player(50, 50)
    entities.add(player)
    build_level(LEVELS[LEVEL_INDEX], entities, platforms)
    camera = Camera(WIDTH, HEIGHT)

    while running:
        dt = CLOCK.tick(FPS) / 1000
        up = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key in (pygame.K_UP, pygame.K_SPACE):
                    up = True
                if event.key == pygame.K_n:
                    for s in list(entities):
                        if isinstance(s, Platform):
                            entities.remove(s)
                    platforms.clear()
                    LEVEL_INDEX = (LEVEL_INDEX + 1) % len(LEVELS)
                    build_level(LEVELS[LEVEL_INDEX], entities, platforms)

        keys = pygame.key.get_pressed()
        left = keys[pygame.K_LEFT]
        right = keys[pygame.K_RIGHT]

        player.update(left, right, up, platforms, dt)
        camera.update(player)

        SCREEN.fill((135, 206, 235))
        for e in entities:
            SCREEN.blit(e.image, camera.apply(e))
        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    main()

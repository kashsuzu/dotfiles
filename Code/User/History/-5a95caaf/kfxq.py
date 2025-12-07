import random
import sys

import pygame

pygame.init()

CELL = 20
W, H = 640, 480
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()
font_big = pygame.font.Font(None, 60)
font_small = pygame.font.Font(None, 34)


def rand_cell():
    return (
        random.randrange(0, W // CELL) * CELL,
        random.randrange(0, H // CELL) * CELL,
    )


def draw_gradient():
    for i in range(H):
        c = 35 + int(40 * (i / H))
        pygame.draw.line(screen, (c, c, c + 20), (0, i), (W, i))


snake = [(W // 2, H // 2), (W // 2 - CELL, H // 2), (W // 2 - 2 * CELL, H // 2)]

dirx, diry = 1, 0
food = rand_cell()
score = 0
record = 0
running = True
game_over = False


def draw_text(text, x, y):
    shadow = font_small.render(text, True, (0, 0, 0))
    screen.blit(shadow, (x + 2, y + 2))
    surf = font_small.render(text, True, (255, 255, 255))
    screen.blit(surf, (x, y))


def reset():
    global snake, dirx, diry, food, score, game_over
    snake = [(W // 2, H // 2), (W // 2 - CELL, H // 2), (W // 2 - 2 * CELL, H // 2)]
    dirx, diry = 1, 0
    food = rand_cell()
    score = 0
    game_over = False


while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        if e.type == pygame.KEYDOWN and not game_over:
            if e.key == pygame.K_UP and diry == 0:
                dirx, diry = 0, -1
            elif e.key == pygame.K_DOWN and diry == 0:
                dirx, diry = 0, 1
            elif e.key == pygame.K_LEFT and dirx == 0:
                dirx, diry = -1, 0
            elif e.key == pygame.K_RIGHT and dirx == 0:
                dirx, diry = 1, 0

        if e.type == pygame.KEYDOWN and game_over:
            if e.key == pygame.K_RETURN:
                reset()
            elif e.key == pygame.K_ESCAPE:
                running = False

    if not game_over:
        head = (snake[0][0] + dirx * CELL, snake[0][1] + diry * CELL)

        if head[0] < 0 or head[0] >= W or head[1] < 0 or head[1] >= H or head in snake:
            game_over = True
            record = max(record, score)
        else:
            snake.insert(0, head)
            if head == food:
                score += 1
                while True:
                    food = rand_cell()
                    if food not in snake:
                        break
            else:
                snake.pop()

    draw_gradient()

    # ---- Draw snake ----
    for s in snake:
        pygame.draw.rect(
            screen,
            (0, 200, 0),
            (s[0] + 2, s[1] + 2, CELL - 4, CELL - 4),
            border_radius=6,
        )

    # ---- Food glow ----
    glow = pygame.Rect(food[0] - 4, food[1] - 4, CELL + 8, CELL + 8)
    pygame.draw.ellipse(screen, (255, 80, 80), glow)

    # ---- Food ----
    pygame.draw.rect(screen, (255, 40, 40), (*food, CELL, CELL), border_radius=4)

    draw_text(f"Score: {score}", 10, 10)
    draw_text(f"Record: {record}", 10, 40)

    if game_over:
        t = font_big.render("GAME OVER", True, (255, 255, 255))
        screen.blit(t, ((W - t.get_width()) // 2, 150))

        t2 = font_small.render("Enter - Restart   Esc - Quit", True, (255, 255, 255))
        screen.blit(t2, ((W - t2.get_width()) // 2, 230))

    pygame.display.flip()
    clock.tick(10)

pygame.quit()
sys.exit()

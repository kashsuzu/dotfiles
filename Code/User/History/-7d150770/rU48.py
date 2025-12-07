import random
import sys

import pygame

pygame.init()

WIDTH, HEIGHT = 640, 480
GRID = 20

window = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font_big = pygame.font.Font(None, 60)
font_small = pygame.font.Font(None, 34)


def random_cell():
    return (
        random.randrange(0, WIDTH // GRID) * GRID,
        random.randrange(0, HEIGHT // GRID) * GRID,
    )


snake = [(300, 240), (280, 240), (260, 240)]
dx, dy = GRID, 0
food = random_cell()

score = 0
record = 0
alive = True
running = True


def draw_gradient():
    for i in range(HEIGHT):
        c = 40 + int(40 * (i / HEIGHT))
        pygame.draw.line(window, (c, c, c + 20), (0, i), (WIDTH, i))


def reset():
    global snake, dx, dy, food, score, alive
    snake = [(300, 240), (280, 240), (260, 240)]
    dx, dy = GRID, 0
    food = random_cell()
    score = 0
    alive = True


while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        if e.type == pygame.KEYDOWN:
            if alive:
                if e.key == pygame.K_UP and dy == 0:
                    dx, dy = 0, -GRID
                elif e.key == pygame.K_DOWN and dy == 0:
                    dx, dy = 0, GRID
                elif e.key == pygame.K_LEFT and dx == 0:
                    dx, dy = -GRID, 0
                elif e.key == pygame.K_RIGHT and dx == 0:
                    dx, dy = GRID, 0
            else:
                if e.key == pygame.K_RETURN:
                    reset()
                elif e.key == pygame.K_ESCAPE:
                    running = False

    if alive:
        head_x, head_y = snake[0]
        new_head = (head_x + dx, head_y + dy)

        if (
            new_head[0] < 0
            or new_head[0] >= WIDTH
            or new_head[1] < 0
            or new_head[1] >= HEIGHT
            or new_head in snake
        ):
            alive = False
            record = max(record, score)
        else:
            snake.insert(0, new_head)
            if new_head == food:
                score += 1
                while True:
                    food = random_cell()
                    if food not in snake:
                        break
            else:
                snake.pop()

    # === DRAW ===
    draw_gradient()

    # Snake
    for x, y in snake:
        pygame.draw.rect(
            window, (0, 180, 0), (x + 2, y + 2, GRID - 4, GRID - 4), border_radius=6
        )

    # Food glow
    glow_rect = pygame.Rect(food[0] - 4, food[1] - 4, GRID + 8, GRID + 8)
    pygame.draw.ellipse(window, (255, 80, 80, 20), glow_rect)

    # Food
    pygame.draw.rect(window, (255, 40, 40), (*food, GRID, GRID), border_radius=4)

    # Score + Record with shadow
    def draw_text(text, x, y):
        shadow = font_small.render(text, True, (0, 0, 0))
        window.blit(shadow, (x + 2, y + 2))
        surf = font_small.render(text, True, (255, 255, 255))
        window.blit(surf, (x, y))

    draw_text(f"Score: {score}", 10, 10)
    draw_text(f"Record: {record}", 10, 40)

    if not alive:
        txt = font_big.render("GAME OVER", True, (255, 255, 255))
        window.blit(txt, ((WIDTH - txt.get_width()) // 2, 140))

        tip = font_small.render("Enter - Restart   Esc - Quit", True, (255, 255, 255))
        window.blit(tip, ((WIDTH - tip.get_width()) // 2, 220))

    pygame.display.update()
    clock.tick(10)

pygame.quit()
sys.exit()

import random
import sys

import pygame

pygame.init()

WIDTH, HEIGHT = 640, 480
GRID = 20

window = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 34)


def random_position():
    cols = WIDTH // GRID
    rows = HEIGHT // GRID
    return random.randint(0, cols - 1) * GRID, random.randint(0, rows - 1) * GRID


snake_body = [(300, 240), (280, 240), (260, 240)]

move_x, move_y = GRID, 0
food_pos = random_position()
points = 0
alive = True
running = True


def reset_game():
    global snake_body, move_x, move_y, food_pos, points, alive
    snake_body = [(300, 240), (280, 240), (260, 240)]
    move_x, move_y = GRID, 0
    food_pos = random_position()
    points = 0
    alive = True


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if alive:
                if event.key == pygame.K_UP and move_y == 0:
                    move_x, move_y = 0, -GRID
                elif event.key == pygame.K_DOWN and move_y == 0:
                    move_x, move_y = 0, GRID
                elif event.key == pygame.K_LEFT and move_x == 0:
                    move_x, move_y = -GRID, 0
                elif event.key == pygame.K_RIGHT and move_x == 0:
                    move_x, move_y = GRID, 0
            else:
                if event.key == pygame.K_RETURN:
                    reset_game()
                elif event.key == pygame.K_ESCAPE:
                    running = False

    if alive:
        head_x, head_y = snake_body[0]
        new_head = (head_x + move_x, head_y + move_y)

        if (
            new_head[0] < 0
            or new_head[0] >= WIDTH
            or new_head[1] < 0
            or new_head[1] >= HEIGHT
            or new_head in snake_body
        ):
            alive = False
        else:
            snake_body.insert(0, new_head)
            if new_head == food_pos:
                points += 1
                while True:
                    food_pos = random_position()
                    if food_pos not in snake_body:
                        break
            else:
                snake_body.pop()

    window.fill((0, 0, 0))

    for px, py in snake_body:
        pygame.draw.rect(window, (0, 200, 0), (px, py, GRID, GRID))

    pygame.draw.rect(window, (200, 30, 30), (*food_pos, GRID, GRID))

    score_surf = font.render(f"Score: {points}", True, (255, 255, 255))
    window.blit(score_surf, (10, 10))

    if not alive:
        msg = font.render(
            "Game Over: Enter - restart, Esc - quit", True, (255, 255, 255)
        )
        window.blit(
            msg, ((WIDTH - msg.get_width()) // 2, (HEIGHT - msg.get_height()) // 2)
        )

    pygame.display.update()
    clock.tick(10)

pygame.quit()
sys.exit()

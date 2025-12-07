import random
import sys

import pygame

pygame.init()

CELL_SIZE = 20
WINDOW_WIDTH, WINDOW_HEIGHT = 640, 480

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)


def get_random_cell():
    return (
        random.randrange(0, WINDOW_WIDTH // CELL_SIZE) * CELL_SIZE,
        random.randrange(0, WINDOW_HEIGHT // CELL_SIZE) * CELL_SIZE,
    )


snake = [
    (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2),
    (WINDOW_WIDTH // 2 - CELL_SIZE, WINDOW_HEIGHT // 2),
    (WINDOW_WIDTH // 2 - 2 * CELL_SIZE, WINDOW_HEIGHT // 2),
]

direction_x, direction_y = 1, 0
food = get_random_cell()
score = 0
running = True
game_over = False


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN and not game_over:
            if event.key == pygame.K_UP and direction_y == 0:
                direction_x, direction_y = 0, -1
            elif event.key == pygame.K_DOWN and direction_y == 0:
                direction_x, direction_y = 0, 1
            elif event.key == pygame.K_LEFT and direction_x == 0:
                direction_x, direction_y = -1, 0
            elif event.key == pygame.K_RIGHT and direction_x == 0:
                direction_x, direction_y = 1, 0

        if event.type == pygame.KEYDOWN and game_over:
            if event.key == pygame.K_RETURN:
                snake = [
                    (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2),
                    (WINDOW_WIDTH // 2 - CELL_SIZE, WINDOW_HEIGHT // 2),
                    (WINDOW_WIDTH // 2 - 2 * CELL_SIZE, WINDOW_HEIGHT // 2),
                ]
                direction_x, direction_y = 1, 0
                food = get_random_cell()
                score = 0
                game_over = False
            elif event.key == pygame.K_ESCAPE:
                running = False

    if not game_over:
        head_x = snake[0][0] + direction_x * CELL_SIZE
        head_y = snake[0][1] + direction_y * CELL_SIZE
        new_head = (head_x, head_y)

        if (
            head_x < 0
            or head_x >= WINDOW_WIDTH
            or head_y < 0
            or head_y >= WINDOW_HEIGHT
            or new_head in snake
        ):
            game_over = True
        else:
            snake.insert(0, new_head)

            if new_head == food:
                score += 1
                while True:
                    food = get_random_cell()
                    if food not in snake:
                        break
            else:
                snake.pop()

    screen.fill((0, 0, 0))

    for cell in snake:
        pygame.draw.rect(screen, (0, 255, 0), (*cell, CELL_SIZE, CELL_SIZE))

    pygame.draw.rect(screen, (255, 0, 0), (*food, CELL_SIZE, CELL_SIZE))

    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))

    if game_over:
        game_over_text = font.render(
            "Game Over - Enter to restart or Esc to quit", True, (255, 255, 255)
        )
        screen.blit(
            game_over_text,
            (
                (WINDOW_WIDTH - game_over_text.get_width()) // 2,
                (WINDOW_HEIGHT - game_over_text.get_height()) // 2,
            ),
        )

    pygame.display.flip()
    clock.tick(10)

pygame.quit()
sys.exit()

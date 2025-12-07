import pygame

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((120, 72, 0))
        pygame.draw.rect(self.image, (160, 110, 30), (2, 2, w - 4, h - 4))
        self.rect = self.image.get_rect(topleft=(x, y))

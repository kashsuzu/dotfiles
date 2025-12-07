import pygame

class Camera:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.camera_rect = pygame.Rect(0, 0, screen_w, screen_h)

    def apply(self, entity):
        return entity.rect.move(-self.camera_rect.x, -self.camera_rect.y)

    def update(self, target):
        self.camera_rect.x = target.rect.centerx - self.screen_w // 2
        self.camera_rect.y = target.rect.centery - self.screen_h // 2

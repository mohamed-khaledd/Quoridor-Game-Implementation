import pygame
from config import Theme

class Button:
    def __init__(self, text, x, y, w, h, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.hovered = False

    def draw(self, screen, font):
        color = Theme.BUTTON_HOVER if self.hovered else Theme.BUTTON_BG
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        
        txt_surf = font.render(self.text, True, Theme.BUTTON_TEXT)
        screen.blit(txt_surf, (self.rect.centerx - txt_surf.get_width()//2, self.rect.centery - txt_surf.get_height()//2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered and event.button == 1:
                self.callback()
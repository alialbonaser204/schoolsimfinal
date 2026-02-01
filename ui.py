import pygame
import textwrap
from simpy_fsm import SimpyFSM


class Legend(pygame.rect.Rect):
    def __init__(self, left, top, width, height, paused, sim_speed, sim_time):
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.paused = paused
        self.speed = sim_speed
        self.sim_time = sim_time

    def __str__(self):
        return f"Pause: SPACE ({self.paused})\n" \
               f"Faster: W\n" \
               f"Slower: S\n" \
               f"Reset: R\n" \
               f"Reset to 0: T\n" \
               f"Sim Speed: {self.speed}\n" \
               f"Sim Time: {self.sim_time:.1f}\n"


class UI(pygame.rect.Rect):
    def __init__(self, screen, font_filename, font_size, left, top, width, height, legend):
        self.screen = screen
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.font = pygame.font.Font(font_filename, font_size)
        self.object = "Click any student for more info."
        self.legend = legend

    def draw(self):
        # Achtergrond van UI
        pygame.draw.rect(self.screen, (200, 200, 200), (self.left, self.top, self.width, self.height))
        pygame.draw.rect(self.screen, (0, 0, 0), (self.left, self.top, self.width, self.height), 2)

        # Tekst van object tonen met wrapping
        lines = textwrap.wrap(str(self.object), width=40)
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, (0, 0, 0))
            self.screen.blit(text_surface, (self.left + 5, self.top + 5 + i * 20))

        # Legend tekst
        legend_lines = str(self.legend).splitlines()
        for i, line in enumerate(legend_lines):
            text_surface = self.font.render(line, True, (0, 0, 0))
            self.screen.blit(text_surface, (self.legend.left + 5, self.legend.top + i * 20))

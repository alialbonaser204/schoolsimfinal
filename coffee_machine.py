# coffee_machine.py
from pathlib import Path
from typing import Tuple
import simpy
import pygame
import util
from util import is_break_time
class CoffeeMachine:
    def __init__(self, env: simpy.Environment, screen: pygame.Surface, image: Path,
                 image_size: Tuple[int, int], position: Tuple[int, int], capacity=1):
        self.env = env
        self.screen = screen
        self.img = pygame.image.load(image)
        self.img = pygame.transform.scale(self.img, image_size)
        self.image_size = image_size
        self.position = position

        self.signal = util.QueueSignal()
        self.resource = simpy.Resource(env, capacity=capacity)

        # Idle tracking
        self.last_used = env.now
        self.total_idle_time = 0



    def update_idle_time(self, now):
        idle_duration = now - self.last_used

        if idle_duration > 0:
            # Loop over elk tijdstip tussen de laatste activiteit en nu
            for t in range(int(self.last_used), int(now)):
                if is_break_time(t):
                    self.total_idle_time += 1  # telt alleen seconden in pauze
        self.last_used = now

    def get_total_idle_time(self):
        return self.total_idle_time

    def place_student(self, student) -> Tuple[int, int]:
        queue_length = len(self.resource.queue) + len(self.resource.users)
        print(f"{student.name} staat {queue_length+1}e in de rij")
        return (self.position[0],
                self.position[1] + self.image_size[1] + queue_length * student.image_size[1])

    def draw(self):
        self.screen.blit(self.img, self.position)

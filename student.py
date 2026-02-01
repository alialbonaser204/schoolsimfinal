import random
import uuid
import pygame
import simpy
from pathlib import Path
import numpy as np
from spritesheet import Spritesheet
from simpy_fsm import SimpyFSM
from state import State


class Student:
    def __init__(self, name: str, env: simpy.Environment, screen: pygame.Surface,
                 image: Path, image_size: (int, int), image_grid_size: (int, int), **knowledge_base):
        self.name = name
        self.uid = uuid.uuid4()
        self.selected = False

        self.total_wait_time = 0
        self.coffee_attempts = 0
        self.missed_coffee = False
        self.did_not_get_coffee = False  # Nieuw

        self.env = env
        self.screen = screen
        self.image_size = image_size
        self.position = (0, 0)
        self.rect = pygame.Rect(0, 0, image_size[0], image_size[1])



        if self.screen is not None:
            self.spritesheet = Spritesheet(image)
            self.sprites = self.spritesheet.load_grid((0, 0, image_grid_size[0], image_grid_size[1]), 3, 4, -1)
            self.sprites = [pygame.transform.scale(s, image_size) for s in self.sprites]
        else:
            self.sprites = []

        # Kennisbasis
        self.kb = {}
        for k, v in knowledge_base.items():
            self.kb[k] = v

        self.general_thirstiness = np.random.poisson(lam=2, size=1)

        self.drink = ""
        self.text = ".."
        self.table_number = -1

    def start_state(self, initial_state: State):
        self.fsm = SimpyFSM(initial_state, self.env)

    def draw(self, delta_time):
        if self.selected:
            pygame.draw.circle(self.screen, pygame.Color(255, 128, 0, 255), self.rect.center, self.rect.width // 2)
        if self.sprites:
            sprite = self.sprites[self.fsm.state.sprite_index(delta_time)]
            self.screen.blit(sprite, self.position)

    def _get_shortest_queue(self, coffee_machines):
        return sorted(coffee_machines, key=lambda m: len(m.resource.queue) + len(m.resource.users))[0]

    def enter_coffee_machine_queue(self):
        QUEUE_LIMIT = 5
        machine = self._get_shortest_queue(self.kb['coffee_machines'])


        current_queue_length = len(machine.resource.queue) + len(machine.resource.users)
        if current_queue_length >= QUEUE_LIMIT:
            self.text = "Te druk, geen koffie!"
            self.missed_coffee = True
            return None  # Student gaat niet in de rij

        self.change_position(machine.place_student(self))
        machine.signal.connect(self)
        return machine

    def leave_coffee_machine_queue(self, machine):
        machine.signal.disconnect(self)
        machine.signal.emit()

    def change_position(self, pos):
        self.position = pos
        self.rect.topleft = pos

    def select(self):
        print(f"Select {self.name}")
        self.selected = True

    def deselect(self):
        print(f"Deselect {self.name}")
        self.selected = False

    def move_up(self):
        new_pos = (self.position[0], self.position[1] - self.image_size[1])
        self.change_position(new_pos)


    def __str__(self):
        return f"Student {self.name}: State={self.fsm.state}, Text={self.text}"

# simulation.py
import random
import sys

import numpy as np
import pygame
import simpy
import time
from pathlib import Path
from box import Box

from classroom import Classroom
from coffee_corner import CoffeeCorner
from coffee_machine import CoffeeMachine
from hallway import Hallway
from name_generator import NameGenerator
from hallway_state import HallwayState
from student import Student
from ui import UI, Legend

class Simulation:
    def __init__(self, conf: Box, headless=False):
        self.headless = headless
        self.conf = conf

        self.screen = None
        self.background = None
        self.env = None
        self.paused = None
        self.fps = None
        self.max_end_time = None
        self.last_frame_time = None
        self.simulation_time = None
        self.simulation_speed = None

        # Statistieken
        self.coffee_wait_times = []
        self.students_no_coffee = 0

        # Componenten
        self.legend = None
        self.ui = None
        self.coffee_corner = None
        self.coffee_machines = None
        self.classroom = None
        self.hallway = None
        self.students = None

        self.reset(conf)

    def reset(self, conf: Box):

        if hasattr(conf, "seed"):
            random.seed(conf.seed)
            np.random.seed(conf.seed)

        if not self.headless:
            self.screen, self.background = self.setup_pygame(conf)
        else:
            self.screen, self.background = None, None

        self.env = simpy.Environment()
        self.paused = True
        self.simulation_speed = 10
        self.fps = 20
        self.max_end_time = 5000000
        self.last_frame_time = time.time()
        self.simulation_time = 0

        if not self.headless:
            self.legend = Legend(conf.ui.legend.left, conf.ui.legend.top, conf.ui.legend.width,
                                 conf.ui.legend.height, self.paused, self.simulation_speed, self.simulation_time)
            self.ui = UI(self.screen, conf.ui.font_filename, conf.ui.font_size, conf.ui.position[0],
                         conf.ui.position[1], conf.ui.width, conf.ui.height, self.legend)

        # Initialiseer de koffiecornert en koffieautomaten
        self.coffee_corner = CoffeeCorner(self.env, self.screen,
                                          conf.coffee_corner.position[0], conf.coffee_corner.position[1],
                                          conf.coffee_corner.width, conf.coffee_corner.height)
        self.coffee_machines = []
        for i in range(conf.coffee_machine.amount):
            machine = CoffeeMachine(
                self.env,
                self.screen,
                Path(conf.coffee_machine.image),
                image_size=(conf.coffee_machine.width, conf.coffee_machine.height),
                position=(conf.coffee_machine.position[i][0], conf.coffee_machine.position[i][1]),
                capacity=conf.coffee_machine.capacity if hasattr(conf.coffee_machine, "capacity") else 1
            )
            self.coffee_machines.append(machine)

        # Initialiseer het klaslokaal en de gang
        self.classroom = Classroom(self.env, self.screen, conf.classroom.position[0],
                                   conf.classroom.position[1], conf.classroom.width, conf.classroom.height,
                                   conf.classroom.seat_size, conf.classroom.seat_image,
                                   conf.classroom.student_table_offset, capacity=conf.classroom.seats)
        self.hallway = Hallway(self.env, self.screen, conf.hallway.position[0],
                               conf.hallway.position[1], conf.hallway.width, conf.hallway.height,
                               conf.hallway.spot_size, conf.hallway.rows)

        # Reset statistieken
        self.coffee_wait_times = []
        self.students_no_coffee = 0

        # Initialiseer de studenten
        NUM_STUDENTS = conf.student.amount if hasattr(conf.student, 'amount') else 3
        self.students = []
        image_size = conf.student.size
        image_grid_size = conf.student.grid_size
        student_names = NameGenerator().randomNames(NUM_STUDENTS)
        student_names = [chr(i) for i in range(65, 65 + NUM_STUDENTS)]

        num_coffee_lovers = int(NUM_STUDENTS * 0.7)

        coffee_lovers_indices = set(random.sample(range(NUM_STUDENTS), num_coffee_lovers))
        self.coffee_lovers_indices = coffee_lovers_indices

        for i in range(NUM_STUDENTS):
            image_path = random.choice(list(Path(conf.student.images_path).glob("*.png")))
            student = Student(student_names[i], self.env, self.screen, Path(image_path),
                              image_size, image_grid_size,
                              coffee_machines=self.coffee_machines,
                              classroom=self.classroom,
                              hallway=self.hallway,
                              simulation=self)

            student.wants_coffee = i in coffee_lovers_indices
            self.students.append(student)
            student.start_state(HallwayState(self.env, student))

    def run_for(self, delta_time):
        if self.paused and not self.headless:
            return
        self.simulation_time += delta_time
        if not self.headless:
            self.ui.legend.sim_time = self.simulation_time
            self.ui.draw()
        while self.env.peek() < self.simulation_time:
            self.env.step()

    def draw(self, delta_time):
        if self.headless:
            return
        self.screen.blit(self.background, (0, 0))
        self.coffee_corner.draw()
        self.classroom.draw()
        self.hallway.draw()
        self.ui.draw()
        for student in self.students:
            student.draw(delta_time)
        pygame.display.update()

    def handle_pygame_events(self):
        if self.headless:
            return
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # Verwerking van muisklikken en toetsen
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.realtime_start = time.time() - self.simulation_time
                    self.paused = not self.paused
                    self.ui.legend.paused = self.paused
                elif event.key == pygame.K_w:
                    self.simulation_speed += 1
                    self.realtime_start = time.time() - self.simulation_time
                elif event.key == pygame.K_s:
                    self.simulation_speed = max(self.simulation_speed - 1, 0.1)
                    self.realtime_start = time.time() - self.simulation_time
                elif event.key == pygame.K_r:
                    self.reset(self.conf)
                elif event.key == pygame.K_t:
                    self.simulation_speed = 1
        self.simulation_speed = round(self.simulation_speed, 2)
        self.ui.legend.speed = self.simulation_speed

    def collect_results(self, sim_id):
        wait_times = [s.total_wait_time for s in self.students if s.coffee_attempts > 0]
        avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
        missed_coffee = sum(1 for s in self.students if s.missed_coffee)
        no_attempts = sum(1 for s in self.students if s.coffee_attempts == 0)
        total_attempts = sum(s.coffee_attempts for s in self.students)

        idle_times = [cm.get_total_idle_time() for cm in self.coffee_machines]
        avg_idle_time = sum(idle_times) / len(idle_times) if self.coffee_machines else 0

        return {
            "sim_id": sim_id,
            "students": len(self.students),
            "coffee_machines": len(self.coffee_machines),
            "avg_wait_time": avg_wait_time,
            "missed_coffee": missed_coffee,
            "no_attempts": no_attempts,
            "total_attempts": total_attempts,
            "avg_idle_time": avg_idle_time
        }


    @staticmethod
    def setup_pygame(conf: Box):
        pygame.init()
        pygame_screen = pygame.display.set_mode((conf.screen.width, conf.screen.height))
        pygame.display.set_caption("School Sim")
        background = pygame.image.load(Path(conf.background)).convert()
        pygame_screen.blit(background, (0, 0))
        pygame.font.init()
        return pygame_screen, background

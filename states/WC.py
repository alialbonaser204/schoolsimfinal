import random

import numpy as np
import simpy

from state import State
from student import Student

"""
"""
class WC(State):
    def __init__(self, env: simpy.Environment, student: Student = None):
        super().__init__()
        self.env = env
        self.student = student
        self.sprite = 10
        self.animation_speed = max(random.normalvariate(1, 0.25), 0.5)


    def enter(self):
        pass


    def leave(self):
        pass
    def step(self):
        pass

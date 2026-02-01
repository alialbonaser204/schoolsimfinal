# states/hallway_state.py
import random
import simpy
from state import State

class HallwayState(State):
    def __init__(self, env: simpy.Environment, student):
        super().__init__()
        self.env = env
        self.student = student
        self.animation_speed = max(random.normalvariate(2, 0.5), 1)

    def enter(self):
        self.hallway = self.student.kb["hallway"]
        self.hallway_spot, pos = self.hallway.place_student()
        self.student.change_position(pos)

    def step(self):
        yield self.env.timeout(random.randint(0, 2))
        self.hallway.remove_student(self.hallway_spot)
        self.hallway_spot = -1

        from coffee_state import CoffeeState
        from classroom_state import ClassroomState

        sim = self.student.kb.get("simulation")


        if self.student.wants_coffee:
            delay = random.randint(0, 4)
            yield self.env.timeout(delay)

        if hasattr(self.student.fsm, "previous_state") and \
                self.student.fsm.previous_state.__class__.__name__ == "CoffeeState":
            self.switch_state(ClassroomState(self.env, self.student))
        elif self.student.wants_coffee:
            self.switch_state(CoffeeState(self.env, self.student))
        else:
            self.switch_state(ClassroomState(self.env, self.student))

    def leave(self):
        pass

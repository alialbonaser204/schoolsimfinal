import random
import simpy

from state import State
from student import Student
from util import print_stats,is_break_time

class ClassroomState(State):
    def __init__(self, env: simpy.Environment, student: Student = None):
        super().__init__()
        self.env = env
        self.student = student
        self.sprite = 10
        self.animation_speed = max(random.normalvariate(0.5, 0.05), 0.25)



    def enter(self):
        pass

    def leave(self):
        pass



    def step(self):
        _classroom = self.student.kb['classroom']
        print_stats(_classroom.resource)

        current_time = self.env.now

        if is_break_time(current_time):
            self.student.text = "Pauze. Even ontspannen met klasgenoten."
            yield self.env.timeout(15)
        else:
            if _classroom.resource.count >= _classroom.resource.capacity:
                self.student.text = "Klaslokaal zit vol. Even wachten buiten."
                yield self.env.timeout(5)
            else:
                with _classroom.resource.request() as req:
                    self.student.text = "Wachten om naar binnen te mogen."
                    yield req
                    self.table_number, position = _classroom.place_student()
                    self.student.change_position(position)
                    self.student.text = "In de les. Leren over Discrete Event Systems!"
                    yield self.env.timeout(30)  # Simuleer wat lestijd
                _classroom.open_spot(self.table_number)

        # Naar volgende state
        from hallway_state import HallwayState
        self.student.text = "Onderweg naar de koffieruimte via de gang."
        new_state = HallwayState(self.env, self.student)
        new_state.sprite = 7
        self.switch_state(new_state)



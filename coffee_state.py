import random
import numpy as np
import simpy
from state import State
from util import is_break_time,get_current_break_window

class CoffeeState(State):
    def __init__(self, env: simpy.Environment, student):
        super().__init__()
        self.env = env
        self.student = student
        self.sprite = 10
        self.animation_speed = max(random.normalvariate(1, 0.25), 0.5)
        self.drink_choice = (["coffee", "tea"], 1, [0.8, 0.2])

    def enter(self):
        pass

    def leave(self):
        sim = self.student.kb.get("simulation")
        if sim and self.student.coffee_attempts > 0:
            sim.coffee_wait_times.append(self.student.total_wait_time)

    def step(self):
        if not is_break_time(self.env.now):
            self.student.text = "Het is geen pauze, dus geen koffie."
            self.move_to_next_state()
            return

        current_break = get_current_break_window(self.env.now)
        if current_break is None:
            self.student.text = "Geen actieve pauze meer."
            self.move_to_next_state()
            return

        _, break_end = current_break
        remaining_break = max(break_end - self.env.now, 0)

        nr_of_drinks = np.random.poisson(self.student.general_thirstiness, size=1)[0]
        coffee_machine = self.student.enter_coffee_machine_queue()


        if coffee_machine is None:
            self.move_to_next_state()
            return

        arrival_time = self.env.now

        with coffee_machine.resource.request() as req:
            reneging_timer = self.env.timeout(remaining_break)
            result = yield self.env.any_of({req: "granted", reneging_timer: "timeout"})

            if reneging_timer in result:
                self.student.text = "Te lang gewacht, geen koffie."
                self.student.missed_coffee = True
                self.student.leave_coffee_machine_queue(coffee_machine)
                self.move_to_next_state()
                return

            # Toegang gekregen
            coffee_machine.update_idle_time(self.env.now)
            wait_duration = self.env.now - arrival_time

            if not is_break_time(self.env.now):  # Hercheck!
                self.student.text = "Les is begonnen, geen koffie."
                self.student.missed_coffee = True
                self.student.leave_coffee_machine_queue(coffee_machine)
                self.move_to_next_state()
                return

            self.student.total_wait_time += wait_duration
            self.student.coffee_attempts += 1
            print(f"{self.student.name}'s beurt bij de koffiemachine!")

            self.student.text = "Koffie kiezen..."
            yield self.env.timeout(2)
            self.drink = np.random.choice(*self.drink_choice)[0]
            self.student.text = f"Koffie: {nr_of_drinks} liter {self.drink}."
            yield self.env.timeout(2)
            self.student.text = f"Admiratie voor de machine..."
            yield self.env.timeout(nr_of_drinks * 2)
            self.student.text = f"Koffie binnen!"

        self.student.leave_coffee_machine_queue(coffee_machine)
        self.move_to_next_state()

    def move_to_next_state(self):
        from hallway_state import HallwayState
        new_state = HallwayState(self.env, self.student)
        new_state.sprite = 4
        self.switch_state(new_state)

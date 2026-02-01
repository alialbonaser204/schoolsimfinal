import os
import csv
import random
import numpy as np
from simulation import Simulation
from box import Box
import yaml

# Laad de config.yaml
def get_conf():
    with open("config.yaml", "r") as f:
        return yaml.unsafe_load(f)

# Eén simulatie uitvoeren
def run_simulation(config: Box, sim_id: int, num_students: int, num_coffee_machines: int, seed=None):
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    config.student.amount = num_students
    config.coffee_machine.amount = num_coffee_machines

    positions_dict = config.coffee_machine.get("position", {})
    for i in range(config.coffee_machine.amount):
        if str(i) not in positions_dict:
            positions_dict[str(i)] = [680 + i * 60, 90]
    config.coffee_machine.position = positions_dict

    sim = Simulation(Box(config), headless=True)
    sim.max_end_time = 440

    while sim.simulation_time < sim.max_end_time:
        sim.run_for(1.0)

    return sim.collect_results(sim_id)

# Batch runs uitvoeren en CSV maken
def batch_run():
    config = Box(get_conf())
    results = []
    sim_id = 0

    for students in [30, 60]:
        for machines in [1, 2, 3, 4, 5]:
            for i in range(100):  # Aantal herhalingen per scenario
                seed = sim_id * 100 + i  # Unieke seed per combinatie
                print(f"▶ Running simulation {sim_id}... Students={students}, Machines={machines}, Seed={seed}")
                result = run_simulation(Box(config), sim_id, students, machines, seed)
                results.append(result)
                sim_id += 1

    csv_file = os.path.join(os.getcwd(), "batch_results.csv")
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"\n Results saved in: {csv_file}")

# Startpunt van script
if __name__ == "__main__":
    batch_run()

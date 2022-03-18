from experiment_find_optimal_friction_factor import create_and_run_epanet_simulation, get_difference
from PipeConverter import PipeConverter
from ModificationStrategy import Strategy
from tqdm import tqdm
import numpy as np
import os
import seaborn as sns
import matplotlib.pyplot as plt


def run_up_simulation(heights, pipe_length, diameter, pressure, roughness):
    template_filepath = "up_template.inp"

    epanet_fill_times, simulation_fill_times = [], []
    for height in tqdm(heights, total=len(heights)):
        # run epanet simulation
        # Note: for a flat pipe, the friction factor doesn't affect the pipe equivalent length since it is always 0.44
        epanet_fill_times.append(
            create_and_run_epanet_simulation(pipe_length, diameter, pressure, roughness, height, template_filepath,
                                             strategy=Strategy.SINGLE_TANK_CV_CONSTANT_PRESSURE,
                                             tank_height_multiplier=tank_height_multiplier))

        # run numerical integration
        converter = PipeConverter()
        converter.update_pressure(pressure)
        simulation_fill_times.append(converter.fill_time(pipe_length, height, diameter, update_pressure=False))

    return epanet_fill_times, simulation_fill_times


def run_down_simulation(heights, pipe_length, diameter, pressure, roughness):
    template_filepath = "down_template.inp"

    epanet_fill_times, simulation_fill_times = [], []
    for height in tqdm(heights, total=len(heights)):
        # run epanet simulation
        # Note: for a flat pipe, the friction factor doesn't affect the pipe equivalent length since it is always 0.44
        epanet_fill_times.append(
            create_and_run_epanet_simulation(pipe_length, diameter, pressure, roughness, height, template_filepath,
                                             strategy=Strategy.SINGLE_TANK_CV_CONSTANT_PRESSURE,
                                             tank_height_multiplier=0.05))

        # run numerical integration
        converter = PipeConverter()
        converter.update_pressure(pressure)
        simulation_fill_times.append(converter.fill_time(pipe_length, -height, diameter, update_pressure=False))

    return epanet_fill_times, simulation_fill_times


if __name__ == "__main__":
    heights = np.linspace(0, 10, 40)
    pipe_length = 1000
    diameter = 0.3
    pressure = 20
    roughness = 100
    tank_height_multiplier = 0.6897
    epanet_fill_times_up, simulation_fill_times_up = run_up_simulation(heights, pipe_length, diameter, pressure,
                                                                       roughness)

    palette = sns.color_palette('coolwarm')
    sns.set_theme(palette=palette)
    yerr = 3
    epanet_fill_times_up = np.array(epanet_fill_times_up)
    # plt.errorbar(heights, epanet_fill_times_up, yerr=yerr, label="EPANET", color="black", fmt="o", alpha=0.75, capsize=2)
    # plt.scatter(heights,
    #             simulation_fill_times_up,
    #             alpha=0.5,
    #             c=np.where(np.abs(epanet_fill_times_up - simulation_fill_times_up) <= yerr, 'g', 'r'))  # in or out of range
    # plt.legend(["Simulation", "EPANET"])
    # plt.title(f'Filling time [s] vs Elevation [m] for 1km Pipe')
    # plt.xlabel('Pipe elevation [m]')
    # plt.ylabel('Time to fill [s]')
    # plt.show()

    # downward sloping pipe
    epanet_fill_times_down, simulation_fill_times_down = run_down_simulation(heights, pipe_length, diameter, pressure,
                                                                             roughness)
    epanet_fill_times_down, simulation_fill_times_down, heights_down = epanet_fill_times_down, simulation_fill_times_down, heights * -1

    epanet_fill_times_down = np.array(epanet_fill_times_down)
    # plt.errorbar(heights_down, epanet_fill_times_down, yerr=yerr, label="EPANET", color="black", fmt="o", alpha=0.75, capsize=2)
    # plt.scatter(heights_down,
    #             simulation_fill_times_down,
    #             alpha=0.5,
    #             c=np.where(np.abs(epanet_fill_times_down - simulation_fill_times_down) <= yerr, 'g', 'r'))  # in or out of range
    # plt.legend(["Simulation", "EPANET"])
    # plt.title(f'Filling time [s] vs Elevation [m] for 1km Pipe')
    # plt.xlabel('Pipe elevation [m]')
    # plt.ylabel('Time to fill [s]')
    # plt.show()

    heights = list(heights_down) + list(heights)
    epanet_fill_times = np.array(list(epanet_fill_times_down) + list(epanet_fill_times_up))
    simulation_fill_times = np.array(list(simulation_fill_times_down) + list(simulation_fill_times_up))

    plt.errorbar(heights, epanet_fill_times, yerr=yerr, label="EPANET", color="black", fmt="o", alpha=0.75, capsize=2)
    plt.scatter(heights,
                simulation_fill_times,
                alpha=0.5,
                c=np.where(np.abs(epanet_fill_times - simulation_fill_times) <= yerr, 'g', 'r'))  # in or out of range
    plt.legend(["Simulation", "EPANET"])
    plt.title(f'Filling time [s] vs Elevation [m] for 1km Pipe')
    plt.xlabel('Pipe elevation [m]')
    plt.ylabel('Time to fill [s]')
    plt.show()

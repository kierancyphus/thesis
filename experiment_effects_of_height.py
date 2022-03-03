from experiment_find_optimal_friction_factor import create_and_run_epanet_simulation, get_difference
from PipeConverter import PipeConverter
from tqdm import tqdm
import numpy as np
import os
import seaborn as sns
import matplotlib.pyplot as plt


def run_ff_simulations_up(heights, pipe_length, diameter, pressure, roughness):
    template_filepath = "up_template.inp"

    epanet_fill_times, simulation_fill_times = [], []
    for height in tqdm(heights, total=len(heights)):
        # run epanet simulation
        # Note: for a flat pipe, the friction factor doesn't affect the pipe equivalent length since it is always 0.44
        epanet_fill_times.append(create_and_run_epanet_simulation(pipe_length, diameter, pressure, roughness, height, template_filepath))

        # run numerical integration for different ff
        converter = PipeConverter()
        converter.update_pressure(pressure)
        simulation_fill_times.append(converter.fill_time(pipe_length, height, diameter, update_pressure=False))

    return epanet_fill_times, simulation_fill_times


if __name__ == "__main__":
    heights = np.linspace(0, 10, 20)
    pipe_length = 1000
    diameter = 0.3
    pressure = 20
    roughness = 100
    epanet_fill_times, simulation_fill_times = run_ff_simulations_up(heights, pipe_length, diameter, pressure, roughness)
    # sns.scatterplot(heights, epanet_fill_times, label="Epanet")
    # sns.scatterplot(heights, simulation_fill_times, label="Simulation")
    # plt.show()

    palette = sns.color_palette('coolwarm')
    sns.set_theme(palette=palette)
    yerr = 3
    epanet_fill_times = np.array(epanet_fill_times)
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
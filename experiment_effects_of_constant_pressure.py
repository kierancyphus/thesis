import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from experiment_effects_of_height import run_up_down_simulation

if __name__ == "__main__":
    heights_original = np.linspace(0, 10, 30)
    pipe_length = 1000
    diameter = 0.3
    pressure = 20
    roughness = 100
    tank_height_multiplier = 0.6897

    heights, epanet_fill_times, simulation_fill_times = run_up_down_simulation(heights_original, pipe_length, diameter, pressure,
                                                                               roughness, thm=tank_height_multiplier,
                                                                               constant_pressure=True)

    palette = sns.color_palette('coolwarm')
    sns.set_theme(palette=palette)

    plt.scatter(heights, simulation_fill_times)

    heights, epanet_fill_times, simulation_fill_times = run_up_down_simulation(heights_original, pipe_length, diameter, pressure,
                                                                               roughness, thm=tank_height_multiplier,
                                                                               constant_pressure=False)

    plt.scatter(heights, simulation_fill_times)

    plt.legend(['Constant Pressure', 'Height based pressure'])
    plt.title(f'Filling time [s] vs Elevation [m] for 1km Pipe')
    plt.xlabel('Pipe elevation [m]')
    plt.ylabel('Time to fill [s]')
    plt.show()
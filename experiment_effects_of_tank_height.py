from experiment_find_optimal_friction_factor import create_and_run_epanet_simulation, get_difference
from PipeConverter import PipeConverter
from ModificationStrategy import Strategy
from tqdm import tqdm
import numpy as np
import os
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib

"""
Effects of Tank Height
_______________________

Seeing how different tank heights affect filling time in our EPANET simulations. Ideally, we would be able to use
this as a way to model the growing resistance in a pipe as it fills, since tanks fill from the bottom, the more
water that is pumped in it, the more it resists being filled and so should slow down the filling. The issue with this
is that tank heights are currently set as a multiple of the height difference, which shouldn't be correlated with the
internal pipe friction. Ideally, however, our calibration with the average friction factor should have negated, these,
and thus, the only relationship left should be with gravity.

Alternatively, variable tank height could be used to compensate for the gravitational effects of slanted pipes. For
example, a pipe sloped upwards receives more gravitational resistance the fuller the pipe is because the effective
mass increases, and thus the resistive force. For a downwards sloping pipe, this should be the opposite as the
water will accelerate the more there is in the pipe (however, since we can't remove resistance with a tank this
is tricky).

"""


# set seaborn theme
cmap = sns.color_palette("coolwarm", as_cmap=True)
sns.set_theme()


def plot_all_htm(pipe_heights, epanet_fill_times_by_htm, thms, simulation_fill_times, param, filename):
    # need to find max and min ff for scaling colours
    norm = matplotlib.colors.Normalize(vmin=np.min(thms), vmax=np.max(thms))

    for ff in thms:
        simulation_fill_time = epanet_fill_times_by_htm[ff]
        plt.scatter(pipe_heights, simulation_fill_time, alpha=0.5, c=[ff for _ in pipe_heights], norm=norm, cmap=cmap)

    plt.errorbar(pipe_heights, simulation_fill_times, yerr=1.5, label="Numerical Simulation", color="black", fmt="o",
                 alpha=0.75)
    plt.title(f'Filling time [s] vs {param} for various tank height multipliers')
    plt.xlabel(param)
    plt.ylabel('Time to fill [s]')
    cb = plt.colorbar()
    cb.set_label("Tank Height Multipliers")
    plt.legend()
    fig = plt.gcf()
    fig.set_size_inches(12, 10)
    filepath = os.path.join(os.getcwd(), 'results', f'all_thms_{filename}.jpg')
    plt.savefig(filepath, dpi=100)
    plt.show()


def plot_one_thm(pipe_heights, epanet_fill_times, simulation_fill_time, best_thm, param, filename):
    plt.errorbar(pipe_heights, epanet_fill_times, yerr=1.5, label="EPANET", color="black", fmt="o", alpha=0.75,
                 capsize=2)
    plt.scatter(pipe_heights,
                simulation_fill_time,
                alpha=0.5,
                c=np.where(np.abs(epanet_fill_times - simulation_fill_time) <= 1.5, 'g', 'r'))  # in or out of range
    plt.legend(["Simulation", "EPANET"])
    plt.title(f'Filling time [s] vs {param} for best tank height multiplier = {best_thm:.4f}')
    plt.xlabel(param)
    plt.ylabel('Time to fill [s]')
    fig = plt.gcf()
    fig.set_size_inches(12, 10)
    filepath = os.path.join(os.getcwd(), 'results', f'one_htm_{filename}.jpg')
    plt.savefig(filepath, dpi=100)
    plt.show()


def run_ff_simulations_up(heights, pipe_length, diameter, pressure, roughness, thm):
    template_filepath = "up_template.inp"

    epanet_fill_times, simulation_fill_times = [], []
    for height in tqdm(heights, total=len(heights)):
        # run epanet simulation
        # Note: for a flat pipe, the friction factor doesn't affect the pipe equivalent length since it is always 0.44
        epanet_fill_times.append(create_and_run_epanet_simulation(pipe_length, diameter, pressure, roughness, height,
                                                                  template_filepath,
                                                                  strategy=Strategy.SINGLE_TANK_CV_CONSTANT_PRESSURE,
                                                                  tank_height_multiplier=thm))

        # run numerical integration for different ff
        converter = PipeConverter()
        converter.update_pressure(pressure)
        simulation_fill_times.append(converter.fill_time(pipe_length, height, diameter, update_pressure=False))

    return epanet_fill_times, simulation_fill_times


def run_tank_height_multiplier_simulations_height(pipe_heights, tank_height_multipliers, pressure, diameter, loss,
                                                  roughness, length):
    template_filepath = "up_template.inp"
    epanet_fill_times_by_thm = {thm: [] for thm in tank_height_multipliers}
    simulation_fill_times = []
    for height in tqdm(pipe_heights, total=len(pipe_heights)):
        # get numerical simulation fill time

        converter = PipeConverter()
        converter.update_pressure(pressure)
        fill_time = converter.fill_time(length, height, diameter, update_pressure=False)
        simulation_fill_times.append(fill_time)

        for thm in tank_height_multipliers:
            epanet_fill_times_by_thm[thm].append(
                create_and_run_epanet_simulation(length, diameter, pressure, roughness, height, template_filepath,
                                                 strategy=Strategy.SINGLE_TANK_CV_CONSTANT_PRESSURE,
                                                 tank_height_multiplier=thm))

    # find the best thm value and plot compared to simulation (lowest loss)
    simulation_fill_times = np.array(simulation_fill_times)
    differences = []
    for ff, result in epanet_fill_times_by_thm.items():
        differences.append((get_difference(simulation_fill_times, np.array(result), loss=loss), ff))

    _, best_thm_index = sorted(differences, key=lambda tup: tup[0])[0]

    return simulation_fill_times, epanet_fill_times_by_thm, best_thm_index


if __name__ == "__main__":
    heights = np.linspace(0, 10, 20)
    tank_height_multipliers = np.linspace(0.1, 1.2, 30)
    pipe_length = 1000
    diameter = 0.3
    pressure = 20
    roughness = 100

    simulation_fill_times, epanet_fill_times_by_thm, best_thm_index = run_tank_height_multiplier_simulations_height(
        pipe_heights=heights,
        tank_height_multipliers=tank_height_multipliers,
        pressure=pressure,
        diameter=diameter,
        loss="mse",
        roughness=100,
        length=pipe_length
    )

    plot_all_htm(heights, epanet_fill_times_by_thm, tank_height_multipliers, simulation_fill_times,
                 "Pipe change in elevation [m]", "height")

    plot_one_thm(heights, epanet_fill_times_by_thm[best_thm_index], simulation_fill_times, best_thm_index,
                 "Pipe change in elevation [m]", "height")

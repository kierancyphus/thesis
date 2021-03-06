import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from tqdm import tqdm

from experiment_utils import create_and_run_epanet_simulation
from PipeConverter import PipeConverter

# set seaborn theme
cmap = sns.color_palette("coolwarm", as_cmap=True)
sns.set_theme()


def plot_all(variable_parameter, epanet_fill_times, friction_factors, simulation_fill_times_by_ff, best_ff,
             param="Pipe Length [m]", filename="pipes"):
    # Loss vs friction factor
    plot_all_ff(variable_parameter, epanet_fill_times, friction_factors, simulation_fill_times_by_ff, param, filename)

    # EPANET vs simulation filling time for best ff value
    plot_one_ff(variable_parameter, epanet_fill_times, simulation_fill_times_by_ff[best_ff], best_ff, param, filename)

    # plot differential compared to error bars
    plot_percent_error(variable_parameter, epanet_fill_times, simulation_fill_times_by_ff[best_ff], best_ff, param,
                       filename)


def plot_all_ff(pipe_lengths, epanet_fill_times, friction_factors, simulation_fill_times_by_ff, param, filename):
    # need to find max and min ff for scaling colours
    norm = matplotlib.colors.Normalize(vmin=np.min(friction_factors), vmax=np.max(friction_factors))

    for ff in friction_factors:
        simulation_fill_time = simulation_fill_times_by_ff[ff]
        plt.scatter(pipe_lengths, simulation_fill_time, alpha=0.5, c=[ff for _ in pipe_lengths], norm=norm, cmap=cmap)

    plt.errorbar(pipe_lengths, epanet_fill_times, yerr=1.5, label="EPANET", color="black", fmt="o", alpha=0.75)
    plt.title(f'Filling time [s] vs {param} for various friction factors')
    plt.xlabel(param)
    plt.ylabel('Time to fill [s]')
    cb = plt.colorbar()
    cb.set_label("Friction Factors")
    plt.legend()
    fig = plt.gcf()
    fig.set_size_inches(12, 10)
    filepath = os.path.join(os.getcwd(), 'results', f'all_ff_{filename}.jpg')
    plt.savefig(filepath, dpi=100)
    plt.show()


def plot_one_ff(pipe_lengths, epanet_fill_times, simulation_fill_time, best_ff, param, filename):
    plt.errorbar(pipe_lengths, epanet_fill_times, yerr=1.5, label="EPANET", color="black", fmt="o", alpha=0.75,
                 capsize=2)
    plt.scatter(pipe_lengths,
                simulation_fill_time,
                alpha=0.5,
                c=np.where(np.abs(epanet_fill_times - simulation_fill_time) <= 1.5, 'g', 'r'))  # in or out of range
    plt.legend(["Simulation", "EPANET"])
    plt.title(f'Filling time [s] vs {param} for best friction factor = {best_ff:.4f}')
    plt.xlabel(param)
    plt.ylabel('Time to fill [s]')
    fig = plt.gcf()
    fig.set_size_inches(12, 10)
    filepath = os.path.join(os.getcwd(), 'results', f'one_ff_{filename}.jpg')
    plt.savefig(filepath, dpi=100)
    plt.show()


def plot_percent_error(pipe_lengths, epanet_fill_times, simulation_fill_time, best_ff, param, filename):
    plt.scatter(pipe_lengths,
                (epanet_fill_times - simulation_fill_time) / epanet_fill_times * 100,
                label=f"Deviation from EPANET for {best_ff:.4f}",
                alpha=0.5)
    plt.title(f'Percent difference from EPANET time vs {param} for best friction factor = {best_ff:.4f}')
    plt.xlabel(param)
    plt.ylabel('Percent difference from EPANET time')
    fig = plt.gcf()
    fig.set_size_inches(12, 10)
    filepath = os.path.join(os.getcwd(), 'results', f'percent_error_{filename}.jpg')
    plt.savefig(filepath, dpi=100)
    plt.show()


def get_difference(a: np.ndarray, b: np.ndarray, loss: str = "mse"):
    if loss == "hinge":
        return np.sum(np.abs(a - b))
    return np.sum((a - b) ** 2)



def run_ff_simulations_diameter(pipe_length, friction_factors, pressure, diameters, loss, roughness):
    simulation_fill_times_by_ff = {ff: [] for ff in friction_factors}
    epanet_fill_times = []
    for diameter in tqdm(diameters, total=len(diameters)):
        # run epanet simulation
        # Note: for a flat pipe, the friction factor doesn't affect the pipe equivalent length since it is always 0.44
        epanet_fill_times.append(create_and_run_epanet_simulation(pipe_length, diameter, pressure, roughness))

        # run numerical integration for different ff
        for ff in friction_factors:
            converter = PipeConverter(f=ff)
            converter.update_pressure(pressure)
            fill_time = converter.fill_time(pipe_length, 0, diameter, update_f=False)
            simulation_fill_times_by_ff[ff].append(fill_time)

    # find the best ff value and plot compared to epanet (lowest loss)
    epanet_fill_times = np.array(epanet_fill_times)
    differences = []
    for ff, result in simulation_fill_times_by_ff.items():
        differences.append((get_difference(epanet_fill_times, np.array(result), loss=loss), ff))

    _, best_ff_index = sorted(differences, key=lambda tup: tup[0])[0]

    return epanet_fill_times, simulation_fill_times_by_ff, best_ff_index


def run_ff_simulations_length(pipe_lengths, friction_factors, pressure, diameter, loss, roughness):
    simulation_fill_times_by_ff = {ff: [] for ff in friction_factors}
    epanet_fill_times = []
    for length in tqdm(pipe_lengths, total=len(pipe_lengths)):
        # run epanet simulation
        # Note: for a flat pipe, the friction factor doesn't affect the pipe equivalent length since it is always 0.44
        epanet_fill_times.append(create_and_run_epanet_simulation(length, diameter, pressure, roughness))

        # run numerical integration for different ff
        for ff in friction_factors:
            converter = PipeConverter(f=ff)
            converter.update_pressure(pressure)
            fill_time = converter.fill_time(length, 0, diameter, update_f=False)
            simulation_fill_times_by_ff[ff].append(fill_time)

    # find the best ff value and plot compared to epanet (lowest loss)
    epanet_fill_times = np.array(epanet_fill_times)
    differences = []
    for ff, result in simulation_fill_times_by_ff.items():
        differences.append((get_difference(epanet_fill_times, np.array(result), loss=loss), ff))

    _, best_ff_index = sorted(differences, key=lambda tup: tup[0])[0]

    return epanet_fill_times, simulation_fill_times_by_ff, best_ff_index


def run_ff_simulations_pressure(pipe_length, friction_factors, pressures, diameter, loss, roughness):
    simulation_fill_times_by_ff = {ff: [] for ff in friction_factors}
    epanet_fill_times = []
    for pressure in tqdm(pressures, total=len(pressures)):
        # run epanet simulation
        # Note: for a flat pipe, the friction factor doesn't affect the pipe equivalent length since it is always 0.44
        epanet_fill_times.append(create_and_run_epanet_simulation(pipe_length, diameter, pressure, roughness))

        # run numerical integration for different ff
        for ff in friction_factors:
            converter = PipeConverter(f=ff)
            converter.update_pressure(pressure)
            fill_time = converter.fill_time(pipe_length, 0, diameter, update_f=False)
            simulation_fill_times_by_ff[ff].append(fill_time)

    # find the best ff value and plot compared to epanet (lowest loss)
    epanet_fill_times = np.array(epanet_fill_times)
    differences = []
    for ff, result in simulation_fill_times_by_ff.items():
        differences.append((get_difference(epanet_fill_times, np.array(result), loss=loss), ff))

    _, best_ff_index = sorted(differences, key=lambda tup: tup[0])[0]

    return epanet_fill_times, simulation_fill_times_by_ff, best_ff_index


def process_bucket(lower_bound, upper_bound, num_length_samples, friction_factors, pressure, diameter, loss, roughness):
    pipe_lengths = list(np.linspace(lower_bound, upper_bound, num_length_samples))
    epanet_fill_times, simulation_fill_times_by_ff, best_ff = run_ff_simulations_length(pipe_lengths, friction_factors,
                                                                                        pressure, diameter, loss,
                                                                                        roughness)
    simulation_fill_times = simulation_fill_times_by_ff[best_ff]
    best_mse = get_difference(epanet_fill_times, simulation_fill_times)
    percent_points_within_bounds = np.sum(
        np.where(np.abs(epanet_fill_times - simulation_fill_times) <= 1.5, 1, 0)) / num_length_samples * 100
    percent_deviations = (epanet_fill_times - simulation_fill_times) / epanet_fill_times * 100
    result_string = "\t".join([f"[{lower_bound}, {upper_bound}]", f"{best_ff:.4f}", f"{best_mse:.4f}",
                               f"{percent_points_within_bounds}",
                               f"[{np.min(percent_deviations):.2f}, {np.max(percent_deviations):.2f}]"])
    return result_string


def get_ideal_ff_per_bucket():
    num_length_samples = 10
    num_friction_factor_samples = 100
    pressure = 20
    diameter = 0.3
    roughness = 100
    loss = "mse"

    friction_factors = np.linspace(0.02, 0.05, num_friction_factor_samples)

    results = []
    results.append("\t".join(["Range", "Friction Factor", "MSE", "% in Bounds", "% Deviation Range"]))
    # [100, 8000]
    for i in range(1, 80):
        lower_bound, upper_bound = i * 100 + 1, i * 100 + 101
        result_string = process_bucket(lower_bound, upper_bound, num_length_samples, friction_factors, pressure,
                                       diameter, loss, roughness)
        results.append(result_string)

    # # [1000, 5000] upper and lower bounds empirically chosen
    # friction_factors = np.linspace(0.027, 0.031, num_friction_factor_samples)
    # for i in range(20):
    #     lower_bound, upper_bound = i * 200 + 1000, i * 200 + 1200
    #     result_string = process_bucket(lower_bound, upper_bound, num_length_samples, friction_factors, pressure,
    #                                    diameter, loss)
    #     results.append(result_string)
    #
    # # [5000, 8000] upper and lower bounds empirically chosen
    # friction_factors = np.linspace(0.03, 0.035, num_friction_factor_samples)
    # for i in range(6):
    #     lower_bound, upper_bound = i * 500 + 5000, i * 500 + 5500
    #     result_string = process_bucket(lower_bound, upper_bound, num_length_samples, friction_factors, pressure,
    #                                    diameter, loss)
    #     results.append(result_string)

    for result in results:
        print(result)


def run_experiments():
    """
    Since the fill times vs length are roughly linear in the bucket, adding more points doesn't improve the accuracy
    of the regression

    5 -> 0.0280
    10 -> 0.0280
    20 -> 0.0280
    50 -> 0.0280

    So I should just use 10  points to speed up the calculations

    pressure 100: 0.0243
    pressure 500: 0.0215

    Friction factor changes over pressure
    :return:
    """
    pipe_lengths = list(np.linspace(1000, 1010, 20))
    friction_factors = np.linspace(0.02, 0.03, 100)

    # default params are pressure head of 20 and 300mm diameter
    pressure = 20
    diameter = 0.3
    roughness = 100
    loss = "mse"

    # lengths
    epanet_fill_times, simulation_fill_times_by_ff, best_ff = run_ff_simulations_length(pipe_lengths, friction_factors,
                                                                                        pressure, diameter, loss,
                                                                                        roughness)
    plot_all(pipe_lengths, epanet_fill_times, friction_factors, simulation_fill_times_by_ff, best_ff, "Pipe Length [m]",
             "length")

    # diameter
    length = 1000
    diameters = list(np.linspace(0.1, 3, 20))
    epanet_fill_times, simulation_fill_times_by_ff, best_ff = run_ff_simulations_diameter(length, friction_factors,
                                                                                          pressure, diameters, loss,
                                                                                          roughness)
    plot_all(diameters, epanet_fill_times, friction_factors, simulation_fill_times_by_ff, best_ff, "Pipe Diameter [m]",
             "diameter")

    # pressure
    pressures = np.linspace(5, 100, 20)
    epanet_fill_times, simulation_fill_times_by_ff, best_ff = run_ff_simulations_diameter(length, friction_factors,
                                                                                          pressure, diameters, loss,
                                                                                          roughness)
    plot_all(pressures, epanet_fill_times, friction_factors, simulation_fill_times_by_ff, best_ff, "Pressure Head [m]",
             "pressure")


if __name__ == "__main__":
    run_experiments()
    # get_ideal_ff_per_bucket()
    """
    Discussion:
    Using MSE chooses an ff value that fits better for later values since they are likely to deviate more and
    dominate the sum. Hinge loss might be better.
    ff in np.linspace(0.01, 0.1, 30)
    
    MSE
    range:      diameter    ff      in_range    % range from EPANET
    100-200:    0.3         0.026   All         [-0.4, 2.0]
    100-400:    0.3         0.0255  All         [-9, 1]
    100-500:    0.3         0.029   -1
    100-1000:   0.3         0.029   +1
    400-500:    0.3         0.026   -4          [0.4, 2]
    100-7000:   0.3         0.0317  +1          [-22, 0]
    
    # Looks like the friction factors are proportional to the size of the diameter?
    100-400:    1           0.0845  All         [-9, 1]
    100-400:    0.1         0.0089  All         [-11, -1]
    
    TODO: I read the wikipedia article and it said that the friction factor changes as a function of the diameter
    but it looks like it also changes as a function of length. Here is what I need to do next.
    - Experiment for different pipe length ranges of 100m, up to 10km
        - I'm expecting that for long pipes the effects start to drop off and so we can bin those buckets together
    - Experiment for different pipe diameters, from 0.1m to 5m
        - Expecting the same sort of behaviour as above
    - Experiment for different pipe roughnesses (in EPANET) and see how that translates in ff
        - Also should read up on what they actually do internally
    
    Ideally, I can create a 3D lookup table that allows me to choose a friction factor such that the EPANET and modelled
    scenarios align to within +-1.5% (or some other small number). For short pipes, getting them to align within the
    uncertainty would also be great.
    
    """
